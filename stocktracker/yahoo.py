#!/usr/bin/env python
#
#  Thanks to Corey Goldberg (corey@goldb.org) for his ystockquote module. http://www.goldb.org/ystockquote.html

from db import *
import urllib
import data_provider

def yahoo(stock_id):
    db = database.get_db()
    db.connect()
    c = db.con.execute('''
        SELECT yahoo_symbol
        FROM yahoo
        WHERE stock_id = ?
        ''', (stock_id,) )
    return c.fetchone()[0]
    

class Yahoo(data_provider.DataProvider):
        
    def __request(self, stock_id, stat):
        url = 'http://finance.yahoo.com/d/quotes.csv?s=%s&f=%s' % (stock_id, stat)
        return urllib.urlopen(url).read().strip().strip('"')

    def get_all(self, stock_id):
        """
        Get all available quote data for the given ticker symbol.
        
        Returns a dictionary.
        """
        values = self.__request(yahoo(stock_id), 'l1c1va2xj1b4j4dyekjm3m4rr5p5p6s7t1d1').split(',')
        data = {}
        data['price'] = values[0]
        data['change'] = values[1]
        data['volume'] = values[2]
        data['avg_daily_volume'] = values[3]
        data['stock_exchange'] = values[4]
        data['market_cap'] = values[5]
        data['book_value'] = values[6]
        data['ebitda'] = values[7]
        data['dividend_per_share'] = values[8]
        data['dividend_yield'] = values[9]
        data['eps'] = values[10]
        data['52_week_high'] = values[11]
        data['52_week_low'] = values[12]
        data['50day_moving_avg'] = values[13]
        data['200day_moving_avg'] = values[14]
        data['price_earnings_ratio'] = values[15]
        data['price_earnings_growth_ratio'] = values[16]
        data['price_sales_ratio'] = values[17]
        data['price_book_ratio'] = values[18]
        data['short_ratio'] = values[19]
        data['price_time'] = values[20]
        data['price_date'] = values[21]
        return data
        
    def get_price(self, stock_id): 
        return float(self.__request(yahoo(stock_id), 'l1'))
        
    def get_price_date(self, stock_id):
        return self.__request(yahoo(stock_id), 'd1')
    
    def get_price_time(self, stock_id):
        return self.__request(yahoo(stock_id), 't1')

    def get_change(self, stock_id):
        return float(self.__request(yahoo(stock_id), 'c1'))
        
    def get_volume(self, stock_id): 
        return self.__request(yahoo(stock_id), 'v')

    def get_avg_daily_volume(self, stock_id): 
        return self.__request(yahoo(stock_id), 'a2')
        
    def get_stock_exchange(self, stock_id): 
        return self.__request(yahoo(stock_id), 'x')
        
    def get_market_cap(self, stock_id):
        return self.__request(yahoo(stock_id), 'j1')
       
    def get_book_value(self, stock_id):
        return self.__request(yahoo(stock_id), 'b4')

    def get_ebitda(self, symbol): 
        return self.__request(yahoo(stock_id), 'j4')
        
    def get_dividend_per_share(self, stock_id):
        return self.__request(yahoo(stock_id), 'd')

    def get_dividend_yield(stock_id): 
        return self.__request(yahoo(stock_id), 'y')
        
    def get_earnings_per_share(self, stock_id): 
        return self.__request(yahoo(stock_id), 'e')

    def get_52_week_high(self, stock_id): 
        return self.__request(yahoo(stock_id), 'k')
        
    def get_52_week_low(self, stock_id): 
        return self.__request(yahoo(stock_id), 'j')

    def get_50day_moving_avg(symbol): 
        return self.__request(yahoo(symbol), 'm3')
        
    def get_200day_moving_avg(self, stock_id): 
        return self.__request(yahoo(stock_id), 'm4')
        
    def get_price_earnings_ratio(self, stock_id): 
        return self.__request(yahoo(stock_id), 'r')

    def get_price_earnings_growth_ratio(self, stock_id): 
        return self.__request(yahoo(stock_id), 'r5')

    def get_price_sales_ratio(self, stock_id): 
        return self.__request(yahoo(stock_id), 'p5')
        
    def get_price_book_ratio(self, stock_id): 
        return self.__request(yahoo(stock_id), 'p6')
    
    def get_short_ratio(self, stock_id): 
        return self.__request(yahoo(stock_id), 's7')
        
    def get_historical_prices(self, stock_id, start_date, end_date):
        """
        Get historical prices for the given ticker symbol.
        Date format is 'YYYYMMDD'
        Returns a nested list.
        """
        url = 'http://ichart.yahoo.com/table.csv?s=%s&' % yahoo(stock_id) + \
              'd=%s&' % str(int(end_date[4:6]) - 1) + \
              'e=%s&' % str(int(end_date[6:8])) + \
              'f=%s&' % str(int(end_date[0:4])) + \
              'g=d&' + \
              'a=%s&' % str(int(start_date[4:6]) - 1) + \
              'b=%s&' % str(int(start_date[6:8])) + \
              'c=%s&' % str(int(start_date[0:4])) + \
              'ignore=.csv'
        days = urllib.urlopen(url).readlines()
        data = [day[:-2].split(',') for day in days]
        return data


if __name__ == '__main__':
    y = Yahoo()
    print y.get_price(12)
    print y.get_price_date(1)
    print y.get_price_time(1)
