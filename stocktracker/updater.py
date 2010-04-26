#!/usr/bin/env python

from stocktracker import yahoo, logger
import datetime

updater = yahoo

    
def update_stocks(stocks):
    if len(stocks) == 0:
        return
    updater.update_stocks(stocks)
     
def update_stock(stock):
    update_stocks([stock])
    
def get_info(symbol):
    return updater.get_info(symbol)
     
def check_symbol(symbol):
    return updater.check_symbol(symbol)

def update_historical_prices(stock):
    """
    Update historical prices for the given ticker symbol.
    """
    from stocktracker.objects import controller
    today = datetime.date.today()
    today = datetime.date(today.year, today.month, today.day-1)
    newest = controller.getNewestQuotation(stock)
    #model.Quotation.query.filter_by(stock=stock).first()
    if newest == None:
        newest = datetime.date(today.year -20, today.month, today.day)
    else:
        newest = newest.date()
    print newest, today
    if newest <= today:
        updater.update_historical_prices(stock, today, newest)
