#!/usr/bin/env python

import unittest
import datetime
import __builtin__
__builtin__._ = str


from avernus import objects
from avernus.objects import db

dbfile = ":memory:"
db.set_db(dbfile)
db.connect()

from avernus.csvimporter import CsvImporter


class CsvImporterTest(unittest.TestCase):

    def setUp(self):
        self.importer = CsvImporter()

    def test_parse_amount(self):
        amount = self.importer._parse_amount('42.99', '.')
        self.assertEqual(amount, 42.99)
        amount = self.importer._parse_amount('42,99', ',')
        self.assertEqual(amount, 42.99)
        amount = self.importer._parse_amount('1,142.99', '.')
        self.assertEqual(amount, 1142.99)
        amount = self.importer._parse_amount('1.142,99', ',')
        self.assertEqual(amount, 1142.99)
        amount = self.importer._parse_amount('42,99', ',', 'S')
        self.assertEqual(amount, -42.99)
        amount = self.importer._parse_amount('42,99', ',', 'H')
        self.assertEqual(amount, 42.99)
        amount = self.importer._parse_amount('-42.99', '.')
        self.assertEqual(amount, -42.99)

    def test_comdirect(self):
        filename = 'tests/data/csv/comdirect.csv'
        profile = {'encoding':'ISO-8859-2',
                   'row length':5,
                   'saldo indicator': None,
                   'description column': [2,3],
                   'amount column': 4,
                   'header': True,
                   'date format': '%d.%m.%Y',
                   'date column': 1,
                   'decimal separator': ','
                   }

        new_profile = self.importer._sniff_csv(filename)
        for key, val in profile.items():
            self.assertEqual(profile[key], new_profile[key])

        self.importer.load_transactions_from_csv(filename)
        transactions = self.importer.results
        self.assertEqual(len(transactions), 5)
        self.assertEqual(transactions[2].date, datetime.date(2010, 3, 8))
        self.assertEqual(transactions[2].description, 'Lastschrift Einzug - Auftraggeber: XYZ SAGT DANKE Buchungstext: XYZ SAGT DANKE EC 123456789 06.03 14.53 CE0 Ref. ABCDFER213456789/1480 ')
        self.assertEqual(transactions[2].amount, -32.27)

    def test_psd(self):
        filename = 'tests/data/csv/psd.csv'
        profile = {'encoding':'windows-1252',
                   'row length': 10,
                   'saldo indicator': 9,
                   'description column': [2, 3, 4, 5, 6, 7],
                   'amount column': 8,
                   'header': True,
                   'date format': '%d.%m.%Y',
                   'date column': 1,
                   'decimal separator': ','
                   }
        new_profile = self.importer._sniff_csv(filename)
        for key, val in profile.items():
            self.assertEqual(profile[key], new_profile[key])

        self.importer.load_transactions_from_csv(filename)
        transactions = self.importer.results
        self.assertEqual(len(transactions), 12)
        self.assertEqual(transactions[2].date, datetime.date(2010, 9, 2))
        self.assertEqual(transactions[2].description, u'MUSTERMANN / MAXEMPTY DE - MOA. - 1811 - 50010900 - Lastschrift\r\nZG. M02 - EUR')
        self.assertEqual(transactions[2].amount, -50.00)

    def test_cortalconsors(self):
        filename = 'tests/data/csv/cortal_consors.csv'
        profile = {'encoding':'windows-1252',
                   'row length': 7,
                   'saldo indicator': None,
                   'description column': [2, 3, 4, 6],
                   'amount column': 5,
                   'header': True,
                   'date format': '%d.%m.%Y',
                   'date column': 1,
                   'decimal separator': ','
                   }
        new_profile = self.importer._sniff_csv(filename)
        for key, val in profile.items():
            self.assertEqual(profile[key], new_profile[key])

        self.importer.load_transactions_from_csv(filename)
        transactions = self.importer.results
        self.assertEqual(len(transactions), 4)
        self.assertEqual(transactions[3].date, datetime.date(2010, 2, 1))
        self.assertEqual(transactions[3].description,  u'\xdcberweisungsgutschrift - Mustermann,Max')
        self.assertEqual(transactions[3].amount, 2500.00)

    def test_dkb(self):
        filename = 'tests/data/csv/dkb.csv'
        profile = {'encoding':'windows-1252',
                   'row length': 9,
                   'saldo indicator': None,
                   'description column': [2, 3, 4, 5, 6, 8],
                   'amount column': 7,
                   'header': True,
                   'date format': '%d.%m.%Y',
                   'date column': 1,
                   'decimal separator': '.'
                   }
        new_profile = self.importer._sniff_csv(filename)
        for key, val in profile.items():
            self.assertEqual(profile[key], new_profile[key])

        self.importer.load_transactions_from_csv(filename)
        transactions = self.importer.results
        self.assertEqual(len(transactions), 20)
        self.assertEqual(transactions[3].date, datetime.date(2010, 8, 4))
        self.assertEqual(transactions[3].description,  u'UEBERWEISUNGSGUTSCHRIFT - BJOERN GOss - UNICOMP MECHANICAL KEYBOARD  - 18106230 - 67250020')
        self.assertEqual(transactions[3].amount, 88.00)
