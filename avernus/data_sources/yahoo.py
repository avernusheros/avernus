# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
from BeautifulSoup import BeautifulSoup
from urllib import urlopen
import csv, pytz, re, os, pickle, json
from datetime import datetime
from avernus import config

from avernus.logger import Log
from avernus.objects import stock

TYPES = {'Fonds':stock.FUND, 'Aktien':stock.STOCK, 'Namensaktie':stock.STOCK, 'Vorzugsaktie':stock.STOCK}
EXCHANGE_CURRENCY = [(['NYQ', 'PNK'], 'USD'),
                     (['GER', 'BER', 'FRA', 'MUN', 'STU', 'HAN' ,'HAM' ,'DUS'], 'EUR'),
                     (['LSE'], 'GBP')
                     ]


class Yahoo():
    name = "yahoo"

    def __init__(self):
        self.__load_yahoo_ids()
    
    def __request(self, searchstring):
        try:
            url = 'http://de.finance.yahoo.com/lookup/all?s='+searchstring          
            Log.info(url)
            return urlopen(url)
        except:
            return None
                
    def __request_csv(self, symbol, stat):
        try:
            url = 'http://finance.yahoo.com/d/quotes.csv?s=%s&f=%s' % (symbol, stat)
            Log.info(url)
            return urlopen(url)
        except:
            return None
        
    def __get_yahoo_ids(self, stocks):
        ids = []
        for stock in stocks:
            try:
                ids.append(self.yahoo_ids[(stock.isin, stock.currency)][0])
            except:
                print "no yahoo id cached"
        return '+'.join(ids)

    def __get_all_yahoo_ids(self, stocks):
        ids = []
        for stock in stocks:
            ids+= self.yahoo_ids[(stock.isin, stock.currency)]
        return '+'.join(ids)

    def update_stocks(self, stocks):
        ids = self.__get_all_yahoo_ids(stocks)
        current_stock = -1
        len_ids = 0
        res = self.__request_csv(ids, 'l1d1d3c1x')
        for row in csv.reader(res):
            if len_ids == 0:
                current_stock += 1
                len_ids = len(self.yahoo_ids[(stocks[current_stock].isin, stocks[current_stock].currency)])
            len_ids -= 1
            if len(row) > 1:
                if row[1] == 'N/A':
                    continue 
                try:
                    new_date = datetime.strptime(row[1] + ' ' + row[2], '%m/%d/%Y %H:%M%p')
                except Exception as e:
                    Log.info(e)
                    new_date = datetime.strptime(row[1], '%m/%d/%Y')
                new_date = pytz.timezone('US/Eastern').localize(new_date)
                new_date = new_date.astimezone(pytz.utc)
                new_date = new_date.replace(tzinfo = None)
                if new_date > stocks[current_stock].date: #we have a newer quote
                    try:
                        stocks[current_stock].price = float(row[0])
                    except Exception as e:
                        Log.info(e)
                        continue
                    stocks[current_stock].date = new_date
                    stocks[current_stock].change = float(row[3])
                    stocks[current_stock].exchange = row[4]
                         
    def get_info(self, symbol):
        #name, isin, exchange, currency
        for row in csv.reader(self.__request_csv(symbol, 'nxc4')):
            if len(row) < 2 or row[1] == 'N/A':
                return None
        return row[0], 'n/a', row[1], row[2]
        
    def _test_api(self, symbol):
        for row in csv.reader(self.__request_csv(symbol, 'nxc4n0n1n2n3n4')):
            print row
    
    def update_historical_prices(self, stock, start_date, end_date):
        #we should use a more intelligent way of choosing the exchange
        #e.g. the exchange with the highest volume for this stock
        yid = self.__get_yahoo_ids([stock])
        url = 'http://ichart.yahoo.com/table.csv?s=%s&' % yid + \
              'a=%s&' % str(start_date.month-1) + \
              'b=%s&' % str(start_date.day) + \
              'c=%s&' % str(start_date.year) + \
              'g=d&' + \
              'd=%s&' % str(end_date.month-1) + \
              'e=%s&' % str(end_date.day) + \
              'f=%s&' % str(end_date.year) + \
              'ignore=.csv'
        file = urlopen(url)
        if file.info().gettype() == 'text/html':
            Log.info("no historical data found for stock: "+stock.name)
            return
        days = file.readlines()
        for row in [day[:-2].split(',') for day in days[1:]]:
            dt = datetime.strptime(row[0], '%Y-%m-%d').date()
            #(stock, date, open, high, low, close, vol)
            yield (stock,stock.exchange,dt,float(row[1]),float(row[2]),\
                        float(row[3]),float(row[6]), int(row[5]))
    
    def search_without_beautifulsoup(self, searchstring):
        #does not provide isin or even lookup by isin
        url = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query=%s&callback=YAHOO.Finance.SymbolSuggest.ssCallback" % (searchstring)
        json_response = str(urlopen(url).read()).replace("YAHOO.Finance.SymbolSuggest.ssCallback(", "").replace(")","")
        for item in json.loads(json_response)['ResultSet']['Result']:
            print item
            
    def search(self, searchstring):
        doc = self.__request(searchstring)
        if doc is None:
            print "doc is none"
            return
        #1. beatifull soup does not like this part of the html file
        #2. remove newlines
        #my_massage = [(re.compile('OPTION VALUE=>---------------------<'), ''), \
        #              (re.compile('\n'), '')]
        soup = BeautifulSoup(doc)#, markupMassage=my_massage)
        for table in soup.findAll('table', summary="YFT_SL_TABLE_SUMMARY"):
            for body in table('tbody'):
                for row in body('tr'):
                    item = []
                    for s in row('td',text=True):
                        s = s.strip()
                        if s is not None and s!=unicode(''):
                            item.append(s)
                    if len(item) == 6:
                        item = self.__to_dict(item)
                        if item is not None:
                            if (item['isin'],item['currency']) in self.yahoo_ids.keys():
                                if not item['yahoo_id'] in self.yahoo_ids[(item['isin'],item['currency'])] :
                                    self.yahoo_ids[(item['isin'],item['currency'])].append(item['yahoo_id'])
                            else:
                                self.yahoo_ids[(item['isin'],item['currency'])] = [item['yahoo_id']]
                            yield (item, self)
        self.__save_yahoo_ids()
    
    #not used
    def __parse_price(self, pricestring):
        if pricestring[-1] == '$':
            price = pricestring[:-1]
            cur = '$'
        elif pricestring[-1] == 'p':
            price = pricestring[:-1]
            cur = 'GBPp'
        else:
            price, cur = pricestring.strip(';').split('&')
            if cur == 'euro' or cur == 'nbsp':
                cur = 'EUR'
        return float(price), cur
    
    def __parse_change(self, changestring, price):
        return price - (price*100 / (100 + float(changestring.strip('%'))))
                    
    def __to_dict(self, item):
        if not item[4] in TYPES:
            return None
        res = {}
        res['name']     = item[1]
        res['yahoo_id'] = item[0]
        res['isin']     = item[2]
        #res['wkn']     = item[3]
        res['exchange'] = item[5]
        res['type']     = TYPES[item[4]]
        res['price']    = float(item[3].replace('.','').replace(',','.'))
        res['date']     = datetime.utcnow().replace(year=2009)
        for ex, cur in EXCHANGE_CURRENCY:
            if res['exchange'] in ex:
                res['currency'] = cur
                return res
        return None
    
    def __load_yahoo_ids(self):
        path = os.path.join(config.config_path, 'yahoo_ids')
        if os.path.isfile(path):
            with open(path, 'r') as file:
                data = pickle.load(file)
                if type(data) == type(dict()):
                    self.yahoo_ids = data
        else:
            self.yahoo_ids = {}

    def __save_yahoo_ids(self):
        path = os.path.join(config.config_path, 'yahoo_ids')
        with open(path, 'wb') as file:
            pickle.dump(self.yahoo_ids, file)


if __name__ == "__main__":
    y = Yahoo()
    y.search('DE0009774794')
    y.request_csv('DE0009774794', 'l1d1d3c1x')
