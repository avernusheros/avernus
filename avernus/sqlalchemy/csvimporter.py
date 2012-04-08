from datetime import datetime
import codecs, csv, re
from cStringIO import StringIO
import chardet

FORMATS = ['%Y-%m-%d', '%d.%m.%Y']

class CsvImporter:

    def __init__(self):
        self.results = []

    def _sniff_csv(self, filename):
        profile = {}
        #csv dialect
        csvdata = StringIO(open(filename, 'rb').read())
        profile['dialect'] = csv.Sniffer().sniff(csvdata.read(2048), delimiters=';,')
        #profile['dialect'].quoting = csv.QUOTE_NONE
        csvdata.seek(0)
        #encoding
        profile['encoding'] = chardet.detect(csvdata.read(2048))['encoding']
        csvdata.seek(0)

        #row length
        t = [-1,-1,-1,-1]
        maxlength = 0
        # determine the maximum row length
        for row in UnicodeReader(csvdata, profile['dialect'], profile['encoding']):
            maxlength = max(maxlength, len(row))
        csvdata.seek(0)
        for row in UnicodeReader(csvdata, profile['dialect'], profile['encoding']):
            # only rows with the maximum row length are transactions
            len_row = len(row)
            if len_row != maxlength:
                continue
            t.append(len_row)
            if t[-1] == t[-2] == t[-3] == t[-4]:
                profile['row length'] = t[-1]
                break

        #detect header
        csvdata.seek(0)
        profile['header'] = self._has_header(csvdata, profile)

        #columns
        profile['saldo indicator'] = None
        profile['category'] = -1
        csvdata.seek(0)
        checked_header = False
        for row in UnicodeReader(csvdata, profile['dialect'], profile['encoding']):
            if len(row) == profile['row length']:
                profile['description column'] = []
                if not checked_header and profile['header']:
                    checked_header = True
                    if "CATEGORY" in row:
                        profile["category"] = row.index("CATEGORY")
                    continue
                col_count = 0
                for col in row:
                    #strip whitespace
                    col = col.strip(' ')
                    if re.match('^[0-9]+[\.\-]+[0-9]*[\.\-][0-9]+$', col ) is not None:
                        profile['date column'] = col_count
                        profile['date format'] = self._detect_date_format(col)
                    elif re.match('^-?[0-9]+[\.\,]+[0-9]*[\.\,]?[0-9]*$', col) is not None:
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
                    elif col_count == profile["category"]:
                        pass
                    else:
                        profile['description column'].append(col_count)
                    col_count+=1

                #check if profile contains the required info, otherwise check the next row
                required = ['description column', 'date column', 'amount column']
                complete = True
                for req in required:
                    if req not in profile:
                        complete = False
                if complete:
                    break
        return profile

    def _has_header(self, csvdata, profile):
        """
        taken from csv
        """
        # Creates a dictionary of types of data in each column. If any
        # column is of a single type (say, integers), *except* for the first
        # row, then the first row is presumed to be labels. If the type
        # can't be determined, it is assumed to be a string in which case
        # the length of the string is the determining factor: if all of the
        # rows except for the first are the same length, it's a header.
        # Finally, a 'vote' is taken at the end for each column, adding or
        # subtracting from the likelihood of the first row being a header.
        started = False
        checked = 0
        for row in UTF8Reader(csvdata, profile['dialect'], profile['encoding']):
            if len(row) == profile['row length']:
                if not started:
                    started = True
                    header = row
                    columns = len(header)
                    columnTypes = {}
                    for i in range(columns): columnTypes[i] = None
                    continue
                #remove newlines and commas, caused sniffer to crash
                row = map(lambda x: x.replace('\n', ''), row)
                row = map(lambda x: x.replace(',', ''), row)
                checked += 1

                for col in columnTypes.keys():

                    for thisType in [int, long, float, complex]:
                        try:
                            thisType(row[col])
                            break
                        except (ValueError, OverflowError):
                            pass
                    else:
                        # fallback to length of string
                        thisType = len(row[col])
                    # treat longs as ints
                    if thisType == long:
                        thisType = int

                    if thisType != columnTypes[col]:
                        if columnTypes[col] is None: # add new column type
                            columnTypes[col] = thisType
                        else:
                            # type is inconsistent, remove column from
                            # consideration
                            del columnTypes[col]

            #If we find a blank line, assume we've hit the end of the transactions.
            if checked > 20 or (not row and started):
                break

        # finally, compare results against first row and "vote"
        # on whether it's a header
        hasHeader = 0
        for col, colType in columnTypes.items():
            if type(colType) == type(0): # it's a length
                if len(header[col]) != colType:
                    hasHeader += 1
                else:
                    hasHeader -= 1
            else: # attempt typecast
                try:
                    colType(header[col])
                except (ValueError, TypeError):
                    hasHeader += 1
                else:
                    hasHeader -= 1

        return hasHeader > 0

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
        if saldo_indicator and saldo_indicator in ['s','S','c','C']:
            amount = -amount
        return amount

    def load_transactions_from_csv(self, filename, profile=None):
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
                tran = {}
                if profile['saldo indicator']:
                    tran['amount'] = self._parse_amount(row[profile['amount column']],
                                           profile['decimal separator'],
                                           row[profile['saldo indicator']])
                else:
                    tran['amount'] = self._parse_amount(row[profile['amount column']],
                                           profile['decimal separator'])

                tran['date'] = self._parse_date(row[profile['date column']].strip(' '), profile['date format'])
                tran['description'] = ' - '.join([row[d] for d in profile['description column'] if len(row[d])>0])
                if profile['category'] == -1:
                    tran['category'] = None
                else:
                    tran['category'] = row[profile['category']].strip()
                tran['b_import'] = True
                result.append(tran)
            #If we find a blank line, assume we've hit the end of the transactions.
            if not row and not len(result)==0:
                break
        self.results = result

    def check_duplicates(self, account):
        for trans in self.results:
            if account.has_transaction({'date':trans.date,'amount':trans.amount,'description':trans.description}):
                trans.b_import = False
            else:
                trans.b_import = True

    


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
