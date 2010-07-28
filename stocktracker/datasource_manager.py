#!/usr/bin/env python

from stocktracker.objects import controller
from stocktracker.objects.stock import Stock
from stocktracker import pubsub
from stocktracker.data_sources import yahoo, onvista
import datetime


sources = {'onvista.de': onvista.Onvista(),
           'yahoo': yahoo.Yahoo()
            }

class DatasourceManager(object):
    
    def __init__(self):
        self.current_searches = []
        pubsub.subscribe('network', self.on_network_change)
        
    def on_network_change(self, state):
        self.b_online = state
 
    def search(self, searchstring, callback):
        self.stop_search()
        self.search_callback = callback
        if not self.b_online:
            print "OFFLINE"
            return
        for name, source in sources.iteritems():
            #check whether search function exists
            func = getattr(source, "search", None)
            if func:
                task = controller.GeneratorTask(func, self._item_found_callback)
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
        item['source'] = source.name
        stock = controller.newStock(**item)
        #FIXME use icon of source
        self.search_callback(stock, 'gtk-add')

    def update_stocks(self, stocks):
        if len(stocks) == 0 or not self.b_online:
            return
        for stock in stocks:
            stock.updated = False
        for name, source in sources.iteritems():
            temp = filter(lambda s: s.source == name, stocks)
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
                #qt : (stock, date, open, high, low, close, vol)
                controller.newQuotation(stock=qt[0], date=qt[1],\
                                        open=qt[2], high=qt[3],\
                                        low=qt[4], close=qt[5],\
                                        vol=qt[6], detectDuplicates=True)
        #needed to run as generator thread
        yield 1
