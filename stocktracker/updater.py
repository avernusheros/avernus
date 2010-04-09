#!/usr/bin/env python

from stocktracker import yahoo

updater = yahoo

    
def update_stocks(stocks):
    if len(stocks) == 0:
        return
    updater.update_stocks(stocks)
     
def update_stock(stock):
    self.update_stocks([stock])
    
def get_info(symbol):
    return updater.get_info(symbol)
     
def check_symbol(symbol):
    return updater.check_symbol(symbol)

def get_historical_prices(stock, start_date, end_date):
    """
    Get historical prices for the given ticker symbol.
    Returns a nested list.
    """
    return updater.get_historical_prices(stock, start_date, end_date)
    #FIXME
    #print start_date, end_date
    from stocktracker import model
    print "newest", model.Quotation.query.last().date
    newest = model.Quotation.query().last.date
    if newest == None:
        newest = datetime.datetime(end_date.year -20, end_date.month, end_date.day)
    # newest.date(), start_date, newest.date() >= start_date
    if newest.date() < start_date:
        new_data = updater.get_historical_prices(stock.symbol, start_date, newest)
        self.store.insert_quotes(stock, new_data)
    return self.store.get_historical_prices(stock, start_date, end_date)
    

