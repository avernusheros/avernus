#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime, date
import codecs, csv, re
from cStringIO import StringIO
import tempfile
import chardet

from stocktracker.objects import controller


FORMATS = ['%Y-%m-%d',
           '%d.%m.%Y']


class CsvImporter:
    
    def __init__(self):
        self.results = []

    def _sniff_csv(self, filename):
        profile = {}
        #csv dialect
        csvdata = StringIO(open(filename, 'rb').read())
        profile['dialect'] = csv.Sniffer().sniff(csvdata.read(2048))
        csvdata.seek(0)
        
        #encoding
        profile['encoding'] = chardet.detect(csvdata.read(2048))['encoding']
        csvdata.seek(0)

        #row length
        t = [-1,-1,-1,-1]
        for row in UnicodeReader(csvdata, profile['dialect'], profile['encoding']):
            #row with only 2 or less items are obviously no transactions
            len_row = len(row)
            if len_row < 3:
                continue
            t.append(len_row)
            if t[-1] == t[-2] == t[-3] == t[-4]:
                profile['row length'] = t[-1]
                break
        csvdata.seek(0)  
             
        #detect header
        temp_file = self._create_temp_csv(csvdata, profile)
        temp_file.seek(0)
        temp_csvdata = StringIO(temp_file.read())
        temp_csvdata.seek(0)
        profile['header'] = csv.Sniffer().has_header(temp_csvdata.read(2048))
        
        #columns
        profile['saldo indicator'] = None
        csvdata.seek(0)
        first_line_skipped = False
        for row in UnicodeReader(csvdata, profile['dialect'], profile['encoding']):  
            if len(row) == profile['row length']:
                profile['description column'] = []
                if not first_line_skipped and profile['header']:
                    first_line_skipped = True
                    continue
                col_count = 0
                for col in row:
                    if re.match('[0-9]+[\.\-]*[0-9]*[\.\-][0-9]+', col ) is not None:
                        profile['date column'] = col_count
                        profile['date format'] = self._detect_date_format(col)
                    elif re.match('-?[0-9]+[\.\,]*[0-9]*[\.\,]+[0-9]*', col) is not None:
                        profile['amount column'] = col_count
                        for s in reversed(col):
                            if s == '.':
                                profile['decimal separator'] = '.'
                                break
                            elif s == ',':
                                profile['decimal separator'] = ','
                                break
                    elif re.match('[sShHdDcC]$', col) is not None:
                        profile['saldo indicator'] = col_count
                    else:
                        profile['description column'].append(col_count)
                    col_count+=1
                break
        for key, val in profile.iteritems():
            print key,": ", val
        return profile

    def _create_temp_csv(self, csvdata, profile):
        temp_file = tempfile.TemporaryFile()
        writer = csv.writer(temp_file)
        for row in UTF8Reader(csvdata, profile['dialect'], profile['encoding']):
            if len(row) == profile['row length']:
                #remove newlines, caused sniffer to crash
                row = map(lambda x: x.replace('\n', ''), row)
                writer.writerow(row)
        return temp_file

    def _detect_date_format(self, datestring):
        for format in FORMATS:
            try:
                datetime.strptime(datestring, format)
                return format
            except:
                pass

    def _parse_date(self, datestring, dateformat):
        return datetime.strptime(datestring, dateformat).date()

    def _parse_amount(self, amount_string, decimal_separator, saldo_indicator=None):
        if decimal_separator == '.':
            amount_string = amount_string.replace(',','')
        elif decimal_separator == ',':
            amount_string = amount_string.replace('.','').replace(',','.')
        amount = float(amount_string)
        if saldo_indicator in ['s','S','c','C']:
            amount = -amount
        return amount

    def get_transactions_from_csv(self, filename, profile=None):
        if profile is None:
            profile = self._sniff_csv(filename)
        csvdata = StringIO(open(filename, 'rb').read())
        result = []
        first_line_skipped = False
        for row in UnicodeReader(csvdata, profile['dialect'], profile['encoding']):            
            if len(row) == profile['row length']:
                if not first_line_skipped and profile['header']:
                    first_line_skipped = True
                    continue
                tran = [self._parse_date(row[profile['date column']], profile['date format']), 
                        ' - '.join([row[d] for d in profile['description column']]),
                        self._parse_amount(row[profile['amount column']], 
                                           profile['decimal separator'], 
                                           profile['saldo indicator'])
                        ]    
                result.append(tran)
            #If we find a blank line, assume we've hit the end of the transactions.
            if not row and not len(result)==0:
                break
        self.results = result
        return result

    def create_transactions(self, account):
        #FIXME detect duplicates
        for result in self.results:
            controller.newAccountTransaction(date=result[0], description=result[1], amount=result[2], account=account)
       

class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self

class UTF8Reader:
    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return row

    def __iter__(self):
        return self


class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    see http://docs.python.org/library/csv.html
    """
    def __init__(self, f, encoding):
        self.encoding = encoding
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode('utf-8')
    
    
if __name__ == "__main__":
    filename = '../data/csv/comdirect.csv'
    importer = CsvImporter()
    profile = importer._sniff_csv(filename)
    print profile
    trans = importer.get_transactions_from_csv(filename, profile)
    count = 1
    for t in trans:
        print count 
        count += 1
        print t
