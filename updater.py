from urllib import urlopen
import csv, pytz
import pubsub
from datetime import datetime



def __request(symbol, stat):
    url = 'http://finance.yahoo.com/d/quotes.csv?s=%s&f=%s' % (symbol, stat)
    return urlopen(url)

def update_stocks(stocks):
    if len(stocks) == 0:
        return
    symbols = ''
    for stock in stocks:
        symbols+= stock.symbol+'+'
    symbols = symbols.strip('+')
    
    s = 0
    res = __request(symbols, 'l1d1d3c1')
    for row in csv.reader(res):
        print stocks[s].name, row
        stocks[s].price = float(row[0])
        try:
            date = datetime.strptime(row[1] + ' ' + row[2], '%m/%d/%Y %H:%M%p')
        except:
            date = datetime.strptime(row[1], '%m/%d/%Y')
        date = pytz.timezone('US/Eastern').localize(date)
        stocks[s].date = date.astimezone(pytz.utc)
        stocks[s].date = stocks[s].date.replace(tzinfo = None)
        stocks[s].change = float(row[3])
        pub.publish('stock.updated', stocks[s])
        s+=1
     
def update_stock(stock):
    update_stocks([stock])
    
def get_info(symbol):
    #name, isin, exchange, currency
    for row in csv.reader(__request(symbol, 'nxc4')):
        return row[0], 'n/a', row[1], row[2]
     
def check_symbol(symbol):
    return __request(symbol, 'e1').read().strip().strip('"') == "N/A"
    
    
if __name__ == "__main__":
    import objects
    
    s = [objects.Stock(0, "ge", 'ge.de', 0.0, None, None, None, None, None), objects.Stock(0, "test1", 'goog', 0.0, None, None, None, None, None)]
    update_stocks(s)
    print get_info('cbk.de')
    print check_symbol('ge.de')
