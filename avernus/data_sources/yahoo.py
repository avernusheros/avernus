# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
from BeautifulSoup import BeautifulSoup
from urllib import urlopen
import csv
import pytz
import re
import json
from datetime import datetime
from avernus.objects import stock
from avernus.controller import controller

import logging
logger = logging.getLogger(__name__)

TYPES = {'Fonds':stock.FUND, 'Aktien':stock.STOCK, 'Namensaktie':stock.STOCK, 'Vorzugsaktie':stock.STOCK}
EXCHANGE_CURRENCY = [(['NYQ', 'PNK'], 'USD'),
                     (['GER', 'BER', 'FRA', 'MUN', 'STU', 'HAN' ,'HAM' ,'DUS', 'AMS'], 'EUR'),
                     (['LSE'], 'GBP')
                     ]

class Yahoo():
    name = "yahoo"

    def __request(self, searchstring):
        try:
            url = 'http://de.finance.yahoo.com/lookup/all?s='+searchstring
            return urlopen(url)
        except:
            return None

    def __request_csv(self, symbol, stat):
        try:
            url = 'http://download.finance.yahoo.com/d/quotes.csv?s=%s&f=%s' % (symbol, stat)
            logger.debug(url)
            return urlopen(url)
        except:
            return None

    def __get_all_yahoo_ids(self, stocks):
        ids = []
        for stock in stocks:
            ids+= [source_info.info for source_info in controller.getSourceInfo(self.name, stock)]
        return '+'.join(ids)

    def update_stocks(self, stocks):
        ids = self.__get_all_yahoo_ids(stocks)
        current_stock = -1
        len_ids = 0
        res = self.__request_csv(ids, 'l1d1d3c1x')
        if not res or len(stocks) == 0:
            return
        for row in csv.reader(res):
            while len_ids == 0 and current_stock < len(stocks)-1:
                current_stock += 1
                #print current_stock, stocks
                len_ids = len(controller.getSourceInfo(self.name, stocks[current_stock]))
            len_ids -= 1
            if len(row) > 1:
                if row[1] == 'N/A':
                    continue
                new_date = datetime.strptime(row[1], '%m/%d/%Y')
                if re.match('^[0-9]{1,2}:[0-9]{2}am|pm$', row[2]):
                    hour = int(row[2].split(':')[0])
                    if 'pm' in row[2]:
                        hour+12
                    new_date = new_date.replace(hour=hour, minute=int(row[2].split(':')[1][:-2]))
                new_date = pytz.timezone('US/Eastern').localize(new_date)
                new_date = new_date.astimezone(pytz.utc)
                new_date = new_date.replace(tzinfo = None)
                if new_date > stocks[current_stock].date: #we have a newer quote
                    try:
                        stocks[current_stock].price = float(row[0])
                    except Exception as e:
                        logger.info(e)
                        continue
                    stocks[current_stock].date = new_date
                    stocks[current_stock].change = float(row[3])
                    stocks[current_stock].exchange = row[4]
            yield 1

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
        sourceInfo = controller.getSourceInfo(self.name, stock)
        if sourceInfo == []:
            print "crapballs... yahoo.update_historical_prices"
            return
        yid = sourceInfo[0].info

        #url = 'http://download.finance.yahoo.com/d/quotes.csv?s=%s&' % yid + \
        url = 'http://ichart.finance.yahoo.com/table.csv?s=%s&' % yid + \
              'a=%s&' % str(start_date.month-1) + \
              'b=%s&' % str(start_date.day) + \
              'c=%s&' % str(start_date.year) + \
              'g=d&' + \
              'd=%s&' % str(end_date.month-1) + \
              'e=%s&' % str(end_date.day) + \
              'f=%s&' % str(end_date.year) + \
              'ignore=.csv'
        logger.debug(url)
        file = urlopen(url)
        if file.info().gettype() == 'text/html':
            logger.info("no historical data found for stock: "+stock.name)
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
            return
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
                            yield (item, self, item['yahoo_id'])

    def __to_dict(self, item):
        if not item[4] in TYPES:
            return None
        res = {}
        res['name']     = item[1]
        res['yahoo_id'] = item[0]
        res['isin']     = item[2]
        res['exchange'] = item[5]
        res['type']     = TYPES[item[4]]
        for ex, cur in EXCHANGE_CURRENCY:
            if res['exchange'] in ex:
                res['currency'] = cur
                return res
        return None


if __name__ == "__main__":
    y = Yahoo()
    for item in y.search('DE0005229504'):
        print item
