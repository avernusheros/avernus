#!/usr/bin/env python

import unittest
from avernus.data_sources import onvista, yahoo
from avernus.datasource_manager import DatasourceManager
from avernus.objects import model, store
from avernus.controller import controller
import datetime

dbfile = ":memory:"
create = True



class DataSourcesTest(unittest.TestCase):

    def setUp(self):
        self.store = store.Store(dbfile)
        model.store = self.store
        controller.createTables()
        self.dsm = DatasourceManager()
        
    def test_yahoo_search(self):
        y = yahoo.Yahoo()
        for res in y.search('google'): 
            data = res[0]
            self.assertTrue(len(data['isin']) == 12)
            self.assertIsNotNone(data['exchange'])
            self.assertIsNotNone(data['name'])
            self.assertIsNotNone(data['currency'])
            self.assertTrue(data['type'] < 10)
            self.assertTrue(data['type'] >= 0)

    
    def test_onvista_search(self):
        o = onvista.Onvista()
        for res in o.search("DE0008474248"):
            data = res[0]
            self.assertTrue(len(data['isin']) == 12)
            self.assertIsNotNone(data['exchange'])
            self.assertIsNotNone(data['name'])
            self.assertIsNotNone(data['currency'])
            self.assertTrue(data['type'] < 10)
            self.assertTrue(data['type'] >= 0)
            
    def put_stocks_in_db(self):
        o = onvista.Onvista()
        for res in o.search("DE0008474248"):
            item, source = res
            self.dsm._item_found_callback(item, source)
        y = yahoo.Yahoo()
        for res in y.search('google'):
            item, source, source_info= res
            self.dsm._item_found_callback(item, source, source_info) 

    def test_update_stocks(self):
        self.put_stocks_in_db()
        test_date = datetime.datetime(1900, 1, 1)
        for st in controller.getAllStock():
            st.price = 0
            st.date = test_date
        self.dsm.update_stocks(controller.getAllStock())
        for st in controller.getAllStock():
            self.assertNotEqual(st.date, test_date)
            self.assertNotEqual(st.price, 0)

    def test_historicals(self):
        self.put_stocks_in_db()
        for st in controller.getAllStock():
            count = len(controller.getAllQuotationsFromStock(st))
            #loops needed, since the dsm uses generators
            for foo in self.dsm.update_historical_prices(st):
                for bar in foo:
                    pass
            self.assertNotEqual(count, len(controller.getAllQuotationsFromStock(st)))
