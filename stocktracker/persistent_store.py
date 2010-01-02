#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/stocktracker
#    persistent_store.py: Copyright 2009 Wolfgang Steitz <wsteitz(at)gmail.com>
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

import sqlite3, logging, os
from sqlite3 import dbapi2 as sqlite
from stocktracker import objects, pubsub, config

logger = logging.getLogger(__name__)

WATCHLIST = 0
PORTFOLIO = 1


class Store:
    def __init__(self, path = None):
        self.version = 4
        if path is None:
            self.new()
        else:
            self.open(path)
        self.subscriptions = (
            (self.on_exit, "exit"),
            (self.on_remove_container, "watchlist.removed"),
            (self.on_remove_container, "portfolio.removed"),
            (self.on_remove_tag, "tag.removed"),
            (self.on_update_container, 'container.updated'),
            (self.on_update_portfolio, 'portfolio.updated'),
            (self.on_update_position, 'position.updated'),
            (self.on_remove_position, 'container.position.removed'),
            (self.on_update_stock, 'stock.updated'),
            (self.on_positon_tags_change, 'position.tags.changed'),
            (self.on_positon_merge, 'container.position.merged')
        )
        for callback, topic in self.subscriptions:
            pubsub.subscribe(topic, callback)
        
        
    def open(self, path):
        logger.debug('Opening database file %s', path)
        self.path = path
        self.dirty = False
        init = False
        if not os.path.exists(self.path):
            init = True
        self.dbconn = sqlite3.connect(self.path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        if init:
            logger.debug('Initializing', self.path)
            self.initialize()

        self.meta = self.get_meta()
        logger.debug(self.meta['version'])
        while self.meta['version'] < self.version:
            self.upgrade_db(self.meta['version'])
            self.meta = self.get_meta()
            logger.debug(self.meta)

        self.commit_if_appropriate()

    def new(self):
        path = config.config_path + '/stocktracker.db'
        i = 0
        while os.path.exists(path):
            i += 1 
            path = config.config_path + '/stocktracker_'+str(i)+'.db'  
        self.open(path)
    
    def commit_if_appropriate(self):
        if self.dirty:
            self.save()
    
    def save(self):
        import time; t = time.time()
        self.dbconn.commit()
        logger.debug("Committed in %s seconds" % (time.time()-t))
        self.dirty = False
   
    def save_as(self, file):
        import time; t = time.time()
        self.dbconn.commit()
        logger.debug("Committed in %s seconds" % (time.time()-t))
        self.dirty = False   
        #copy db to new location
        import shutil
        shutil.copyfile(self.path, file)
        self.path = file
        self.dbconn = sqlite3.connect(self.path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
   
    def close(self):
        self.dbconn.close()
        for callback, topic in self.subscriptions:
            pubsub.unsubscribe(callback)
    
    def upgrade_db(self, version):
        upgrade = False
        if version == 1:
            cursor = self.dbconn.cursor()
            cursor.execute('''
                CREATE TABLE tag (
                    id INTEGER PRIMARY KEY
                    , name text
                    );  
                    ''') 
            cursor.execute('''
                CREATE TABLE has_tag (
                    id INTEGER PRIMARY KEY
                    , position_id integer
                    , tag_id integer
                    );  
                    ''')
            upgrade = True 
            
        elif version == 2:
            cursor = self.dbconn.cursor()
            cursor.execute('''
                ALTER TABLE stock
                ADD type integer;  
                    ''')
            upgrade = True 
        elif version == 3:
            cursor = self.dbconn.cursor()
            cursor.execute('''
                ALTER TABLE container
                ADD last_update timestamp
                    ''')
            upgrade = True 
        else:
            print "upgrade to version not implemented", version
        if upgrade:
            cursor.execute('UPDATE meta SET value=? WHERE name=?', (version+1, 'version' ))
            self.save()
    
    def get_meta(self):
        try:
            results = self.dbconn.cursor().execute('SELECT * FROM meta').fetchall()
        except sqlite3.OperationalError:
            meta = {'version': 1}
        else:
            meta = {}
            for uid, key, value in results:
                # All values come in as strings but some we want to cast.
                if key == "version" or key == 'VERSION':
                    value = int(value)
                meta['version'] = value
        return meta
    
    def get_watchlists(self):
        wl = {}
        for result in self.dbconn.cursor().execute("SELECT * FROM container WHERE type =?", (0,)).fetchall():
            id, type, name, comment, cash, last_update = result
            positions = self.get_positions(id, 0)
            wl[id] = objects.Watchlist(id, name, self.model,positions, last_update, comment)
        return wl
           
    def get_portfolios(self):
        pf = {}
        for result in self.dbconn.cursor().execute("SELECT * FROM container WHERE type =?", (1,)).fetchall():
            id, type, name, comment, cash, last_update = result
            positions = self.get_positions(id, 1)
            pf[id] = objects.Portfolio(cash, id, name, self.model,positions, last_update, comment)
        return pf
    
    def get_stocks(self):
        stx = {}
        for result in self.dbconn.cursor().execute("SELECT * FROM stock").fetchall():
            id, name, symbol, isin, exchange, currency, price, date, change, type = result
            stx[id] = objects.Stock(id, name, symbol, isin, exchange, type, currency, price, date, change)
        return stx
    
    def get_tags(self):
        tags = {}
        for result in self.dbconn.cursor().execute("SELECT * FROM tag").fetchall():
            id, name = result
            tags[name] = objects.Tag(id, name, self.model)
        return tags
    
    def get_tags_from_position(self, id):
        tags = []
        for result in self.dbconn.cursor().execute("SELECT name FROM tag, has_tag WHERE tag.id = has_tag.tag_id AND has_tag.position_id = ? ",(id,)).fetchall():
            name = result[0]
            tags.append(name)
        return tags
        
    def get_positions(self, cid, type):
        pos = {}
        for result in self.dbconn.cursor().execute("SELECT * FROM position WHERE container_id=?",(cid,)).fetchall():
            id, cid, sid, buy_price, buy_date, quantity = result
            transactions = self.get_transactions(id)
            tags = self.get_tags_from_position(id)
            if type == 0:
                pos[id] = objects.WatchlistPosition(id, cid, sid, self.model, buy_price, buy_date, transactions, quantity, tags)
            elif type == 1:
                pos[id] = objects.PortfolioPosition(id, cid, sid, self.model, buy_price, buy_date, transactions, quantity, tags)
        return pos
    
    def get_transactions(self, pid):
        tas = {}
        for result in self.dbconn.cursor().execute("SELECT * FROM transactions WHERE position_id=?",(pid,)).fetchall():
            id, pos_id, type, date, quantity, price, ta_costs = result
            tas[id] = objects.Transaction(id, pos_id, type, date, quantity, price, ta_costs)
        return tas

               
    def create_container(self, name, comment, type = 0, cash = 0.0):
        cursor = self.dbconn.cursor()
        cursor.execute('INSERT INTO CONTAINER VALUES (null, ?,?, ?, ?)', (type, name,comment,cash))
        id = cursor.lastrowid
        self.dirty = True
        self.commit_if_appropriate()
        return id   
       

    def create_stock(self, name, symbol,isin,exchange, type,currency, price, date,change):
        print "TYPE", type
        cursor = self.dbconn.cursor()
        cursor.execute('INSERT INTO stock VALUES (null,?,?,?,?,?,?,?,?,?)', (name,symbol,isin, exchange,  currency, price, date, change, type))
        id = cursor.lastrowid
        self.dirty = True
        self.commit_if_appropriate()
        return id 
        
    def create_position(self, cid, sid, buy_price, buy_date, quantity):
        cursor = self.dbconn.cursor()
        cursor.execute('INSERT INTO position VALUES (null,?,?,?,?,?)', (cid, sid, buy_price, buy_date, quantity))
        id = cursor.lastrowid
        self.dirty = True
        self.commit_if_appropriate()
        return id 
    
    def create_tag(self, name):
        cursor = self.dbconn.cursor()
        cursor.execute('INSERT INTO tag VALUES (null,?)', (name,))
        id = cursor.lastrowid
        self.dirty = True
        self.commit_if_appropriate()
        return id 
        
    def create_transaction(self, pid, type, date, quantity, price, ta_costs):
        cursor = self.dbconn.cursor()
        cursor.execute('INSERT INTO transactions VALUES (null,?,?,?,?,?,?)', (pid, type, date, quantity, price, ta_costs))
        id = cursor.lastrowid
        self.dirty = True
        self.commit_if_appropriate()
        return id 

    def initialize(self):
        """
        sqlite create statements
        """
        cursor = self.dbconn.cursor()
        cursor.execute('''
            CREATE TABLE TRANSACTIONS (
                    id INTEGER PRIMARY KEY AUTOINCREMENT
                    , position_id integer
                    , type integer
                    , datetime timestamp
                    , quantity integer
                    , price real
                    , transaction_costs real
                    );
                    ''')
        cursor.execute('''  
            CREATE TABLE CONTAINER (
                id INTEGER PRIMARY KEY AUTOINCREMENT
                , type integer
                , name text
                , comment text
                , cash real
                , last_update timestamp
                );
                ''')
        cursor.execute('''
            CREATE TABLE POSITION (
                id INTEGER PRIMARY KEY AUTOINCREMENT
                , container_id integer
                , stock_id integer
                , buy_price real
                , buy_date timestamp
                , quantity integer
                );
                ''')
        cursor.execute('''
            CREATE TABLE STOCK (
                id INTEGER PRIMARY KEY AUTOINCREMENT
                , name text
                , symbol text
                , isin text
                , exchange text
                , currency text
                , price real
                , date timestamp
                , change real
                , type integer
                );
                ''')
        cursor.execute('''
            CREATE TABLE meta (
                id INTEGER PRIMARY KEY
                , name text
                , value text
                );  
                ''') 
        cursor.execute('''
            CREATE TABLE tag (
                id INTEGER PRIMARY KEY
                , name text
                );  
                ''') 
        cursor.execute('''
            CREATE TABLE has_tag (
                id INTEGER PRIMARY KEY
                , position_id integer
                , tag_id integer
                );  
                ''') 

        cursor.execute('INSERT INTO meta VALUES (null, ?, ?)'
                ,('version', self.version))
        self.dirty = True

    def clear_container(self, cid):
        for result in self.dbconn.cursor().execute("SELECT * FROM position WHERE container_id=?",(cid,)).fetchall():
            pid, cid, sid, buy_price, buy_date, quantity = result
            self.dbconn.cursor().execute('DELETE FROM transactions WHERE position_id=?',(pid,))
        self.dbconn.cursor().execute("DELETE FROM position WHERE container_id=?",(cid,))
        self.dirty = True
        self.commit_if_appropriate()

    def on_update_container(self, item):
        self.dbconn.cursor().execute('UPDATE container SET name=?, last_update=? WHERE id=?', (item.name, item.last_update, item.id))
        self.dirty = True
        self.commit_if_appropriate()
    
    def on_update_portfolio(self, item):
        self.dbconn.cursor().execute('UPDATE container SET cash=? WHERE id=?', (item.cash, item.id))
        self.dirty = True
        self.commit_if_appropriate()
        
    def on_update_position(self, item):
        self.dbconn.cursor().execute('UPDATE position SET quantity=? WHERE id=?', (item.quantity, item.id))
        self.dirty = True
        self.commit_if_appropriate()

    def on_update_stock(self, item):
        self.dbconn.cursor().execute('UPDATE stock SET price=? WHERE id=?', (item.price, item.id))
        self.dbconn.cursor().execute('UPDATE stock SET date=? WHERE id=?', (item.date, item.id))
        self.dbconn.cursor().execute('UPDATE stock SET change=? WHERE id=?', (item.change, item.id))
        self.dirty = True

    def on_remove_container(self, item):
        self.clear_container(item.id)
        self.dbconn.cursor().execute('DELETE FROM container WHERE id=?',(item.id,))
        self.dirty = True
        self.commit_if_appropriate()
        
    def on_remove_tag(self, item):
        self.dbconn.cursor().execute('DELETE FROM has_tag WHERE tag_id=?',(item.id,))
        self.dbconn.cursor().execute('DELETE FROM tag WHERE id=?',(item.id,))
        self.dirty = True
        self.commit_if_appropriate()    
        
    def on_remove_position(self, item, container):
        self.dbconn.cursor().execute('DELETE FROM position WHERE id=?',(item.id,))
        self.dbconn.cursor().execute('DELETE FROM transactions WHERE position_id=?',(item.id,))
        self.dbconn.cursor().execute('DELETE FROM has_tag WHERE position_id=?',(item.id,))
        self.dirty = True
        self.commit_if_appropriate()

    def on_positon_tags_change(self, tags, position):
        c = self.dbconn.cursor()
        c.execute('DELETE FROM has_tag WHERE position_id=?',(position.id,))
        for t in tags:
            c.execute('INSERT INTO has_tag VALUES (null, ?,?)', (position.id, t.id))
        self.dirty = True
        self.commit_if_appropriate()
    
    def on_positon_merge(self, pos1, pos2, new_pos):
        c = self.dbconn.cursor()
        c.execute('UPDATE transactions SET position_id=? WHERE position_id=? OR position_id=?', (new_pos.id, pos1.id, pos2.id))
        self.dirty = True
        self.commit_if_appropriate()
        
    def on_exit(self, message):
        if self.dirty:
            pubsub.publish("warning.dirty_exit", message.data)

    def __del__(self):
        self.commit_if_appropriate()
        self.close()
