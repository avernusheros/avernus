#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/stocktracker
#    updater.py: Copyright 2009 Wolfgang Steitz <wsteitz(at)gmail.com>
#
#    This file is part of stocktracker.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.



from urllib import urlopen
import csv, pytz
from stocktracker import pubsub
from datetime import datetime



def __request(symbol, stat):
    url = 'http://finance.yahoo.com/d/quotes.csv?s=%s&f=%s' % (symbol, stat)
    return urlopen(url)

def update_stocks(stocks):
    if len(stocks) == 0:
        return
    symbols = ''
    for stock in stocks:
        symbols+= stock.symbol+'+'
    symbols = symbols.strip('+')
    
    s = 0
    res = __request(symbols, 'l1d1d3c1')
    for row in csv.reader(res):
        stocks[s].price = float(row[0])
        try:
            date = datetime.strptime(row[1] + ' ' + row[2], '%m/%d/%Y %H:%M%p')
        except:
            date = datetime.strptime(row[1], '%m/%d/%Y')
        date = pytz.timezone('US/Eastern').localize(date)
        stocks[s].date = date.astimezone(pytz.utc)
        stocks[s].date = stocks[s].date.replace(tzinfo = None)
        stocks[s].change = float(row[3])
        pubsub.publish('stock.updated', stocks[s])
        s+=1
     
def update_stock(stock):
    update_stocks([stock])
    
def get_info(symbol):
    #name, isin, exchange, currency
    for row in csv.reader(__request(symbol, 'nxc4')):
        return row[0], 'n/a', row[1], row[2]
     
def check_symbol(symbol):
    return __request(symbol, 'e1').read().strip().strip('"') == "N/A"
    
    
if __name__ == "__main__":
    import objects
    
    s = [objects.Stock(0, "ge", 'ge.de', 0.0, None, None, None, None, None, None), objects.Stock(0, "test1", 'goog', 0.0, None, None, None, None, None, None)]
    update_stocks(s)
    print get_info('cbk.de')
    print check_symbol('ge.de')
