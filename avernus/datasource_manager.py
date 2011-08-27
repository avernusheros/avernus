#!/usr/bin/env python

from avernus.controller import controller
from avernus.objects.stock import Stock
from avernus import pubsub
from avernus.data_sources import yahoo, onvista
import datetime, re
from avernus.gui import gui_utils


sources = {'onvista.de': onvista.Onvista(),
           'yahoo': yahoo.Yahoo()
            }
source_icons = {
                'onvista.de':'onvista',
                'yahoo':'yahoo'
                }

class DatasourceManager(object):
    
    def __init__(self):
        self.current_searches = []
        self.b_online = True
        self.search_callback = None
        pubsub.subscribe('network', self.on_network_change)
        
    def on_network_change(self, state):
        self.b_online = state
    
    def get_source_count(self):
        return len(sources.items())
 
    def search(self, searchstring, callback, complete_cb):
        self.stop_search()
        self.search_callback = callback
        if not self.b_online:
            print "OFFLINE"
            return
        for name, source in sources.iteritems():
            #check whether search function exists
            func = getattr(source, "search", None)
            if func:
                task = gui_utils.GeneratorTask(func, self._item_found_callback, complete_cb)
                self.current_searches.append(task)
                task.start(searchstring)

    def stop_search(self):
        for search in self.current_searches:
            search.stop()
        self.current_searches = [] 

    def _item_found_callback(self, item, source, source_info=None):
        #mandatory: isin, type, name
        if not self.validate_isin(item['isin']):
            return
        new = False
        stock = controller.check_duplicate(Stock, **item)
        if not stock:
            new = True
            item['source'] = source.name
            stock = controller.newStock(**item)
        if source_info is not None:
            controller.newSourceInfo(source=source.name, stock=stock, info=source_info)
        if new and self.search_callback:     
            self.search_callback(stock, source_icons[item['source']])

    def validate_isin(self, isin):
        return re.match('^[A-Z]{2}[A-Z0-9]{9}[0-9]$', isin)

    def update_stocks(self, stocks):
        if len(stocks) == 0 or not self.b_online:
            return
        for name, source in sources.iteritems():
            temp = filter(lambda s: s.source == name, stocks)
            if len(temp) > 0:
                source.update_stocks(temp)
        
    def update_stock(self, stock):
        self.update_stocks([stock])
    
    def get_historical_prices(self, stock, start_date=None, end_date=None):
        if not self.b_online:
            yield 1
        if end_date is None:
            end_date = datetime.date.today() - datetime.timedelta(days=1)
        if start_date is None:
            start_date = datetime.date(end_date.year -20, end_date.month, end_date.day)
        if start_date <= end_date:
            for qt in sources[stock.source].update_historical_prices(stock, start_date, end_date):
                #qt : (stock, exchange, date, open, high, low, close, vol)
                yield controller.newQuotation(stock=qt[0], exchange=qt[1],\
                            date=qt[2], open=qt[3], high=qt[4],\
                            low=qt[5], close=qt[6], vol=qt[7],\
                            detectDuplicates=True)
        #needed to run as generator thread
        yield 1
        
    def update_historical_prices(self, stock):
        if not self.b_online:
            yield 1
        end_date = datetime.date.today() - datetime.timedelta(days=1)
        start_date = controller.getNewestQuotation(stock)
        if start_date == None:
            start_date = datetime.date(end_date.year -20, end_date.month, end_date.day)
        yield self.get_historical_prices(stock, start_date, end_date)
