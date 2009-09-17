import sqlite3, logging, os
from sqlite3 import dbapi2 as sqlite
from pubsub import pub
import objects

logger = logging.getLogger(__name__)

WATCHLIST = 0
PORTFOLIO = 1


class Store:
    def __init__(self, path):
        self.path = path
        self.version = 1
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

        self.subscriptions = (
            (self.on_exit, "exit"),
            (self.on_remove_container, "watchlist.removed"),
            (self.on_remove_container, "portfolio.removed"),
            (self.on_update_container, 'container.updated'),
            (self.on_remove_position, 'container.position.removed'),
            (self.on_update_stock, 'stock.updated')
        )
        for callback, topic in self.subscriptions:
            pub.subscribe(callback, topic)
    
    def commit_if_appropriate(self):
        if self.dirty:
            self.save()
    
    def save(self):
        import time; t = time.time()
        self.dbconn.commit()
        logger.debug("Committed in %s seconds" % (time.time()-t))
        self.dirty = False
   
    def close(self):
        self.dbconn.close()
        for callback, topic in self.subscriptions:
            pub.unsubscribe(callback)
    
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
            id, type, name, comment, cash = result
            positions = self.get_positions(id)
            wl[id] = objects.Watchlist(id, name, self.model,positions, comment)
        return wl
           
    def get_portfolios(self):
        pf = {}
        for result in self.dbconn.cursor().execute("SELECT * FROM container WHERE type =?", (1,)).fetchall():
            id, type, name, comment, cash = result
            positions = self.get_positions(id)
            pf[id] = objects.Portfolio(cash, id, name, self.model,positions, comment)
        return pf
    
    def get_stocks(self):
        stx = {}
        for result in self.dbconn.cursor().execute("SELECT * FROM stock").fetchall():
            id, name, symbol, isin, exchange, currency, price, date, change = result
            stx[id] = objects.Stock(id, name, symbol, isin, exchange, currency, price, date, change)
        return stx
         
        
    def get_positions(self, cid):
        pos = {}
        for result in self.dbconn.cursor().execute("SELECT * FROM position WHERE container_id=?",(cid,)).fetchall():
            id, cid, sid, buy_price, buy_date, amount = result
            transactions = self.get_transactions(id)
            pos[id] = objects.Position(id, cid, sid, self.model, buy_price, buy_date, transactions, amount)
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
       

    def create_stock(self, name, symbol,isin,exchange,currency, price, date,change):
        cursor = self.dbconn.cursor()
        cursor.execute('INSERT INTO stock VALUES (null,?,?,?,?,?,?,?,?)', (name,symbol,isin, exchange, currency, price, date, change))
        id = cursor.lastrowid
        self.dirty = True
        self.commit_if_appropriate()
        return id 
        
    def create_position(self, cid, sid, buy_price, buy_date, amount):
        cursor = self.dbconn.cursor()
        cursor.execute('INSERT INTO position VALUES (null,?,?,?,?,?)', (cid, sid, buy_price, buy_date, amount))
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
                );
                ''')
        cursor.execute('''
            CREATE TABLE POSITION (
                id INTEGER PRIMARY KEY AUTOINCREMENT
                , container_id integer
                , stock_id integer
                , buy_price real
                , buy_date timestamp
                , amount integer
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
                );
                ''')
        cursor.execute('''
            CREATE TABLE meta (
                id INTEGER PRIMARY KEY
                , name text
                , value text
                );  
                ''') 
        cursor.execute('INSERT INTO meta VALUES (null, ?, ?)'
                ,('version', self.version))
        self.dirty = True

    def clear_container(self, container):
        print "TODO: clear everything connected to this container"

    def on_update_container(self, item):
        self.dbconn.cursor().execute('UPDATE container SET name=? WHERE id=?', (item.name, item.id))
        self.dirty = True
        self.commit_if_appropriate()

    def on_update_stock(self, item):
        self.dbconn.cursor().execute('UPDATE stock SET price=? WHERE id=?', (item.price, item.id))
        self.dbconn.cursor().execute('UPDATE stock SET date=? WHERE id=?', (item.date, item.id))
        self.dbconn.cursor().execute('UPDATE stock SET change=? WHERE id=?', (item.change, item.id))
        self.dirty = True
        self.commit_if_appropriate()

    def on_remove_container(self, item):
        self.clear_container(item)
        self.dbconn.cursor().execute('DELETE FROM container WHERE id=?',(item.id,))
        self.dirty = True
        self.commit_if_appropriate()
        
    def on_remove_position(self, item, container):
        self.dbconn.cursor().execute('DELETE FROM position WHERE id=?',(item.id,))
        self.dirty = True
        self.commit_if_appropriate()

    def on_exit(self, message):
        if self.dirty:
            pub.sendMessage("warning.dirty_exit", message.data)

    def __del__(self):
        self.commit_if_appropriate()
        self.close()
