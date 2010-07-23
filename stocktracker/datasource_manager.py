#!/usr/bin/env python

from stocktracker.objects import controller
from stocktracker.objects.stock import Stock
from stocktracker import config, pubsub
import datetime


class DatasourceManager(object):
    
    def __init__(self):
        self.sources = {}
        self.cfg = config.StocktrackerConfig()
        q = self.cfg.get_option('priority', section='Plugins')
        if q is None:
            self._queue = []
        else:
            self._queue = eval(q)
        self.current_searches = []
        pubsub.subscribe('network', self.on_network_change)
        
    @property
    def queue(self):
        return self._queue

    @queue.setter
    def queue(self, value):
        self._queue = value
        self.cfg.set_option('priority', self._queue, 'Plugins')
    
    def on_network_change(self, state):
        self.b_online = state

    def register(self, item, name):
        self.sources[name] = item
        if not name in self.queue:
            self.queue.append(name)
    
    def deregister(self, item, name):
        del self.sources[name]
        self.queue.remove(name)
        
    def search(self, searchstring, callback):
        for search in self.current_searches:
            search.stop()
        self.current_searches = [] 
        self.search_callback = callback
        if not self.b_online:
            return
        for name, source in self.sources.iteritems():
            #check whether search function exists
            func = getattr(source, "search", None)
            if func:
                task = controller.GeneratorTask(func, self._item_found_callback)
                self.current_searches.append(task)
                task.start(searchstring)

    def _item_found_callback(self, item, plugin):
        #mandatory: isin, type, name
        if controller.is_duplicate(Stock, **item):
            return
        stock = controller.newStock(**item)
        #FIXME use icon of plugin or maybe some 'web' icon
        self.search_callback(stock, 'gtk-add')

    def update_stocks(self, stocks):
        if len(stocks) == 0 or not self.b_online:
            return
        for stock in stocks:
            stock.updated = False
        source = -1
        while len(stocks) > 0 and source < len(self.queue)-1:
            source += 1
            func = getattr(self.queue[source], "update_stocks", None)
            if func:
                func(stocks)
                stocks = filter(stocks, lambda s: s.updated)
        
    def update_stock(self, stock):
        self.update_stocks([stock])
        
    def update_historical_prices(self, stock):
        """
        Update historical prices for the stock.
        """
        if not self.b_online:
            yield 1
        today = datetime.date.today() - datetime.timedelta(days=1)
        newest = controller.getNewestQuotation(stock)
        if newest == None:
            newest = datetime.date(today.year -20, today.month, today.day)
        if newest <= today:
            #FIXME
            print self.sources
            #source = self.sources[self.queue[0]]
            source = self.sources.values()[0]
            func = getattr(source, "update_historical_prices", None)
            for qt in func(stock, today, newest):
                #qt : (stock, date, open, high, low, close, vol)
                controller.newQuotation(stock=qt[0], date=qt[1],\
                                        open=qt[2], high=qt[3],\
                                        low=qt[4], close=qt[5],\
                                        vol=qt[6])
        #needed to run as generator thread
        yield 1
