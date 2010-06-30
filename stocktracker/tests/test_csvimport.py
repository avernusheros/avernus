#!/usr/bin/env python

if __name__ == '__main__':
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

import unittest, datetime
from stocktracker.csvimporter import CsvImporter

class CsvImporterTest(unittest.TestCase):
    def setUp(self):
        self.importer = CsvImporter()
        
    def test_comdirect(self):
        filename = 'data/csv/comdirect.csv'
        profile = {'encoding':'iso-8859-15', 'row length':5 }
        
        new_profile = self.importer._sniff_csv(filename)
        self.assertEqual(profile['encoding'], new_profile['encoding'])
        self.assertEqual(profile['row length'], new_profile['row length'])

        transactions = self.importer.get_rows_from_csv(filename, new_profile)
        self.assertEqual(len(transactions), 5)
        
        tran = transactions[2]
        self.assertEqual(tran.Date, datetime.date(2010, 3, 8))
        self.assertEqual(tran.Description, "Auftraggeber: XYZ SAGT DANKE Buchungstext: XYZ SAGT DANKE EC 123456789 06.03 14.53 CE0 Ref. ABCDFER213456789/1480  (Lastschrift Einzug)")
        self.assertEqual(tran.Amount, -32.27)   
        

if __name__ == "__main__":
    unittest.main()
