# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
from bs4 import BeautifulSoup
from urllib import urlopen
import csv
import pytz
import re
import json
import logging
from datetime import datetime



logger = logging.getLogger(__name__)

TYPES = {'Fonds': 'fund',
         'Aktien': 'stock',
         'Namensaktie': 'stock',
         'Vorzugsaktie': 'stock',
         'ETF': "etf",
         }
EXCHANGE_CURRENCY = [(['NYQ', 'PNK'], 'USD'),
                     (['GER', 'BER', 'FRA', 'MUN', 'STU', 'HAN' , 'HAM' , 'DUS', 'AMS'], 'EUR'),
                     (['LSE'], 'GBP')
                     ]


class DataSource():
    name = "yahoo"

    def __request(self, searchstring):
        try:
            url = 'http://de.finance.yahoo.com/lookup/all?s=' + searchstring
            return urlopen(url)
        except:
            return None

    def __request_csv(self, symbol, stat):
        try:
            url = 'http://download.finance.yahoo.com/d/quotes.csv?s=%s&f=%s' % (symbol, stat)
            logger.debug(url)
            return urlopen(url)
        except:
            logger.debug("exception in request_csv")
            return None

    def __get_all_yahoo_ids(self, assets):
        ids = []
        for asset in assets:
            ids += [source_info.info for source_info in asset.get_source_info(self.name)]
        return '+'.join(ids)

    def update_stocks(self, assets):
        if not assets:
            return
        ids = self.__get_all_yahoo_ids(assets)
        res = self.__request_csv(ids, 'l1d1d3c1x')
        if not res:
            return
        result_reader = csv.reader(res)
        for current_asset in assets:
            len_ids = len(current_asset.get_source_info(self.name))
            for i in range(len_ids):
                row = result_reader.next()
                if len(row) > 1:
                    if row[1] == 'N/A':
                        continue
                    new_date = datetime.strptime(row[1], '%m/%d/%Y')
                    if re.match('^[0-9]{1,2}:[0-9]{2}am|pm$', row[2]):
                        hour = int(row[2].split(':')[0])
                        if 'pm' in row[2]:
                            hour += 12
                        new_date = new_date.replace(hour=hour, minute=int(row[2].split(':')[1][:-2]))
                    new_date = pytz.timezone('US/Eastern').localize(new_date)
                    new_date = new_date.astimezone(pytz.utc)
                    new_date = new_date.replace(tzinfo=None)
                    # is the quotation newer?
                    if new_date > current_asset.date:
                        try:
                            current_asset.price = float(row[0])
                        except Exception as e:
                            logger.info(e)
                            continue
                        current_asset.date = new_date
                        current_asset.change = float(row[3])
                        current_asset.exchange = row[4]
            yield current_asset

    def get_info(self, symbol):
        # name, isin, exchange, currency
        for row in csv.reader(self.__request_csv(symbol, 'nxc4')):
            if len(row) < 2 or row[1] == 'N/A':
                return None
        return row[0], 'n/a', row[1], row[2]

    def _test_api(self, symbol):
        for row in csv.reader(self.__request_csv(symbol, 'nxc4n0n1n2n3n4')):
            print row

    def update_historical_prices(self, stock, start_date, end_date):
        # we should use a more intelligent way of choosing the exchange
        # e.g. the exchange with the highest volume for this stock
        sourceInfo = stock.get_source_info(self.name)
        if len(sourceInfo) == 0:
            logger.debug("no source info for stock")
            return
        yid = sourceInfo[0].info

        # url = 'http://download.finance.yahoo.com/d/quotes.csv?s=%s&' % yid + \
        url = 'http://ichart.finance.yahoo.com/table.csv?s=%s&' % yid + \
              'a=%s&' % str(start_date.month - 1) + \
              'b=%s&' % str(start_date.day) + \
              'c=%s&' % str(start_date.year) + \
              'g=d&' + \
              'd=%s&' % str(end_date.month - 1) + \
              'e=%s&' % str(end_date.day) + \
              'f=%s&' % str(end_date.year) + \
              'ignore=.csv'
        logger.debug(url)
        csvfile = urlopen(url)
        if csvfile.info().gettype() == 'text/html':
            logger.info("no historical data found for stock: " + stock.name)
            yield None
        days = csvfile.readlines()
        for row in [day[:-2].split(',') for day in days[1:]]:
            dt = datetime.strptime(row[0], '%Y-%m-%d').date()
            # (stock, date, open, high, low, close, vol)
            yield (stock, stock.exchange, dt, float(row[1]), float(row[2]), \
                        float(row[3]), float(row[6]), int(row[5]))

    def search_without_beautifulsoup(self, searchstring):
        # does not provide isin or even lookup by isin
        url = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query=%s&callback=YAHOO.Finance.SymbolSuggest.ssCallback" % (searchstring)
        json_response = str(urlopen(url).read()).replace("YAHOO.Finance.SymbolSuggest.ssCallback(", "").replace(")", "")
        for item in json.loads(json_response)['ResultSet']['Result']:
            print item

    def search(self, searchstring):
        doc = self.__request(searchstring)
        if doc is None:
            return
        soup = BeautifulSoup(doc)
        found_items = {}
        for table in soup.find_all('table', summary="YFT_SL_TABLE_SUMMARY"):
            for body in table('tbody'):
                for row in body('tr'):
                    item = []
                    for s in row('td', text=True):
                        if s is not None:
                            s = s.get_text().strip()
                            if s != unicode(''):
                                item.append(s)
                    if len(item) == 6:
                        item = self.__to_dict(item)
                        if item is not None:
                            logger.debug("yahoo found item", item)
                            # cache all items first, because we want to store all yahoo_ids..
                            key = (item['isin'], item['currency'])
                            if key in found_items:
                                found_items[key].append(item)
                            else:
                                found_items[key] = [item]
        for items in found_items.values():
            yield (items[0], self, [item['yahoo_id'] for item in items])

    def __to_dict(self, item):
        if not item[4] in TYPES:
            return None
        res = {}
        res['name'] = unicode(item[1])
        res['yahoo_id'] = item[0]
        res['isin'] = item[2]
        res['exchange'] = item[5]
        res['type'] = TYPES[item[4]]
        for ex, cur in EXCHANGE_CURRENCY:
            if res['exchange'] in ex:
                res['currency'] = cur
                return res
        return None


if __name__ == "__main__":
    import sys
    sys.path.append("../../")
    import __builtin__
    __builtin__._ = str
    from avernus import objects
    from avernus.objects import db
    from avernus.controller import datasource_controller as dsm

    dbfile = ":memory:"
    db.set_db(dbfile)
    db.connect()

    test_asset = 'FR0010959676'

    y = DataSource()
    for res in y.search(test_asset):
        item, source, source_info = res
        dsm._item_found_callback(item, source, source_info)

    asset = objects.asset.get_asset_for_searchstring(test_asset)[0]
    for foo in dsm.update_assets([asset]):
        pass

    for asset in objects.asset.get_all_assets():
        for foo in dsm.update_historical_prices_asset(asset, threaded=False):
            for bar in foo:
                pass

    print asset.price, asset.date
    print len(asset.quotations)
