#!/usr/bin/env python

from stocktracker.objects import controller
from stocktracker.objects.exchange import Exchange
from stocktracker.objects.stock import Stock, StockInfo
import datetime


class DatasourceManager():
    
    def __init__(self):
        self.sources = {}
        self.current_searches = []

    def register(self, item, name):
        self.sources[name] = item
    
    def deregister(self, item, name):
        del self.sources[name]
        
    def search(self, searchstring, callback):
        for search in self.current_searches:
            search.stop()
        self.current_searches = []
        self.search_callback = callback
        for name, source in self.sources.iteritems():
            #FIXME
            #if source has function search:
                task = controller.GeneratorTask(source.search, self._item_found_callback)
                self.current_searches.append(task)
                task.start(searchstring)

    def _item_found_callback(self, item, plugin):
        exchange = controller.detectDuplicate(Exchange, name=item['exchange'])
        stock_info = controller.detectDuplicate(StockInfo, isin=item['isin'], type=item['type'], name=item['name']) 
        if controller.is_duplicate(Stock, exchange=exchange.id, stockinfo = stock_info.id):
            return
        stock = controller.newStock(price=item['price'],\
                            change=item['change'],\
                            exchange=exchange,\
                            stockinfo = stock_info,\
                            yahoo_symbol=item['yahoo_symbol']
                            )
        #FIXME use icon of plugin or maybe some 'web' icon
        self.search_callback(stock, 'gtk-add')

    def update_stocks(self, stocks):
        if len(stocks) == 0:
            return
        #FIXME sources should have priorities
        #try the one with highest prio, if unsuccessfull the next etc
        self.sources['yahoo'].update_stocks(stocks)
        
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
