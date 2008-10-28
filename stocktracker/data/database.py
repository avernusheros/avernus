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
        return c.fetchone()
    
    def create_tables(self):
        #stockdata
        self.con.execute('''CREATE TABLE stockdata (isin text PRIMARY KEY
                            , name text, type text)''')
        #stocks
        self.con.execute('''CREATE TABLE stocks (id INTEGER PRIMARY KEY, 
                           isin text, mic text ,currency text, yahoo_symbol text)''')
        #transactions
        self.con.execute('''CREATE TABLE transactions (id INTEGER PRIMARY KEY AUTOINCREMENT
                        , type integer, datetime timestamp, quantity integer
                                    , transaction_costs real)''')
        #exchanges
        self.con.execute('''CREATE TABLE exchanges (mic text PRIMARY KEY
                                 ,name text, countrycode text)''')
        #quotations
        self.con.execute('''CREATE TABLE quotations (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                               isin text, mic text,datetime timestamp
                                 ,price real)''')
        #portfolios
        self.con.execute('''CREATE TABLE portfolios (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                               name text, comment text,balance real
                                 ,type int)''')
        #positions
        self.con.execute('''CREATE TABLE positions (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                               porfolio_id integer, stock_id integer,
                               comment text, buydate timestamp, quantity integer,
                               buyprice real, type int, buysum real)''')                    
                                 
                                 
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
    
    def  fill_stocks_table(self):
        #ISIN, MIC, CURRENCY, YAHOO_SYMBOL
        f = open('stocks.csv')
        input = csv.reader(f, delimiter='\t')
        self.connect()
        for i in input:
            self.con.execute('INSERT INTO stocks VALUES (null,?,?,?,?)', i)


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
    
    
