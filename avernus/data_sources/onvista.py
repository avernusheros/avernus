# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
from bs4 import BeautifulSoup
from Queue import Queue
from datetime import datetime, date
import logging
import pytz
import re
import threading
import urllib
import urllib2

logger = logging.getLogger(__name__)



QUEUE_THRESHOLD = 3
QUEUE_DIVIDEND = 10
QUEUE_MAX = 10


def to_float(s):
    return float(s.replace('.', '').replace('%', '').replace(',', '.').split('&')[0])


def to_datetime(datestring, time=None, toUTC=True):
    if time is None:
        ret_date = datetime.strptime(datestring, "%d.%m.%y")
    else:
        ret_date = datetime.strptime(datestring + time, "%d.%m.%y%H:%M:%S")
    ret_date = pytz.timezone('Europe/Berlin').localize(ret_date)
    if toUTC:
        ret_date = ret_date.astimezone(pytz.utc)
        ret_date = ret_date.replace(tzinfo=None)
    return ret_date


def to_int(s):
    s = s.replace('.', '')
    try:
        return int(s)
    except:
        return 0

opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]


class URLGetter(threading.Thread):
    def __init__(self, url):
        self.url = url
        self.result = None
        threading.Thread.__init__(self)

    def get_result(self):
        return self.result

    def run(self):
        try:
            self.result = opener.open(self.url)
        except IOError:
            print "Could not open document: %s" % self.url


class FunctionThread(threading.Thread):

    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.result = None
        threading.Thread.__init__(self)

    def get_result(self):
        return self.result

    def run(self):
        print "Executing ", self.func.__name__, self.args, self.kwargs
        self.result = self.func(*self.args, **self.kwargs)

class Paralyzer:

    def __init__(self):
        self.producerArgs = self.consumerArgs = ()

    def perform(self):
        logger.debug('Performing Tasks #' + str(self.taskSize))
        self.finished = []
        queueSize = min(QUEUE_THRESHOLD, self.taskSize)
        calcSize = self.taskSize / QUEUE_DIVIDEND
        size = max(queueSize, calcSize)
        size = min(size, QUEUE_MAX)
        logger.debug("ThreadQueue Size: " + str(size))
        self.q = Queue(size)
        prod_thread = threading.Thread(target=self.producer, args=self.producerArgs)
        cons_thread = threading.Thread(target=self.consumer, args=self.consumerArgs)
        prod_thread.start()
        cons_thread.start()
        prod_thread.join()
        logger.debug('Producer Thread joined')
        cons_thread.join()
        logger.debug('Consumer Thread joined')
        return self.finished

    def consumer(self):
        while len(self.finished) < self.taskSize:
            thread = self.q.get(True)
            thread.join()
            self.finished.append(thread.get_result())


class FileDownloadParalyzer(Paralyzer):

    def __init__(self, files):
        Paralyzer.__init__(self)
        self.files = files
        self.taskSize = len(files)

    def producer(self):
        for f in self.files:
            thread = URLGetter(f)
            thread.start()
            self.q.put(thread, True)


class KursParseParalyzer(Paralyzer):

    def __init__(self, pages, fun):
        Paralyzer.__init__(self)
        self.pages = pages
        self.func = fun
        self.taskSize = len(pages)

    def producer(self):
        for page in self.pages:
            thread = FunctionThread(self.func, page)
            thread.start()
            self.q.put(thread, True)

fondTDS = {
           'table_class':'t',
           'table':1,
           'currency':1,
           'price':11,
           'temp_date':8,
           'volume':12,
           'change':14,
           }

etfTDS = {
          'table_class':'t',
          'table':2,
          'currency':5,
          'price':12,
          'temp_date':6,
          'volume':11,
          'change':3,
          }

bondTDS = {
        'table_class':'t KURSTABELLE',
        'table':0,
          'price':1,
          'temp_date':4,
          'volume':9,
          'change':3,
          }


class DataSource():

    def __init__(self):
        self.name = 'onvista.de'
        self.exchangeBlacklist = [u'Summe:', u'Realtime-Kurse', u'Neartime-Kurse', \
                                 u'Leider stehen zu diesem Fonds keine Informationen zur Verfügung.']

    def regex_isin(self, text):
        match_object = re.search('[A-Z]{2}[A-Z0-9]{9}[0-9]', text)
        if match_object:
            return match_object.group(0)

    def search(self, searchstring):
        logger.debug("Starting search for " + searchstring)
        # http://www.onvista.de/suche.html?TARGET=kurse&SEARCH_VALUE=&ID_TOOL=FUN
        #FIXME onvista changed their asset search page. "suche2" is the old search...  
        search_url = "http://www.onvista.de/suche2.html"
        # ID_TOOL FUN only searches fonds and etfs
        page = opener.open(search_url, urllib.urlencode({"TARGET": "kurse", "SEARCH_VALUE": searchstring}))  # ,'ID_TOOL':'FUN' }))
        received_url = page.geturl()
        # single result http://www.onvista.de/etf/kurse.html?ID_INSTRUMENT=16353286&SEARCH_VALUE=DBX0AE
        # result page http://www.onvista.de/suche.html
        # now check if we got a single result or a result page
        # if we get a result page, the url doesn't change
        if received_url == search_url or "www.onvista.de/suche" in received_url:
            logger.debug("Received result page")
            # we have a result page
            soup = BeautifulSoup(page.read())
            linkTagsFonds = soup.find_all(attrs={'href' : re.compile('http://fonds\\.onvista\\.de/kurse\\.html\?ID_INSTRUMENT=\d+')})
            etfRegex = re.compile("http://www\\.onvista\\.de/etf/.+?")  # re.compile('http://etf\\.onvista\\.de/kurse\\.html\?ID_INSTRUMENT=\d+')
            linkTagsETF = soup.find_all(attrs={'href' : etfRegex})
            linkTagsBond = soup.find_all(attrs={'href' : re.compile('http://anleihen\\.onvista\\.de/kurse\\.html\?ID_INSTRUMENT=\d+')})
            filePara = FileDownloadParalyzer([tag['href'] for tag in linkTagsFonds])
            pages = filePara.perform()
            for kursPage in pages:
                logger.debug("Parsing fonds result page")
                for item in self._parse_kurse_html(kursPage):
                    yield (item, self, None)
            logger.debug("Finished Fonds")

            # enhance the /kurse suffix to the links
            etflinks = [tag['href'] for tag in linkTagsETF]
            etflinks = [link + "/kurse" for link in etflinks]
            filePara = FileDownloadParalyzer(etflinks)
            pages = filePara.perform()
            for kursPage in pages:
                logger.debug("Parsing ETF result page")
                for item in self._parse_kurse_html(kursPage, tdInd=etfTDS, stockType='etf'):
                    yield (item, self, None)

            bondlinks = [tag['href'] for tag in linkTagsBond]
            bondlinks = [link + "/kurse" for link in bondlinks]
            filePara = FileDownloadParalyzer(bondlinks)
            pages = filePara.perform()
            for kursPage in pages:
                logger.debug("Parsing bond result page")
                for item in self._parse_kurse_html(kursPage, tdInd=bondTDS, stockType='bond'):
                    yield (item, self, None)
        else:
            logger.debug("Received a Single result page")
            # we have a single page
            # determine whether its an etf or a fonds
            html = page.read()
            if "etf" in received_url:
                for item in self._parse_kurse_html(html, tdInd=etfTDS, stockType='etf'):
                    yield (item, self, None)
            elif "anleihen" in received_url:
                for item in self._parse_kurse_html(html, tdInd=bondTDS, stockType='bond'):
                    yield (item, self, None)
            elif "fond" in received_url:
                for item in self._parse_kurse_html(html):
                    yield (item, self, None)
            else:
                logger.error("unknown %s", received_url)
        logger.debug("Finished Searching " + searchstring)

    def _parse_kurse_html(self, kursPage, tdInd=fondTDS, stockType='fund'):
        try:
            base = BeautifulSoup(kursPage).find('div', 'INHALT')
            regex404 = re.compile("http://www\\.onvista\\.de/404\\.html")
            if regex404.search(str(base)):
                logger.info("Encountered 404 while Searching")
                return
            name = unicode(base.h1.contents[0])
            if stockType == 'bond':
                temp = base.find_all('tr', 'hgrau2')[0].findAll('td').get_text()
                isin = temp[3]
                currency = temp[9]
            else:
                isin = base.find_all('tr', 'hgrau2')[1].find_all('td')[1].get_text()

                # getting the year
                # FIXME
                # try:
                #    yearTable = base.find('div','tt_hl').findNextSibling('table','weiss abst').find('tr','hgrau2')
                # except:
                #    print "Error getting year in ", kursPage
                #    yearTable = None
                # if yearTable:
                #    print yearTable.td
                #    year = yearTable.td.string.split(".")[2]
                # else:
                #    #fallback to the hardcoded current year
                year = unicode(str(date.today().year)[2:])
            isin = self.regex_isin(isin)
            for row in base.findAll('div', tdInd['table_class'])[tdInd['table']].find('table'):
                tds = row.findAll('td')
                if len(tds) > 3:
                    if not tds[0].contents[0] in self.exchangeBlacklist:
                        exchange = unicode(tds[0].find(text=True))
                        price = to_float(tds[tdInd['price']].contents[0])
                        if stockType == 'bond':
                            temp_date = to_datetime(tds[tdInd['temp_date']].contents[0],
                                                tds[tdInd['temp_date'] + 1].contents[0])
                        else:
                            currency = unicode(tds[tdInd['currency']].contents[0])
                            temp_date = to_datetime(tds[tdInd['temp_date']].contents[0] + year,
                                                tds[tdInd['temp_date'] + 1].contents[0])
                        volume = to_int(tds[tdInd['volume']].contents[0])
                        change = tds[tdInd['change']]
                        if change.span:
                            change = change.span
                        change = to_float(change.contents[0])
                        erg = {'name':name, 'isin':isin, 'exchange':exchange, 'price':price,
                          'date':temp_date, 'currency':currency, 'volume':volume,
                          'type':stockType, 'change':change}
                        # print [(k,type(v)) for k,v in erg.items()]
                        yield erg
        except:
            logger.error("parsing errror in onvista.py")
            return

    def update_stocks(self, assets):
        for asset in assets:
            try:
                if asset.type == "fund":
                    f = opener.open("http://www.onvista.de/fonds/kurse.html", urllib.urlencode({"ISIN": asset.isin}))
                    generator = self._parse_kurse_html(f)
                elif asset.type == "etf":
                    f = opener.open("http://www.onvista.de/etf/kurse.html", urllib.urlencode({"ISIN": asset.isin}))
                    generator = self._parse_kurse_html(f, tdInd=etfTDS, stockType='etf')
                elif asset.type == "bond":
                    f = opener.open("http://www.onvista.de/anleihen/kurse.html", urllib.urlencode({"ISIN": asset.isin}))
                    generator = self._parse_kurse_html(f, tdInd=bondTDS, stockType='bond')
                else:
                    print "Unknown stock type in onvistaplugin.update_stocks: ", type(asset)
                    return
            except:
                logger.info("can not download quotations")
                return
            for item in generator:
                # found newer price?
                if asset.date < item['date']:
                    asset.exchange = item['exchange']
                    asset.price = item['price']
                    asset.date = item['date']
                    asset.change = item['change']
                    asset.volume = item['volume']
                    yield asset

    def update_historical_prices(self, asset, start_date, end_date):
        url = ''
        if asset.type == "fund":
            url = 'http://www.onvista.de/fonds/kurshistorie.html'
        elif asset.type == "etf":
            url = 'http://www.onvista.de/etf/kurshistorie.html'
        elif asset.type == "bond":
            url = 'http://anleihen.onvista.de/kurshistorie.html'
        else:
            logger.error("Uknown stock type in onvistaplugin.search_kurse")
        fileobj = opener.open(url, urllib.urlencode({'ISIN':asset.isin, 'RANGE':'60M'}))
        soup = BeautifulSoup(fileobj)
        if asset.type == "bond":
            lines = soup.find_all('tr', {'class':'hr'})
        else:
            lines = soup.find_all('tr', {'align':'right'})
        for line in lines:
            tds = line.find_all('td')
            try:
                day = to_datetime(tds[0].get_text()).date()
            except:
                continue
            # terminate if the start date is reached
            if day < start_date:
                return

            if asset.type == "bond":
                yield (asset, 'KAG',
                       day,
                       to_float(tds[1].get_text().replace('&nbsp;', '')),
                       to_float(tds[2].get_text().replace('&nbsp;', '')),
                       to_float(tds[3].get_text().replace('&nbsp;', '')),
                       to_float(tds[4].get_text().replace('&nbsp;', '')),
                       0)
            else:
                kurs = to_float(tds[1].get_text().replace('&nbsp;', ''))
                yield (asset, 'KAG', day, kurs, kurs, kurs, kurs, 0)


if __name__ == "__main__":

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.setLevel(logging.DEBUG)
    consolehandler = logging.StreamHandler()
    consolehandler.setFormatter(formatter)
    logger.addHandler(consolehandler)

    class Stock():
        def __init__(self, isin, ex, type):
            self.isin = isin
            self.type = type
            self.exchange = ex
            self.currency = 'EUR'
            self.date = datetime(2008, 5, 1)

    def test_update(s):
        for item in plugin.update_stocks([s]):
            pass
        print s.price, s.change, s.date
        # print s2.price, s2.change, s2.date

    def test_search():
        for res in plugin.search('DE0008474248'):
            print res

    def test_historicals():
        print "los"
        for quot in plugin.update_historical_prices(s2, date(2010, 1, 1), date.today()):
            print quot
        print "fertsch"

    def test_parse_kurse():
        page = opener.open('http://fonds.onvista.de/kurse.html?ID_INSTRUMENT=83602')
        for item in plugin._parse_kurse_html(page, tdInd=fondTDS, stockType='fund'):
            print item
        print "---------------------------------"
        page = opener.open('http://www.onvista.de/etf/kurse.html?ISIN=LU0203243414')
        for item in plugin._parse_kurse_html(page, tdInd=etfTDS, stockType='etf'):
            print item

    plugin = DataSource()
    s1 = Stock('DE000A0RFEE5', 'foo', "fund")
    s2 = Stock('LU0103598305', 'foo', "fund")
    test_historicals()

