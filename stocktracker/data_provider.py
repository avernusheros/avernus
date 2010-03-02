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
import os, logging
from datetime import datetime, timedelta

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
                    , symbol integer
                    , datetime timestamp
                    , open real
                    , high real
                    , low real
                    , close real
                    , volume integer
                    );
                    ''')

    def insert_quotes(self, symbol, quotes):
        #quotes: list of tuples : (date, open, high, low, close, volume)
        cursor = self.dbconn.cursor()
        for q in quotes:
            cursor.execute('INSERT INTO quotations VALUES (null,?, ?,?,?,?,?,?)', (symbol, q[0], q[1], q[2], q[3], q[4], q[5]))
        self.save()
    
    def get_quote_at_date(self, symbol, date1):
        cursor = self.dbconn.cursor()
        result = cursor.execute("""
        SELECT * FROM quotations 
        WHERE symbol = ?
        AND datetime = ?""",(symbol, date1)).fetchone()
        if result is not None:    
            return ((result[2],result[3],result[4],result[5],result[6],result[7]))
        return None
    
    def get_historical_prices(self, symbol, start_date, end_date):
        cursor = self.dbconn.cursor()
        res = []
        start_date += timedelta(days = 1)
        for result in cursor.execute("""
        SELECT * FROM quotations 
        WHERE symbol=?
        AND datetime >= ?
        AND datetime <= ?
        ORDER BY datetime""",(symbol,end_date, start_date)).fetchall():
            res.append((result[2],result[3],result[4],result[5],result[6],result[7]))
        #print "foo", res
        return res
        
    def get_latest_date(self, symbol):
        res = self.dbconn.cursor().execute("SELECT MAX(datetime) FROM quotations WHERE symbol= ? ",(symbol,)).fetchone()
        print "RESULT", res
        if res[0] is None:
            return None
        return datetime.strptime(res[0], '%Y-%m-%d %H:%M:%S')
    
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
    
    def get_quote_at_date(self, symbol, date1):
        newest = self.store.get_latest_date(symbol)
        if newest is None or newest < date1:
            print "HERE", newest, date1
            self.update_history(symbol)
        return self.store.get_quote_at_date(symbol, date1)

    def update_history(self, symbol):
        if self.online():
            today = datetime.today()
            newest = self.store.get_latest_date(symbol)
            if newest == None:
                newest = datetime(today.year -20, today.month, today.day)
            new_data = updater.get_historical_prices(symbol, today, newest)
            self.store.insert_quotes(symbol, new_data)
    
    def get_historical_prices(self, symbol, start_date, end_date):
        """
        Get historical prices for the given ticker symbol.
        Returns a nested list.
        """
        #print start_date, end_date
        newest = self.store.get_latest_date(symbol)
        if newest == None or newest.date() < start_date:
            newest = datetime(end_date.year -20, end_date.month, end_date.day)
            self.update_history(symbol)
        return self.store.get_historical_prices(symbol, start_date, end_date)
        

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
