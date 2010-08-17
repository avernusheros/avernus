#!/usr/bin/env python

import unittest, datetime
from stocktracker.csvimporter import CsvImporter

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
        filename = 'data/csv/comdirect.csv'
        profile = {'encoding':'ISO-8859-2', 'row length':5 }
        
        new_profile = self.importer._sniff_csv(filename)
        for key, val in profile.items():
            self.assertEqual(profile[key], new_profile[key])

        transactions = self.importer.get_rows_from_csv(filename, new_profile)
        self.assertEqual(len(transactions), 5)
        
        tran = transactions[2]
        self.assertEqual(tran.Date, datetime.date(2010, 3, 8))
        self.assertEqual(tran.Description, "Auftraggeber: XYZ SAGT DANKE Buchungstext: XYZ SAGT DANKE EC 123456789 06.03 14.53 CE0 Ref. ABCDFER213456789/1480  (Lastschrift Einzug)")
        self.assertEqual(tran.Amount, -32.27)   
        
if __name__ == "__main__":
    unittest.main()
