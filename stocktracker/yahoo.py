#!/usr/bin/env python

from urllib import urlopen
import csv, pytz, logging
from datetime import datetime


logger= logging.getLogger(__name__)



def __request(symbol, stat):
    url = 'http://finance.yahoo.com/d/quotes.csv?s=%s&f=%s' % (symbol, stat)
    logger.info(url)
    return urlopen(url)


def __get_symbols_from_stocks(stocks):
    symbols = ''
    for stock in stocks:
        symbols+= stock.yahoo_symbol+'+'
    return symbols.strip('+')

def update_stocks(stocks):
    symbols = __get_symbols_from_stocks(stocks)
    
    s = 0
    res = __request(symbols, 'l1d1d3c1')
    for row in csv.reader(res):
        if row[1] == 'N/A':
            continue 
        stocks[s].price = float(row[0])
        try:
            date = datetime.strptime(row[1] + ' ' + row[2], '%m/%d/%Y %H:%M%p')
        except:
            date = datetime.strptime(row[1], '%m/%d/%Y')
        date = pytz.timezone('US/Eastern').localize(date)
        stocks[s].date = date.astimezone(pytz.utc)
        stocks[s].date = stocks[s].date.replace(tzinfo = None)
        stocks[s].change = float(row[3])
        s+=1
                         
def get_info(symbol):
    #name, isin, exchange, currency
    for row in csv.reader(__request(symbol, 'nxc4')):
        if len(row) < 2 or row[1] == 'N/A':
            return None
        return row[0], 'n/a', row[1], row[2]


        
def test_api(symbol):
    for row in csv.reader(__request(symbol, 'nxc4n0n1n2n3n4')):
        print row
     
def check_symbol(symbol):
    #FIXME
    return __request(symbol, 'e1').read().strip().strip('"') == "N/A"
    

def update_historical_prices(stock, start_date, end_date):
    """
    Update historical prices for the given ticker symbol.
    """
    from stocktracker.objects import controller
    symbol = stock.yahoo_symbol
    #print "fetch data", start_date, end_date
    url = 'http://ichart.yahoo.com/table.csv?s=%s&' % symbol + \
          'd=%s&' % str(start_date.month-1) + \
          'e=%s&' % str(start_date.day) + \
          'f=%s&' % str(start_date.year) + \
          'g=d&' + \
          'a=%s&' % str(end_date.month-1) + \
          'b=%s&' % str(end_date.day) + \
          'c=%s&' % str(end_date.year) + \
          'ignore=.csv'
    #print url
    days = urlopen(url).readlines()
    data = []
    
    for row in [day[:-2].split(',') for day in days[1:]]:
        #print row[0]
        dt = datetime.strptime(row[0], '%Y-%m-%d')
        controller.newQuotation(date=dt, stock=stock, open=float(row[1]), high=float(row[2])\
                        , low=float(row[3]), close=float(row[6]), vol=int(row[5]))
    #    data.append((dt, float(row[1]), float(row[2]), float(row[3]), float(row[6]), int(row[5])))

    #data.reverse()
    #return data #(date, open, high, low, close, vol)        , Adj. Schluss


def get_index(name):
    #FIXME could be improved to fetch stocks from all indices with one request
    from stocktracker.objects import controller
    iname, isin, exchange, currency = get_info(name)
    ex = controller.newExchange(name=exchange)
    ind = controller.newIndex(name=iname, exchange=ex,yahoo_symbol=name)
    
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
        ex = controller.newExchange(name=exchange)
        st = controller.newStock(exchange=ex, yahoo_symbol=symbol, name=sname, currency=currency)
        ind.positions.append(st)
      
        

if __name__ == "__main__":
    s = 'GOOG'
    #print check_symbol([s])
    print get_infos(['BMW.DE', 'GOOG'])
