try:
    import sqlite3, os, csv, sys
    import stocktracker.config
except ImportError, e:
    print "Import error in database.py:", e
    #sys.exit(1)
    

path = os.path.join(os.path.expanduser("~"), '.stocktracker/data.db')


instance = None

def get_db():
    global instance
    if not instance:
        instance = Database(path)
    return instance

class Database():
    def __init__(self, path):
        self.path = path
        self.con = None

    def connect(self):
        if not self.con:
            self.con = sqlite3.connect(self.path)
            self.cur = self.con.cursor()

    def commit(self):
        self.con.commit()

    def get_stock_list(self):
        self.connect()
        c = self.con.execute('''
            SELECT stock.id, security.isin, security.name, exchange.name
            FROM stock, security, exchange
            WHERE stock.security_id = security.id
            AND stock.exchange_id = exchange.id
            ''')
        ret = []
        for row in c:
            ret.append(list(row))
        return ret

    def get_stock_name(self, stock_id):
        self.connect()
        c = self.con.execute('''
            SELECT security.name, security.isin, exchange.name
            FROM security, stock, exchange
            WHERE stock.id = ?
            AND stock.security_id = security.id
            AND stock.exchange_id = exchange.id
            ''', (stock_id,) )
        c = c.fetchone()
        item = {}
        item['name']     = c[0]
        item['isin']     = c[1]
        item['exchange'] = c[2]
        return item

    def get_portfolios(self):
        self.connect()
        c = self.con.execute('''
            SELECT *
            FROM portfolio
            ''')
        ret = []
        for row in c.fetchall():
            item = {}
            item['id']      = row[0]
            item['type']    = row[1]
            item['name'] = row[2]
            item['comment'] = row[3]
            item['cash']    = row[4]
            ret.append(item)
        return ret

    def get_indices(self):
        self.connect()
        c = self.con.execute('''
            SELECT *
            FROM indices
            ''')
        ret = []
        for row in c.fetchall():
            item = {}
            item['id']      = row[0]
            item['type']    = stocktracker.config.INDEX
            item['name']    = row[1]
            item['comment'] = row[2]
            item['cash']    = 0
            ret.append(item)
        return ret

    def get_transactions(self, portfolio_id):
        self.connect()
        c = self.con.execute('''
            SELECT transactions.*, exchange.name, security.isin, security.name
            FROM transactions, exchange, security, stock, position
            WHERE position.portfolio_id = ?
            AND transactions.position_id = position.id
            AND position.stock_id = stock.id
            AND stock.security_id = security.id
            AND stock.exchange_id = exchange.id
            ''', (portfolio_id,))
        c = c.fetchall()
        items = []
        for row in c:
            item = {}
            item['id']                = row[0]
            item['position_id']       = row[1]
            item['type']              = row[2]
            item['datetime']          = row[3]
            item['quantity']          = row[4]
            item['price']             = row[5]
            item['transaction_costs'] = row[6]
            item['exchange']          = row[7]
            item['isin']              = row[8]
            item['name']              = row[9]
            items.append(item)
        return items

    def get_index_positions(self, index_id):
        self.connect()
        c = self.con.execute('''
            SELECT *
            FROM index_of_stock
            WHERE index_id = ?            
                ''', (index_id,))
        c = c.fetchall()
        items = []
        for row in c:
            item = {}
            item['index_id'] = index_id
            item['stock_id'] = row[0]
            #we need type and id to make the fundamentals treeview work
            item['id']       = index_id
            item['type']     = stocktracker.config.INDEXITEM
            item.update(self.get_stock_info(item['stock_id']))
            items.append(item)
        return items
            
    def get_portfolio_positions(self, portfolio_id):
        self.connect()
        c = self.con.execute('''
            SELECT *
            FROM position
            WHERE portfolio_id = ?
            ''', (portfolio_id,))
        c = c.fetchall()
        items = []
        for row in c:
            item = {}
            item['portfolio_id'] = portfolio_id
            item['id'] = row[0]
            item['stock_id'] = row[2]
            item['comment'] = row[3]
            item['buydate'] = row[4]
            item['quantity'] = row[5]
            item['buyprice'] = row[6]
            item['type'] = row[7]
            item['buysum'] = row[8]
            item.update(self.get_stock_info(item['stock_id']))
            items.append(item)
        return items
            
    def get_stock_info(self, stock_id):
        """
        @param stock_id: 
        """
        item = {}
        info = self.con.execute('''
        SELECT security.name, security.isin, exchange.name
        FROM stock, security, exchange
        WHERE stock.id = ?
        AND security.id = stock.security_id
        AND stock.exchange_id = exchange.id
        ''', (stock_id,))
        info = info.fetchone()
        item['name'] = info[0]
        item['isin'] = info[1]
        item['exchange'] = info[2]
        #get fundamental data
        data = self.con.execute('''
        SELECT *, max(id)
        FROM quotation
        WHERE stock_id = ?
        ''', (stock_id,))
        data = data.fetchone()
        if data[0]:
            print 'here' 
            item['price'] = data[3]
            item['change'] = data[4] 
            item['datetime'] = data[1] 
            
            data = self.con.execute('''
            SELECT *
            FROM stockdata
            WHERE stock_id = ?
            ''', (stock_id,))
            data = data.fetchone()
            if data[0]:
                item['avg_daily_volume'] = data[2]
                item['market_cap'] = data[3]
                item['book_value'] = data[4]
                item['ebitda'] = data[5]
                item['dividend_per_share'] = data[6]
                item['dividend_yield'] = data[7]
                item['eps'] = data[8]
                item['52_week_high'] = data[9]
                item['52_week_low'] = data[10]
                item['price_earnings_ratio'] = data[11]
            item['updated'] = True
        else:
            item['updated'] = False
        #return the stock item
        return item

    def get_portfolio_info(self, id):
        """
        @params id - integer - portfolio or watchlist ID
        """
        self.connect()
        c = self.con.execute('''
            SELECT name, cash
            FROM portfolio
            WHERE portfolio.id = ?
            ''', (id,))
        c = c.fetchone()
        item = {}
        item['name']   = c[0]
        item['cash']   = c[1]
        c = self.con.execute('''
            SELECT TOTAL(buysum), COUNT(id)
            FROM position
            WHERE portfolio_id = ?
            ''', (id,))
        c = c.fetchone()
        item['buysum'] = c[0]
        item['count']  = c[1]
        if item['count'] > 0:
            c = self.con.execute('''
                SELECT p.quantity, q.price, q.change
                FROM position as p
                , (SELECT stock_id, change, price, max(id)
                   FROM quotation
                   GROUP BY stock_id) as q
                WHERE p.stock_id = q.stock_id
                AND p.portfolio_id = ?
                ''', (id,))
            c = c.fetchall()
            item['value']  = 0.0
            item['change'] = 0.0
            for row in c:
                item['value']  += row[0] * row[1]
                item['change'] += row[0] * row[2]
            item['overall_change']  = item['value'] - item['buysum']
            item['percent']         = 100/(item['value']-item['change'])*item['change']
            item['overall_percent'] = 100*item['overall_change']/item['buysum']
        else:
            item['value'] = 0.0
            item['change'] = 0.0
            item['overall_change'] = 0.0
            item['percent'] = 0.0
            item['overall_percent'] = 0.0
        return item

    def create_tables(self):
        """
        sqlite create statements
        """
        self.connect()
        self.cur.executescript('''
            CREATE TABLE TRANSACTIONS (
                    id INTEGER PRIMARY KEY AUTOINCREMENT
                    , position_id integer
                    , type integer
                    , datetime timestamp
                    , quantity integer
                    , price real
                    , transaction_costs real
                    );
            CREATE TABLE PORTFOLIO (
                id INTEGER PRIMARY KEY AUTOINCREMENT
                , type integer
                , name text
                , comment text
                , cash real
                );
            CREATE TABLE POSITION (
                id INTEGER PRIMARY KEY AUTOINCREMENT
                , portfolio_id integer
                , stock_id integer
                , comment text
                , buydate timestamp
                , quantity integer
                , buyprice real
                , type integer
                , buysum real
                );
            CREATE TABLE STOCK (
                id INTEGER PRIMARY KEY AUTOINCREMENT
                , security_id text
                , exchange_id text
                , currency text
                );
            CREATE TABLE INDICES (
                id INTEGER PRIMARY KEY AUTOINCREMENT
                , symbol text
                , name text
                , country_code text
                );
            CREATE TABLE INDEX_OF_STOCK (
                stock_id integer
                , index_id integer
                );
            CREATE TABLE YAHOO (
                stock_id integer PRIMARY KEY
                , yahoo_symbol text
                );
            CREATE TABLE SECURITY (
                id INTEGER PRIMARY KEY AUTOINCREMENT
                , isin text
                , name text
                , type integer
                );
            CREATE TABLE EXCHANGE (
                id INTEGER PRIMARY KEY AUTOINCREMENT
                , name text
                , mic text
                , country_code text
                );
            CREATE TABLE QUOTATION (
                id INTEGER PRIMARY KEY AUTOINCREMENT
                , datetime timestamp
                , stock_id integer
                , price real
                , change real
                , volume integer
                );
            CREATE TABLE STOCKDATA (
                stock_id integer PRIMARY KEY
                , avg_volume integer
                , market_cap real
                , book_value real
                , ebitda real
                , dividend_per_share real
                , dividend_yield real
                , eps real
                , s52_week_high real
                , s52_week_low real
                , price_earnings_ratio real
                , last_update timestamp
                );                
            ''')

    def fill_tables(self):
        f = open(os.path.join(sys.path[0], '../../share/stockdata/exchanges.csv'))
        input = csv.reader(f, delimiter='\t')
        self.connect()
        for i in input:
            self.con.execute('INSERT INTO EXCHANGE VALUES (null, ?,?,?)', (i[1],i[0],i[2]))

        f = open(os.path.join(sys.path[0], '../../share/stockdata/stockdata.csv'))
        input = csv.reader(f, delimiter='\t')
        for i in input:
            self.con.execute('INSERT INTO SECURITY VALUES (NULL, ?,?,?)', i)
            
        f = open(os.path.join(sys.path[0], '../../share/stockdata/index.csv'))
        input = csv.reader(f, delimiter='\t')
        for i in input:
            self.con.execute('INSERT INTO indices VALUES (NULL, ?,?,?)', i)
                
        f = open(os.path.join(sys.path[0], '../../share/stockdata/stocks.csv'))
        input = csv.reader(f, delimiter='\t')
        for i in input:
            d = self.cur.execute('SELECT id FROM exchange WHERE mic = ?', (i[1],))
            exchange_id = d.fetchone()[0]
            d = self.cur.execute('SELECT id FROM security WHERE isin = ?', (i[0],))
            security_id = d.fetchone()[0]
            self.cur.execute('INSERT INTO STOCK VALUES (null,?,?,?)', (security_id,exchange_id,i[2] ))
            stock_id = self.cur.lastrowid
            self.cur.execute('INSERT INTO YAHOO VALUES (?,? )', (stock_id, i[3]))
            if i[4]: #we know the index of the stock
                d = self.cur.execute('''SELECT id
                                        FROM indices
                                        WHERE symbol = ?''', (i[4],))
                index_id = d.fetchone()[0]
                if index_id: #index exists in our table indexS
                    self.cur.execute('''INSERT INTO index_of_stock 
                                        VALUES (?,?)'''
                                        , (stock_id, index_id))

    def add_portfolio(self, item):
        """ insert a portfolio into the database
        @params name - string - name of the portfolio to be added
        @params comment - string - comment
        @params cash - float - cash balance
        @params type - integer - type
        """
        self.connect()
        self.cur.execute('''INSERT INTO portfolio
                            VALUES (null, ?,?,?,?)'''
                            , (item['type'], item['name'], item['comment'], item['cash']))
        self.commit()
        return self.cur.lastrowid

    def remove_portfolio(self, portfolio_id):
        """ remove portfolio and all corresponding database entries
        @params portfolio_id - integer - portfolio id of the portfolio
        to be removed
        """
        self.con.execute('''
            DELETE FROM portfolio
            WHERE portfolio.id = ?
            ''' , (portfolio_id,))
        self.con.execute('''
            DELETE FROM position
            WHERE portfolio_id = ?
            ''', (portfolio_id,))
        self.con.execute('''
            DELETE FROM transactions
            WHERE transactions.position_id 
            IN (SELECT position.id
                FROM position
                WHERE position.portfolio_id = ?)
            ''', (portfolio_id,))
        self.commit()

    def add_position(self, item):
        """
        adds a position to db
        @param item - the item to add
        """
        self.connect()
        self.cur.execute('''INSERT INTO position
                            VALUES (null, ?,?,?,?,?,?,?,?)'''
                            , (item['portfolio_id'],item['stock_id']
                                , item['comment'], item['buydate']
                                , item['quantity'], item['buyprice']
                                , item['type'], item['buy_sum']))
        self.commit()
        return self.cur.lastrowid

    def remove_position(self, position_id):
        self.connect()
        self.con.execute('''
            DELETE FROM position
            WHERE id = ?
            ''', (position_id,))
        self.con.execute('''
            DELETE FROM transactions
            WHERE position_id = ?
            ''', (position_id,))
        self.commit()

    def add_transaction(self, item):
        self.connect()
        self.cur.execute('''
            INSERT INTO transactions
            VALUES (null, ?,?,?,?,?,?)'''
            , (item['position_id']
            , item['type'], item['datetime'], item['quantity']
            , item['price'], item['transaction_costs']))
        self.commit()

    def remove_transaction(self, id):
         self.connect()
         self.con.execute('''
            DELETE FROM transactions
            WHERE id = ?
            ''', (id,))
         self.commit()

    def add_quotation(self, item):
        self.connect()
        self.cur.execute('''
            INSERT INTO quotation
            VALUES (null, ?,?,?,?,?)'''
            , (item['datetime'],item['stock_id'],item['price']
             ,item['change'],item['volume']))
        self.cur.execute('''
        DELETE FROM stockdata
        WHERE stock_id = ?
        ''', (item['stock_id'],))
        self.cur.execute('''
        INSERT INTO stockdata
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)'''
        , (item['stock_id'],item['avg_daily_volume'], item['market_cap']
        , item['book_value'], item['ebitda'], item['dividend_per_share']
        , item['dividend_yield'], item['eps'], item['52_week_low']
        , item['52_week_high'], item['price_earnings_ratio']
        , item['datetime']))
        self.commit()
        return self.cur.lastrowid


if __name__ == "__main__":
    if os.path.exists(path):
        os.remove(path)
    d = Database(path)
    d.connect()
    d.create_tables()
    d.fill_tables()
    d.commit()
