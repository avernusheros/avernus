#!/usr/bin/env python


class DatasourceManager():
    
    def __init__(self):
        self.sources = {}

    def register(self, item, name):
        self.sources[name] = item
    
    def deregister(self, item, name):
        del self.sources[name]
        
    def search(self, searchstring):
        for name, source in self.sources.iteritems():
            #if source has function search:
                source.search(searchstring)

    def update_stocks(self, stocks):
        if len(stocks) == 0:
            return
        for name, source in self.sources.iteritems():
            if source.update:
                source.update(stocks)
        
    def update_stock(self, stock):
        self.update_stocks([stock])
        
    def update_historical_prices(self, stock):
        """
        Update historical prices for the given ticker symbol.
        """
        from stocktracker.objects import controller
        today = datetime.date.today() - datetime.timedelta(days=1)
        newest = controller.getNewestQuotation(stock)
        if newest == None:
            newest = datetime.date(today.year -20, today.month, today.day)
        #print newest, today
        if newest <= today:
            updater.update_historical_prices(stock, today, newest)
        yield 1
