#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import codecs, csv, re
from cStringIO import StringIO
import tempfile
import chardet

{
    'linesToSkip':13, 
    'encoding':'iso-8859-15',
    'delimiter':';',
    'amountColumn':8,
    'decimalSeparator':',',
    'descriptionColumn':6,
    'dateColumn':1,
    'dateFormat':'%d.%m.%Y',
    'saldoIndicator':9,
    'negativeSaldo':'S',
    'receiver':3,
    'sender':2,
    }


class CsvImporter:
    
    def getTransactionsFromFile(self, filename, settings):
        contents = open(filename, 'rb').read()
        return self.getTransactionsFromCSV(contents, settings)

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

    def get_rows_from_csv(self, filename, profile):
        csvdata = StringIO(open(filename, 'rb').read())
        result = []
        first_line_skipped = False
        for row in UnicodeReader(csvdata, profile['dialect'], profile['encoding']):            
            if len(row) == profile['row length']:
                if not first_line_skipped and profile['header']:
                    first_line_skipped = True
                    continue
                result.append(row)
            #If we find a blank line, assume we've hit the end of the transactions.
            if not row and not len(result)==0:
                break
        return result

    def getTransactionsFromCSV(self, csvdata, settings):
        csvdata = StringIO(csvdata)
        csvReader = csv.reader(
            UTF8Recoder(csvdata, settings['encoding']),
            delimiter=settings['delimiter'])

        transactions = []
        linesSkipped = 0
        for row in csvReader:
            # Unfortunately csvReader is not subscriptable so we must count ourselves.
            if settings['linesToSkip']>linesSkipped:
                linesSkipped+=1
                continue

            # If we find a blank line, assume we've hit the end of the transactions.
            if not row:
                break
            # convert to python unicode strings
            row = [unicode(s, "utf-8") for s in row]
            amount = self.parseAmount(row[settings['amountColumn']], settings['decimalSeparator'])
            if 'saldoIndicator' in settings:
                indicator = row[settings['saldoIndicator']]
                if indicator == settings['negativeSaldo']:
                    amount *= -1
            sender = receiver = None
            if 'sender' in settings:
                sender = row[settings['sender']]
            if 'receiver' in settings:
                receiver = row[settings['receiver']]
            desc = self.parseDesc(row[settings['descriptionColumn']])
            tdate = datetime.strptime(row[settings['dateColumn']],
                settings['dateFormat']).strftime('%Y-%m-%d')
            erg = [tdate, desc, amount]
            if sender is not None:
                erg.append(sender)
            if receiver is not None:
                erg.append(receiver)
            transactions.append(erg)
            
        return transactions
    
    def parseDesc(self, desc):
        return re.sub('[\s]+',' ',desc)
       
    def parseAmount(self, val, decimalSeparator):
        amountStr = ""
        for char in val:
            if char in "-1234567890"+decimalSeparator:
                amountStr += char

        amountStr = amountStr.replace(decimalSeparator, '.')
        return float(amountStr)


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
    filename = '../data/csv/psd.csv'
    importer = CsvImporter()
    profile = importer._sniff_csv(filename)
    print profile
    trans = importer.get_rows_from_csv(filename, profile)
    count = 1
    for t in trans:
        print count 
        count += 1
        print t
