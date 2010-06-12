# -*- coding: utf-8 -*-

import gtk, csv, pytz
from urllib import urlopen
from datetime import datetime

class YahooCSV():
    configurable = False
    
    def __init__(self):
        self.name = 'yahoo'

    def activate(self):
        self.api.register_datasource(self, self.name)
                
    def deactivate(self):
        self.api.deregister_datasource(self, self.name)
            
    def __request(self, symbol, stat):
        url = 'http://finance.yahoo.com/d/quotes.csv?s=%s&f=%s' % (symbol, stat)
        self.api.logger.info(url)
        return urlopen(url)
        
    def __get_symbols_from_stocks(self, stocks):
        return '+'.join(s.yahoo_symbol for s in stocks)

    def update_stocks(self, stocks):
        symbols = self.__get_symbols_from_stocks(stocks)
        s = 0
        res = self.__request(symbols, 'l1d1d3c1')
        for row in csv.reader(res):
            if len(row) > 1:
                if row[1] == 'N/A':
                    s+=1
                    continue 
                try:
                    stocks[s].price = float(row[0])
                except Exception as e:
                    self.api.logger.info(e)
                    stocks[s].price = 0.0
                try:
                    date = datetime.strptime(row[1] + ' ' + row[2], '%m/%d/%Y %H:%M%p')
                except Exception as e:
                    self.api.logger.info(e)
                    date = datetime.strptime(row[1], '%m/%d/%Y')
                date = pytz.timezone('US/Eastern').localize(date)
                stocks[s].date = date.astimezone(pytz.utc)
                stocks[s].date = stocks[s].date.replace(tzinfo = None)
                stocks[s].change = float(row[3])
                stocks[s].updated = True
                s+=1
                         
    def get_info(self, symbol):
        #name, isin, exchange, currency
        for row in csv.reader(self.__request(symbol, 'nxc4')):
            if len(row) < 2 or row[1] == 'N/A':
                return None
        return row[0], 'n/a', row[1], row[2]
        
    def _test_api(self, symbol):
        for row in csv.reader(self.__request(symbol, 'nxc4n0n1n2n3n4')):
            print row
    
    def update_historical_prices(self, stock, start_date, end_date):
        """
        Update historical prices for the given stock.
        """
        symbol = stock.yahoo_symbol
        self.api.logger.debug("fetch data"+ str(start_date)+ str(end_date))
        url = 'http://ichart.yahoo.com/table.csv?s=%s&' % symbol + \
              'd=%s&' % str(start_date.month-1) + \
              'e=%s&' % str(start_date.day) + \
              'f=%s&' % str(start_date.year) + \
              'g=d&' + \
              'a=%s&' % str(end_date.month-1) + \
              'b=%s&' % str(end_date.day) + \
              'c=%s&' % str(end_date.year) + \
              'ignore=.csv'
        days = urlopen(url).readlines()
        data = []
        
        for row in [day[:-2].split(',') for day in days[1:]]:
            dt = datetime.strptime(row[0], '%Y-%m-%d').date()
            #(stock, date, open, high, low, close, vol)
            data.append((stock,dt,float(row[1]),float(row[2]),\
                        float(row[3]),float(row[6]), int(row[5])))
        return data


if __name__ == '__main__':
    class Stock():
        yahoo_symbol = ''
    s =Stock()
    s.yahoo_symbol = 'GOOG'
    y = YahooCSV()
    y.update_stocks([s])
    print s.change
