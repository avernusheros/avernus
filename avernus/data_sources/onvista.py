# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
from BeautifulSoup import BeautifulSoup
from datetime import datetime, date
import pytz
import threading
import re
from Queue import Queue
import urllib
import urllib2

import logging
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    import sys
    sys.path.append("../../")

from avernus.objects import stock

QUEUE_THRESHOLD = 3
QUEUE_DIVIDEND = 10
QUEUE_MAX = 10

def to_float(s):
    return float(s.replace('.','').replace('%','').replace(',','.').split('&')[0])

def to_datetime(datestring, time='', toUTC=True):
    if time == '':
        ret_date = datetime.strptime(datestring+time, "%d.%m.%y")
    else:
        ret_date = datetime.strptime(datestring+time, "%d.%m.%y%H:%M:%S")
    ret_date = pytz.timezone('Europe/Berlin').localize(ret_date)
    if toUTC:
        ret_date = ret_date.astimezone(pytz.utc)
        ret_date = ret_date.replace(tzinfo = None)
    #print ret_date
    return ret_date


def to_int(s):
    s = s.replace('.','')
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
            print "Downloaded ", self.url
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
        calcSize = self.taskSize/QUEUE_DIVIDEND
        size = max(queueSize,calcSize)
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
        for file in self.files:
            thread = URLGetter(file)
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
            self.q.put(thread,True)

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


class Onvista():

    def __init__(self):
        self.name = 'onvista.de'
        self.exchangeBlacklist = [u'Summe:',u'Realtime-Kurse',u'Neartime-Kurse',\
                                 u'Leider stehen zu diesem Fonds keine Informationen zur Verfügung.']

    def search(self, searchstring):
        logger.debug("Starting search for " + searchstring)
        #http://www.onvista.de/suche.html?TARGET=kurse&SEARCH_VALUE=&ID_TOOL=FUN
        search_url = "http://www.onvista.de/suche.html"
        #ID_TOOL FUN only searches fonds and etfs
        page = opener.open(search_url, urllib.urlencode({"TARGET": "kurse", "SEARCH_VALUE": searchstring}))#,'ID_TOOL':'FUN' }))
        received_url = page.geturl()
        #print "received url ", received_url
        # single result http://www.onvista.de/etf/kurse.html?ID_INSTRUMENT=16353286&SEARCH_VALUE=DBX0AE
        # result page http://www.onvista.de/suche.html
        # now check if we got a single result or a result page
        # if we get a result page, the url doesn't change
        if received_url == search_url or received_url.startswith(search_url):
            logger.debug("Received result page")
            # we have a result page
            soup = BeautifulSoup(page.read())
            #print soup
            linkTagsFonds = soup.findAll(attrs={'href' : re.compile('http://fonds\\.onvista\\.de/kurse\\.html\?ID_INSTRUMENT=\d+')})
            etfRegex = re.compile("http://www\\.onvista\\.de/etf/.+?") #re.compile('http://etf\\.onvista\\.de/kurse\\.html\?ID_INSTRUMENT=\d+')
            linkTagsETF = soup.findAll(attrs={'href' : etfRegex})
            linkTagsBond = soup.findAll(attrs={'href' : re.compile('http://anleihen\\.onvista\\.de/kurse\\.html\?ID_INSTRUMENT=\d+')})
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
                for item in self._parse_kurse_html(kursPage, tdInd=etfTDS, stockType=stock.ETF):
                    yield (item, self, None)

            bondlinks = [tag['href'] for tag in linkTagsBond]
            bondlinks = [link + "/kurse" for link in bondlinks]
            filePara = FileDownloadParalyzer(bondlinks)
            pages = filePara.perform()
            for kursPage in pages:
                logger.debug("Parsing bond result page")
                for item in self._parse_kurse_html(kursPage, tdInd=bondTDS, stockType=stock.BOND):
                    yield (item, self, None)
        else:
            logger.debug("Received a Single result page")
            # we have a single page
            # determine whether its an etf or a fonds
            html = page.read()
            if "etf" in received_url:
                # etf
                #print "found ETF-onepage"
                for item in self._parse_kurse_html(html, tdInd=etfTDS, stockType=stock.ETF):
                    #print "Yield ", item
                    yield (item, self, None)
            elif "anleihen" in received_url:
                #bond
                for item in self._parse_kurse_html(html, tdInd=bondTDS, stockType=stock.BOND):
                    yield (item, self, None)
            elif "fond" in received_url:
                # aktive fonds
                for item in self._parse_kurse_html(html):
                    yield (item, self, None)
        logger.debug("Finished Searching " + searchstring)

    def _parse_kurse_html(self, kursPage, tdInd=fondTDS, stockType = stock.FUND):
        base = BeautifulSoup(kursPage).find('div', 'INHALT')
        regex404 = re.compile("http://www\\.onvista\\.de/404\\.html")
        if regex404.search(str(base)):
            logger.info("Encountered 404 while Searching")
            return
        name = unicode(base.h1.contents[0])
        if stockType == stock.BOND:
            temp = base.findAll('tr','hgrau2')[0].findAll('td', text=True)
            isin = temp[3]
            currency = temp[9]
        else:
            isin = str(base.findAll('tr','hgrau2')[1].findAll('td', text=True)[1])

            #getting the year
            #FIXME
            #try:
            #    yearTable = base.find('div','tt_hl').findNextSibling('table','weiss abst').find('tr','hgrau2')
            #except:
            #    print "Error getting year in ", kursPage
            #    yearTable = None
            #if yearTable:
            #    print yearTable.td
            #    year = yearTable.td.string.split(".")[2]
            #else:
            #    #fallback to the hardcoded current year
            year = unicode(str(date.today().year)[2:])
        isin = isin.replace('&nbsp;', '')
        for row in base.findAll('div',tdInd['table_class'])[tdInd['table']].find('table'):
            tds = row.findAll('td')
            if len(tds)>3:
                if not tds[0].contents[0] in self.exchangeBlacklist:
                    exchange = unicode(tds[0].find(text=True))
                    price = to_float(tds[tdInd['price']].contents[0])
                    if stockType == stock.BOND:
                        temp_date = to_datetime(tds[tdInd['temp_date']].contents[0],
                                            tds[tdInd['temp_date']+1].contents[0])
                    else:
                        currency = unicode(tds[tdInd['currency']].contents[0])
                        temp_date = to_datetime(tds[tdInd['temp_date']].contents[0]+year,
                                            tds[tdInd['temp_date']+1].contents[0])
                    volume = to_int(tds[tdInd['volume']].contents[0])
                    change = tds[tdInd['change']]
                    if change.span:
                        change = change.span
                    change = to_float(change.contents[0])
                    erg = {'name':name,'isin':isin,'exchange':exchange,'price':price,
                      'date':temp_date,'currency':currency,'volume':volume,
                      'type':stockType,'change':change}
                    #print [(k,type(v)) for k,v in erg.items()]
                    yield erg

    def update_stocks(self, sts):
        for st in sts:
            if st.type == stock.FUND:
                file = opener.open("http://www.onvista.de/fonds/kurse.html", urllib.urlencode({"ISIN": st.isin}))
                generator = self._parse_kurse_html(file)
            elif st.type == stock.ETF:
                file = opener.open("http://www.onvista.de/etf/kurse.html", urllib.urlencode({"ISIN": st.isin}))
                generator = self._parse_kurse_html(file, tdInd=etfTDS, stockType=stock.ETF)
            elif st.type == stock.BOND:
                file = opener.open("http://www.onvista.de/anleihen/kurse.html", urllib.urlencode({"ISIN": st.isin}))
                generator = self._parse_kurse_html(file, tdInd=bondTDS, stockType=stock.BOND)
            else:
                print "Unknown stock type in onvistaplugin.update_stocks: ", st.type
                generator = []
            for item in generator:
                if st.date < item['date']: #found newer price
                    st.exchange = item['exchange']
                    st.price = item['price']
                    st.date = item['date']
                    st.change = item['change']
                    st.volume = item['volume']
            yield 1

    def update_historical_prices(self, st, start_date, end_date):
        url = ''
        if st.type == stock.FUND:
            url = 'http://www.onvista.de/fonds/kurshistorie.html'
        elif st.type == stock.ETF:
            url = 'http://www.onvista.de/etf/kurshistorie.html'
        elif st.type == stock.BOND:
            url = 'http://anleihen.onvista.de/kurshistorie.html'
        else:
            logger.error("Uknown stock type in onvistaplugin.search_kurse")
        file = opener.open(url,urllib.urlencode({'ISIN':st.isin, 'RANGE':'60M'}))
        soup = BeautifulSoup(file)
        if st.type==stock.BOND:
            lines = soup.findAll('tr',{'class':'hr'})
        else:
            lines = soup.findAll('tr',{'align':'right'})
        for line in lines:
            tds = line.findAll('td', text=True)
            day = to_datetime(tds[0].replace('&nbsp;', '')).date()

            if st.type == stock.BOND:
                yield (st,'KAG',
                       day,
                       to_float(tds[1].replace('&nbsp;', '')),
                       to_float(tds[2].replace('&nbsp;', '')),
                       to_float(tds[3].replace('&nbsp;', '')),
                       to_float(tds[4].replace('&nbsp;', '')),
                       0)
            else:
                kurs = to_float(tds[1].replace('&nbsp;', ''))
                yield (st,'KAG',day,kurs,kurs,kurs,kurs,0)


if __name__ == "__main__":

    class Exchange():
        name = 'KAG-Kurs'

    class Stock():
        def __init__(self, isin, ex, type):
            self.isin = isin
            self.type = type
            self.exchange = ex
            self.currency = 'EUR'
            self.date = datetime(2008,5,1)

    ex = Exchange()
    s1 = Stock('DE0008474248', ex, stock.FUND)
    s2 = Stock('LU0382362290', ex, stock.ETF)

    def test_update(s):

        plugin.update_stocks([s])
        print s.price, s.change, s.date
        #print s2.price, s2.change, s2.date

    def test_search():
        for res in plugin.search('DE0008474248'):
            print res

    def test_historicals():
        print "los"
        for quot in plugin.update_historical_prices(s3, date(1920,1,1), date.today()):
            print quot
        for quot in plugin.update_historical_prices(s2, date(1920,1,1), date.today()):
            print quot
        print "fertsch"


    def test_parse_kurse():
        page = opener.open('http://fonds.onvista.de/kurse.html?ID_INSTRUMENT=83602')
        for item in plugin._parse_kurse_html(page, tdInd=fondTDS, stockType = stock.FUND):
            print item
        print "---------------------------------"
        page = opener.open('http://www.onvista.de/etf/kurse.html?ISIN=LU0203243414')
        for item in plugin._parse_kurse_html(page, tdInd=etfTDS, stockType = stock.ETF):
            print item


    plugin = Onvista()
    ex = Exchange()
    s1 = Stock('DE000A0F5G98', ex, stock.FUND)
    s2 = Stock('LU0103598305', ex, stock.FUND)
    s3 = Stock('LU0103598305', ex, stock.FUND)
    test_search()
    #print plugin.search_kurse(s1)
    #print plugin.search_kurse(s3)
    #test_parse_kurse()
    test_update(s3)
    #test_historicals()
