#!/usr/bin/env python

import __builtin__
__builtin__._ = str


from avernus import objects
from avernus.objects import db

dbfile = ":memory:"
db.set_db(dbfile)
db.connect()

from avernus.data_sources import yahoo
from avernus.controller import datasource_controller as dsm
import datetime
import unittest



#stocks which are mentioned in bug reports
ITEMS_WITH_PROBLEMS = ['AT0000859582', 'DE0005229504']


class DataSourcesTest(unittest.TestCase):

    def setUp(self):
        db.set_db(dbfile)
        db.connect()
        objects.session.commit()

    def test_yahoo_search(self):
        y = yahoo.DataSource()
        for res in y.search('google'):
            data = res[0]
            self.assertTrue(len(data['isin']) == 12)
            self.assertIsNotNone(data['exchange'])
            self.assertIsNotNone(data['name'])
            self.assertIsNotNone(data['currency'])
            self.assertEqual(data['type'], 'stock')


    def put_stocks_in_db(self):
        y = yahoo.DataSource()
        for res in y.search('google'):
            item, source, source_info = res
            dsm._item_found_callback(item, source, source_info)


    def test_update_stocks(self):
        test_date = datetime.datetime(1900, 1, 1)
        for asset in objects.asset.get_all_assets():
            asset.price = 0
            asset.date = test_date
        for item in dsm.update_assets(objects.asset.get_all_assets()):
            print item
        for asset in objects.asset.get_all_assets():
            self.assertNotEqual(asset.date, test_date)
            self.assertNotEqual(asset.price, 0)

    def get_historical_prices(self, st):
        #loops needed, since the dsm uses generators
        for foo in dsm.update_historical_prices_asset(st, threaded=False):
            for bar in foo:
                pass

    def test_historicals_yahoo(self):
        self.put_stocks_in_db()
        asset_count = 0
        for asset in objects.asset.get_all_assets():
            if "yahoo" in asset.source:
                asset_count +=1
                count = len(asset.quotations)
                self.get_historical_prices(asset)
                self.assertNotEqual(count, len(asset.quotations))
        self.assertNotEqual(0, asset_count)

    def test_items_with_problems(self):
        for item in ITEMS_WITH_PROBLEMS:
            dsm.search(item, threaded=False)
            asset = objects.asset.get_asset_for_searchstring(item)[0]
            self.assertIsNotNone(asset)
            test_date = datetime.datetime(1900, 1, 1)
            asset.price = 0
            asset.date = test_date
            for foo in dsm.update_assets([asset]):
                pass
            self.assertNotEqual(asset.date, test_date)
            self.assertNotEqual(asset.price, 0)

            self.assertIsNotNone(asset)
            count = len(asset.quotations)
            self.get_historical_prices(asset)
            self.assertNotEqual(count, len(asset.quotations))
