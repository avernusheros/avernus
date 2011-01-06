#!/usr/bin/env python

from avernus.objects import controller
from avernus.objects.stock import Stock
from avernus import pubsub
from avernus.data_sources import yahoo, onvista
import datetime, re


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
                task = controller.GeneratorTask(func, self._item_found_callback, complete_cb)
                self.current_searches.append(task)
                task.start(searchstring)

    def stop_search(self):
        for search in self.current_searches:
            search.stop()
        self.current_searches = [] 

    def _item_found_callback(self, item, source):
        #mandatory: isin, type, name
        if controller.is_duplicate(Stock, **item):
            return
        if not self.validate_isin(item['isin']):
            print "false isin", item['isin']
            return
        item['source'] = source.name
        stock = controller.newStock(**item)
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
        
    def update_historical_prices(self, stock):
        if not self.b_online:
            yield 1
        today = datetime.date.today() - datetime.timedelta(days=1)
        newest = controller.getNewestQuotation(stock)
        if newest == None:
            newest = datetime.date(today.year -20, today.month, today.day)
        if newest <= today:
            for qt in sources[stock.source].update_historical_prices(stock, newest, today):
                #qt : (stock, exchange, date, open, high, low, close, vol)
                controller.newQuotation(stock=qt[0], exchange=qt[1],\
                            date=qt[2], open=qt[3], high=qt[4],\
                            low=qt[5], close=qt[6], vol=qt[7],\
                            detectDuplicates=True)
        #needed to run as generator thread
        yield 1
