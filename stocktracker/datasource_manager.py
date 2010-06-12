#!/usr/bin/env python

from stocktracker.objects import controller
from stocktracker.objects.exchange import Exchange
from stocktracker.objects.stock import Stock, StockInfo
from stocktracker import config
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
        print self.queue
        self.current_searches = []
    
    @property
    def queue(self):
        return self._queue

    @queue.setter
    def queue(self, value):
        self._queue = value
        self.cfg.set_option('priority', self._queue, 'Plugins')
    
    def register(self, item, name):
        self.sources[name] = item
        if not name in self.queue:
            self._queue.append(name)
    
    def deregister(self, item, name):
        del self.sources[name]
        self._queue.remove(name)
        
    def search(self, searchstring, callback):
        for search in self.current_searches:
            search.stop()
        self.current_searches = [] 
        self.search_callback = callback
        for name, source in self.sources.iteritems():
            #check whether search function exists
            func = getattr(source, "search", None)
            if func:
                task = controller.GeneratorTask(func, self._item_found_callback)
                self.current_searches.append(task)
                task.start(searchstring)

    def _item_found_callback(self, item, plugin):
        #mandatory: exchange, isin, type, name
        item['exchange'] = controller.detectDuplicate(Exchange, name=item['exchange'])
        stock_info = controller.detectDuplicate(StockInfo, isin=item['isin'], type=item['type'], name=item['name']) 
        if controller.is_duplicate(Stock, exchange=item['exchange'].id, stockinfo = stock_info.id):
            return
        stock = controller.newStock(stockinfo = stock_info, **item)
        #FIXME use icon of plugin or maybe some 'web' icon
        self.search_callback(stock, 'gtk-add')

    def update_stocks(self, stocks):
        if len(stocks) == 0:
            return
        for stock in stocks:
            stock.updated = False
        source = -1
        while len(stocks) > 0 and source < len(self.queue)-1:
            source += 1
            func = getattr(self.queue[source], "update_stocks", None)
            if func:
                self.sources[self.queue[source]].update_stocks(stocks)
                stocks = filter(stocks, lambda s: s.updated)
        
    def update_stock(self, stock):
        self.update_stocks([stock])
        
    def update_historical_prices(self, stock):
        """
        Update historical prices for the stock.
        """
        today = datetime.date.today() - datetime.timedelta(days=1)
        newest = controller.getNewestQuotation(stock)
        if newest == None:
            newest = datetime.date(today.year -20, today.month, today.day)
        if newest <= today:
            #FIXME
            data = self.sources['yahoo'].update_historical_prices(stock, today, newest)
            for qt in data:
                #qt : (stock, date, open, high, low, close, vol)
                controller.newQuotation(stock=qt[0], date=qt[1],\
                                        open=qt[2], high=qt[3],\
                                        low=qt[4], close=qt[5],\
                                        vol=qt[6])
        #needed to run as generator thread
        yield 1
