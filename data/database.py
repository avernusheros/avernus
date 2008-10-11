import sqlite3, os, csv


class Database():
    def __init__(self, path):
        self.path = path
        self.db_conn = None
    
    def connect(self):
        if not self.db_conn:
            self.db_conn = sqlite3.connect(self.path)

    def commit(self):
        self.db_conn.commit()
    
    def create_tables(self):
        #stockdata
        self.db_conn.execute('''CREATE TABLE stockdata (isin text, name text
                                ,type text)''')
        #stocks
        self.db_conn.execute('''CREATE TABLE stocks (isin text, mic text
                                ,currency text, yahoo_symbol text)''')
        #transactions
        self.db_conn.execute('''CREATE TABLE transactions (id text
            , type integer, datetime timestamp, quantity integer
                                    ,price real, charge real)''')
        #exchanges
        self.db_conn.execute('''CREATE TABLE exchanges (mic text
                                 ,name text, countrycode text)''')

    def fill_exchanges_table(self):
        #MIC, NAME, COUNTRY_CODE
        f = open('exchanges.csv')
        input = csv.reader(f, delimiter='\t')
        self.connect()
        for i in input:
            self.db_conn.execute('INSERT INTO exchanges VALUES (?,?,?)', i)
    
    def fill_stockdata_table(self):
        #ISIN, NAME, TYPE, INDUSTRY
        f = open('stockdata.csv')
        input = csv.reader(f, delimiter='\t')
        self.connect()
        for i in input:
            self.db_conn.execute('INSERT INTO stockdata VALUES (?,?,?)', i)
    
    def  fill_stocks_table(self):
        #ISIN, MIC, CURRENCY, YAHOO_SYMBOL
        f = open('stocks.csv')
        input = csv.reader(f, delimiter='\t')
        self.connect()
        for i in input:
            self.db_conn.execute('INSERT INTO stocks VALUES (?,?,?,?)', i)


if __name__ == "__main__":
    path = 'data.db'
    os.remove(path)
    d = Database(path)
    d.connect()
    d.create_tables()
    d.fill_exchanges_table()
    d.fill_stockdata_table()
    d.fill_stocks_table()
    d.commit()
    
    
