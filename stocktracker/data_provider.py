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


from sqlite3 import dbapi2 as sqlite
import sqlite3
from stocktracker import config, pubsub
from stocktracker import yahoo as updater
import os, logging, datetime

logger = logging.getLogger(__name__)



class Store:
    def __init__(self, path):
        self.path = path
        if not os.path.exists(self.path):
            init = True
        else: init = False
        self.dbconn = sqlite3.connect(self.path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        if init:
            self.initialize()

        self.save()

        self.subscriptions = (
            (self.on_exit, "exit"),
        )
        for callback, topic in self.subscriptions:
            pubsub.subscribe(topic, callback)
    
    
    def close(self):
        self.dbconn.close()
        for callback, topic in self.subscriptions:
            pubsub.unsubscribe(callback)
    
    def save(self):
        import time; t = time.time()
        self.dbconn.commit()
        logger.debug("Committed in %s seconds" % (time.time()-t))
        self.dirty = False

    def initialize(self):
        """
        sqlite create statements
        """
        cursor = self.dbconn.cursor()
        cursor.execute('''
            CREATE TABLE QUOTATIONS (
                    id INTEGER PRIMARY KEY AUTOINCREMENT
                    , stock_id integer
                    , datetime timestamp
                    , open real
                    , high real
                    , low real
                    , close real
                    , volume integer
                    );
                    ''')

    def insert_quotes(self, stock, quotes):
        #quotes: list of tuples : (date, open, high, low, close, volume)
        cursor = self.dbconn.cursor()
        for q in quotes:
            cursor.execute('INSERT INTO quotations VALUES (null,?, ?,?,?,?,?,?)', (stock.id, q[0], q[1], q[2], q[3], q[4], q[5]))
        self.save()
    
    def get_historical_prices(self, stock, start_date, end_date):
        cursor = self.dbconn.cursor()
        res = []
        start_date += datetime.timedelta(days = 1)
        for result in cursor.execute("""
        SELECT * FROM quotations 
        WHERE stock_id=?
        AND datetime >= ?
        AND datetime <= ?
        ORDER BY datetime""",(stock.id,end_date, start_date)).fetchall():
            res.append((result[2],result[3],result[4],result[5],result[6],result[7]))
        #print "foo", res
        return res
        
    def get_latest_date(self, stock):
        res = self.dbconn.cursor().execute("SELECT MAX(datetime) FROM quotations WHERE stock_id= ? ",(stock.id,)).fetchone()
        if res[0] is None:
            return None
        return datetime.datetime.strptime(res[0], '%Y-%m-%d %H:%M:%S')
    
    def on_exit(self, message):
        pass

    def __del__(self):
        self.save()
        self.close()


class DataProvider():
    def __init__(self):
        self.store = Store(config.quotes_file)

    def online(self):
        return True
    
    def update_stocks(self, stocks):
        if len(stocks) == 0:
            return
        if self.online():
            updater.update_stocks(stocks)
         
    def update_stock(self, stock):
        self.update_stocks([stock])
        
    def get_info(self, symbol):
        if self.online():
            #name, isin, exchange, currency
            return updater.get_info(symbol)
         
    def check_symbol(self, symbol):
        if self.online():
            return updater.check_symbol(symbol)
    
    def get_historical_prices(self, stock, start_date, end_date):
        """
        Get historical prices for the given ticker symbol.
        Returns a nested list.
        """
        #print start_date, end_date
        newest = self.store.get_latest_date(stock)
        if newest == None:
            newest = datetime.datetime(end_date.year -20, end_date.month, end_date.day)
        # newest.date(), start_date, newest.date() >= start_date
        if self.online() and newest.date() < start_date:
            new_data = updater.get_historical_prices(stock.symbol, start_date, newest)
            self.store.insert_quotes(stock, new_data)
        return self.store.get_historical_prices(stock, start_date, end_date)
        

if __name__ == "__main__":
    #from objects import Stock
    import datetime
    
    #s = [objects.Stock(0, "ge", 'ge.de', 0.0, None, None, None, None, None, None), objects.Stock(0, "test1", 'goog', 0.0, None, None, None, None, None, None)]
    #update_stocks(s)
    #print get_info('cbk.de')
    #print check_symbol('ge.de')

    date1 = datetime.date(2009, 11, 25)
    date2 = datetime.date(2009, 11, 24)
    dp = DataProvider()
    dp.get_historical_prices('GE', date1, date2)
