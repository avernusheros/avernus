#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    csvimporter.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
#
#    This file is part of wxBanker.
#
#    wxBanker is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    wxBanker is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with wxBanker.  If not, see <http://www.gnu.org/licenses/>.

from datetime import datetime
import codecs, csv, re
from cStringIO import StringIO

class CsvImporter:
    """
    Parses a csv file and extracts the data for import into the wxBanker data structures.
    """
    
    def getTransactionsFromFile(self, filename, settings):
        contents = open(filename, 'rb').read()
        return self.getTransactionsFromCSV(contents, settings)

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
    fileName = '../data/csv/psd.csv'
    importer = CsvImporter()
    trans = importer.getTransactionsFromFile(fileName,
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
                                            })
    for t in trans:
        print t
