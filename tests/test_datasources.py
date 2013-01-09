#!/usr/bin/env python

from avernus import objects
from avernus.objects import db
from avernus.data_sources import onvista, yahoo
import __builtin__
import datetime
import unittest
__builtin__._ = str



dbfile = ":memory:"
db.set_db(dbfile)
db.connect()
objects.Session().commit()

#stocks which are mentioned in bug reports
ITEMS_WITH_PROBLEMS = ['AT0000859582']


class DataSourcesTest(unittest.TestCase):

    def test_yahoo_search(self):
        y = yahoo.DataSource()
        for res in y.search('google'):
            data = res[0]
            self.assertTrue(len(data['isin']) == 12)
            self.assertIsNotNone(data['exchange'])
            self.assertIsNotNone(data['name'])
            self.assertIsNotNone(data['currency'])
            self.assertTrue(data['type'] < 10)
            self.assertTrue(data['type'] >= 0)

    def test_onvista_search(self):
        o = onvista.DataSource()
        for res in o.search("DE0008474248"):
            data = res[0]
            self.assertTrue(len(data['isin']) == 12)
            self.assertIsNotNone(data['exchange'])
            self.assertIsNotNone(data['name'])
            self.assertIsNotNone(data['currency'])
            self.assertTrue(data['type'] < 10)
            self.assertTrue(data['type'] >= 0)

    def put_stocks_in_db(self):
        o = onvista.DataSource()
        for res in o.search("DE0008474248"):
            item, source, source_info = res
            self.dsm._item_found_callback(item, source, source_info)
        y = yahoo.Yahoo()
        for res in y.search('google'):
            item, source, source_info = res
            self.dsm._item_found_callback(item, source, source_info)

    def test_update_stocks(self):
        self.put_stocks_in_db()
        test_date = datetime.datetime(1900, 1, 1)
        for st in controller.getAllStock():
            st.price = 0
            st.date = test_date
        for item in self.dsm.update_stocks(controller.getAllStock()):
            pass
        for st in controller.getAllStock():
            self.assertNotEqual(st.date, test_date)
            self.assertNotEqual(st.price, 0)


    def get_historical_prices(self, st):
        #loops needed, since the dsm uses generators
        for foo in self.dsm.update_historical_prices(st):
            for bar in foo:
                pass

    def test_historicals(self):
        self.put_stocks_in_db()
        for st in controller.getAllStock():
            count = len(controller.getAllQuotationsFromStock(st))
            self.get_historical_prices(st)
            self.assertNotEqual(count, len(controller.getAllQuotationsFromStock(st)))

    def test_items_with_problems(self):
        for item in ITEMS_WITH_PROBLEMS:
            self.dsm.search(item, threaded=False)
            stock = controller.getStockForSearchstring(item)[0]

            test_date = datetime.datetime(1900, 1, 1)
            stock.price = 0
            stock.date = test_date
            self.dsm.update_stocks([stock])
            self.assertNotEqual(stock.date, test_date)
            self.assertNotEqual(stock.price, 0)

            self.assertIsNotNone(stock)
            count = len(controller.getAllQuotationsFromStock(stock))
            self.get_historical_prices(stock)
            self.assertNotEqual(count, len(controller.getAllQuotationsFromStock(stock)))
