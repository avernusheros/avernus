#!/usr/bin/env python

from urllib import urlopen
import csv
from datetime import datetime

from stocktracker import logger

logger= logger.logger


def __request(symbol, stat):
    url = 'http://finance.yahoo.com/d/quotes.csv?s=%s&f=%s' % (symbol, stat)
    logger.info(url)
    return urlopen(url)


def get_indices(indices):
    from stocktracker.objects import controller
    from stocktracker.objects.stock import Stock
    from stocktracker.objects.exchange import Exchange
    from stocktracker.objects.container import Index
    
    current = 0
    count = len(indices)
    
    
    for name in indices:
        iname, isin, exchange, currency = get_info(name)
        ex = controller.detectDuplicate(Exchange,name=exchange)
        ind = controller.detectDuplicate(Index,name=iname, exchange=ex,yahoo_symbol=name, currency=currency)
        
        #get symbols from yahoo
        name = name.replace('^', 'E')
        symbols = ''
        for row in csv.reader(__request('@%5'+name, 's')):
            if len(row) > 0:
                symbols+=row[0]+'+'
        symbols = symbols.strip('+')
            
        #get infos for symbols    
        for row in csv.reader(__request(symbols, 'nxc4s')):  
            sname, exchange, currency, symbol = row
            ex = controller.detectDuplicate(Exchange, name=exchange)
            #ex = controller.newExchange(name=exchange)
            st = controller.detectDuplicate(Stock,exchange=ex, yahoo_symbol=symbol, name=sname, currency=currency)
            #st = controller.newStock(exchange=ex, yahoo_symbol=symbol, name=sname, currency=currency)
            ind.positions.append(st)
        current += 1
        
        yield float(current)/count*100
