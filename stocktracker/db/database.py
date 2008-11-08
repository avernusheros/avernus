import sqlite3, os, csv
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
            SELECT stocks.id, stockdata.isin, stockdata.name, exchanges.name
            FROM stocks, stockdata, exchanges
            WHERE stocks.isin = stockdata.isin
            AND stocks.mic = exchanges.mic
            ''')
        ret = []
        for row in c:
            ret.append(list(row))
        return ret

    def get_stock_name(self, stock_id):
        self.connect()
        c = self.con.execute('''
            SELECT stockdata.name, stocks.isin, exchanges.name
            FROM stockdata, stocks, exchanges
            WHERE stocks.id = ?
            AND stocks.isin = stockdata.isin
            AND stocks.mic = exchanges.mic
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
            FROM portfolios
            ''')
        ret = []
        for row in c.fetchall():
            item = {}
            item['id']      = row[0]
            item['name']    = row[1]
            item['comment'] = row[2]
            item['cash'] = row[3]
            item['type']    = row[4]
            ret.append(item)
        return ret

    def get_transactions(self, portfolio_id):
        self.connect()
        c = self.con.execute('''
            SELECT transactions.*, exchanges.name, stocks.isin, stockdata.name
            FROM transactions, exchanges, stockdata, stocks, positions
            WHERE transactions.portfolio_id = ?
            AND transactions.position_id = positions.id
            AND positions.stock_id = stocks.id
            AND stocks.isin = stockdata.isin
            AND stocks.mic = exchanges.mic
            ''', (portfolio_id,))
        c = c.fetchall()
        items = []
        for row in c:
            item = {}
            item['id'] = row[0]
            item['portfolio_id'] = row[1]
            item['position_id'] = row[2]
            item['type'] = row[3]
            item['datetime'] = row[4]
            item['quantity'] = row[5]
            item['price'] = row[6]
            item['transaction_costs'] = row[7]
            item['exchange'] = row[8]
            item['isin'] = row[9]
            item['name'] = row[10]
            items.append(item)
        return items

    def get_portfolio_positions(self, portfolio_id):
        self.connect()
        c = self.con.execute('''
            SELECT *
            FROM positions
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
            #get stock info
            info = self.con.execute('''
            SELECT stockdata.name, stocks.isin, exchanges.name
            FROM stocks, stockdata, exchanges
            WHERE stocks.id = ?
            AND stockdata.isin = stocks.isin
            AND stocks.mic = exchanges.mic
            ''', (item['stock_id'],))
            info = info.fetchone()
            item['name'] = info[0]
            item['isin'] = info[1]
            item['exchange'] = info[2]
            #get fundamental data
            data = self.con.execute('''
            SELECT *, max(id)
            FROM quotations
            WHERE stock_id = ?
            ''', (item['stock_id'],))
            data = data.fetchall()
            for row1 in data:
                item['price'] = row1[2]
                item['change'] = row1[3]
                item['avg_daily_volume'] = row1[4]
                item['market_cap'] = row1[5]
                item['book_value'] = row1[6]
                item['ebitda'] = row1[7]
                item['dividend_per_share'] = row1[8]
                item['dividend_yield'] = row1[9]
                item['earnings_per_share'] = row1[10]
                item['52_week_high'] = row1[11]
                item['52_week_low'] = row1[12]
                item['price_earnings_ratio'] = row1[13]
                item['datetime'] = row1[14]
            items.append(item)
        return items

    def get_portfolio_info(self, id):
        """
        @params id - integer - portfolio or watchlist ID
        """
        self.connect()
        c = self.con.execute('''
            SELECT portfolios.name
                  , portfolios.cash
                  , TOTAL(positions.buysum)
                  , COUNT(positions.id)
            FROM portfolios, positions
            WHERE positions.portfolio_id = portfolios.id
            AND portfolios.id = ?
            ''', (id,))
        c = c.fetchone()
        item = {}
        item['name']   = c[0]
        item['cash']   = c[1]
        item['buysum'] = c[2]
        item['count']  = c[3]
        if item['count'] > 0:
            c = self.con.execute('''
                SELECT p.quantity, q.price, q.change
                FROM positions as p
                , (SELECT stock_id, change, price, max(id)
                   FROM quotations
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
        #stockdata
        self.con.execute('''CREATE TABLE stockdata (isin text PRIMARY KEY
                            , name text, type text)''')
        #stocks
        self.con.execute('''CREATE TABLE stocks (id INTEGER PRIMARY KEY,
                           isin text, mic text ,currency text, yahoo_symbol text)''')
        #transactions
        self.con.execute('''
            CREATE TABLE transactions (id INTEGER PRIMARY KEY AUTOINCREMENT
                    , portfolio_id integer
                    , position_id integer
                    , type integer
                    , datetime string
                    , quantity integer
                    , price real
                    , transaction_costs real
                    )
                      ''')
        #exchanges
        self.con.execute('''CREATE TABLE exchanges (mic text PRIMARY KEY
                                 ,name text, countrycode text)''')
        #quotations
        self.con.execute('''
            CREATE TABLE quotations (id INTEGER PRIMARY KEY AUTOINCREMENT
                                    , stock_id integer
                                    , price real
                                    , change real
                                    , volume integer
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
                                    , datetime string
                                    )''')

        #portfolios
        self.con.execute('''CREATE TABLE portfolios (id INTEGER PRIMARY KEY AUTOINCREMENT,
                               name text, comment text,cash real
                                 ,type int)''')
        #positions
        self.con.execute('''
            CREATE TABLE positions (id INTEGER PRIMARY KEY AUTOINCREMENT
                    , portfolio_id integer
                    , stock_id integer
                    , comment text
                    , buydate timestamp
                    , quantity integer
                    , buyprice real
                    , type int
                    , buysum real)''')


    def fill_exchanges_table(self):
        #MIC, NAME, COUNTRY_CODE
        f = open('exchanges.csv')
        input = csv.reader(f, delimiter='\t')
        self.connect()
        for i in input:
            self.con.execute('INSERT INTO exchanges VALUES (?,?,?)', i)

    def fill_stockdata_table(self):
        #ISIN, NAME, TYPE, INDUSTRY
        f = open('stockdata.csv')
        input = csv.reader(f, delimiter='\t')
        self.connect()
        for i in input:
            self.con.execute('INSERT INTO stockdata VALUES (?,?,?)', i)

    def fill_stocks_table(self):
        #ISIN, MIC, CURRENCY, YAHOO_SYMBOL
        f = open('stocks.csv')
        input = csv.reader(f, delimiter='\t')
        self.connect()
        for i in input:
            self.con.execute('INSERT INTO stocks VALUES (null,?,?,?,?)', i)

    def add_portfolio(self, name, comment, cash, type):
        """ insert a portfolio into the database
        @params name - string - name of the portfolio to be added
        @params comment - string - comment
        @params cash - float - cash balance
        @params type - integer - type
        """
        self.connect()
        self.cur.execute('''INSERT INTO portfolios
                            VALUES (null, ?,?,?,?)'''
                            , (name, comment, cash, type))
        self.commit()
        return self.cur.lastrowid

    def remove_portfolio(self, portfolio_id):
        """ remove portfolio and all corresponding database entries
        @params portfolio_id - integer - portfolio id of the portfolio
        to be removed
        """
        self.con.execute('''
            DELETE FROM portfolios
            WHERE portfolios.id = ?
            ''' , (portfolio_id,))
        self.con.execute('''
            DELETE FROM positions
            WHERE portfolio_id = ?
            ''', (portfolio_id,))
        self.con.execute('''
            DELETE FROM transactions
            WHERE portfolio_id = ?
            ''', (portfolio_id,))
        self.commit()

    def add_position(self, portfolio_id, stock_id, comment, buy_date, quantity, buy_price, type, buy_sum):
        """adds a position to db
        @params portfolio_id - integer -
        @params stock_id - integer -
        @params comment - string -
        @params buy_date - timestamp -
        @params quantity - integer -
        @params buy_price - float -
        @params type - integer -
        @params buy_sum - float -
        """
        self.connect()
        self.cur.execute('''INSERT INTO positions
                            VALUES (null, ?,?,?,?,?,?,?,?)'''
                            , (portfolio_id, stock_id, comment, buy_date
                                ,quantity, buy_price, type, buy_sum))
        self.commit()
        return self.cur.lastrowid

    def remove_position(self, position_id):
        self.connect()
        self.con.execute('''
            DELETE FROM positions
            WHERE id = ?
            ''', (position_id,))
        self.con.execute('''
            DELETE FROM transactions
            WHERE position_id = ?
            ''', (position_id,))
        self.commit()

    def add_transaction(self, portfolio_id, position_id, type, datetime
                        , quantity,price,  transaction_costs):
        self.connect()
        self.cur.execute('''
            INSERT INTO transactions
            VALUES (null, ?,?,?,?,?,?, ?)'''
            , (portfolio_id, position_id, type, datetime, quantity, price,
                transaction_costs))
        self.commit()

    def remove_transaction(self, id):
         self.connect()
         self.con.execute('''
            DELETE FROM transactions
            WHERE id = ?
            ''', (id,))
         self.commit()

    def add_quotation(self, stock_id, price, change, volume, avg_volume
                        , market_cap, book_value, ebitda
                        , dividend_per_share, dividend_yield, eps
                        , s52_week_high, s52_week_low, price_earnings_ratio
                        , datetime):
        self.connect()
        self.cur.execute('''
            INSERT INTO quotations
            VALUES (null, ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
            , (stock_id, price, change, volume, avg_volume
                        , market_cap, book_value, ebitda
                        , dividend_per_share, dividend_yield, eps
                        , s52_week_high, s52_week_low, price_earnings_ratio
                        , datetime))

        self.commit()
        return self.cur.lastrowid





if __name__ == "__main__":
    if os.path.exists(path):
        os.remove(path)
    d = Database(path)
    d.connect()
    d.create_tables()
    d.fill_exchanges_table()
    d.fill_stockdata_table()
    d.fill_stocks_table()
    d.commit()

    print d.get_stock_list()
    print d.add_portfolio("bla", "na", 0, 1)
    d.remove_portfolio(1)

