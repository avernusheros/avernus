# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
from BeautifulSoup import BeautifulSoup, NavigableString
from datetime import datetime, date
import pytz
from dateutil.relativedelta import relativedelta
import threading, re
from Queue import Queue
import urllib
import urllib2

if __name__ == "__main__":
    import sys
    sys.path.append("../../")

from stocktracker.objects import stock
from stocktracker.logger import Log

QUEUE_THRESHOLD = 3
QUEUE_DIVIDEND = 10
QUEUE_MAX = 10


def to_float(s):
    return float(s.replace('.','').replace(',','.'))

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
        Log.debug('Performing Tasks #' + str(self.taskSize))
        self.finished = []
        queueSize = min(QUEUE_THRESHOLD, self.taskSize)
        calcSize = self.taskSize/QUEUE_DIVIDEND
        size = max(queueSize,calcSize)
        size = min(size, QUEUE_MAX)
        Log.debug("ThreadQueue Size: " + str(size))
        self.q = Queue(size)
        prod_thread = threading.Thread(target=self.producer, args=self.producerArgs)
        cons_thread = threading.Thread(target=self.consumer, args=self.consumerArgs)
        prod_thread.start()
        cons_thread.start()
        prod_thread.join()
        Log.debug('Producer Thread joined')
        cons_thread.join()
        Log.debug('Consumer Thread joined')
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
           'table':1,
           'currency':1,
           'price':11,
           'temp_date':8,
           'volume':12,
           'change':14,
           }

etfTDS = {
          'table':2,
          'currency':5,
          'price':12,
          'temp_date':6,
          'volume':11,
          'change':3,
          }

class Onvista():

    def __init__(self):
        self.name = 'onvista.de'
        self.exchangeBlacklist = ['Summe:','Realtime-Kurse','Neartime-Kurse',\
                                 'Leider stehen zu diesem Fonds keine Informationen zur Verfügung.']

    def search(self, searchstring):
        Log.debug("Starting search for " + searchstring)
        #http://www.onvista.de/suche.html?TARGET=kurse&SEARCH_VALUE=&ID_TOOL=FUN
        search_url = "http://www.onvista.de/suche.html"
        page = opener.open(search_url, urllib.urlencode({"TARGET": "kurse", "SEARCH_VALUE": searchstring,'ID_TOOL':'FUN' }))
        received_url = page.geturl()
        #print "received url ", received_url
        # single result http://www.onvista.de/etf/kurse.html?ID_INSTRUMENT=16353286&SEARCH_VALUE=DBX0AE
        # result page http://www.onvista.de/suche.html
        # now check if we got a single result or a result page
        # if we get a result page, the url doesn't change
        if received_url == search_url or received_url.startswith(search_url):
            Log.debug("Received result page")
            # we have a result page
            soup = BeautifulSoup(page.read())
            #print soup
            linkTagsFonds = soup.findAll(attrs={'href' : re.compile('http://fonds\\.onvista\\.de/kurse\\.html\?ID_INSTRUMENT=\d+')})
            etfRegex = re.compile("http://www\\.onvista\\.de/etf/.+?") #re.compile('http://etf\\.onvista\\.de/kurse\\.html\?ID_INSTRUMENT=\d+')
            linkTagsETF = soup.findAll(attrs={'href' : etfRegex})
            filePara = FileDownloadParalyzer([tag['href'] for tag in linkTagsFonds])
            pages = filePara.perform()
            for kursPage in pages:
                Log.debug("Parsing fonds result page")
                for item in self._parse_kurse_html(kursPage):
                    yield (item, self)
            Log.debug("Finished Fonds")
            # enhance the /kurse suffix to the links
            etflinks = [tag['href'] for tag in linkTagsETF]
            etflinks = [link + "/kurse" for link in etflinks]
            filePara = FileDownloadParalyzer(etflinks)
            pages = filePara.perform()
            for kursPage in pages:
                Log.debug("Parsing ETF result page")
                for item in self._parse_kurse_html(kursPage, tdInd=etfTDS, stockType=stock.ETF):
                    yield (item, self)
        else:
            Log.debug("Received a Single result page")
            # we have a single page
            # determine whether its an etf or a fonds
            html = page.read()
            if received_url.find("etf")>-1:
                # etf
                print "found ETF-onepage"
                for item in self._parse_kurse_html(html, tdInd=etfTDS, stockType=stock.ETF):
                    print "Yield ", item
                    yield (item, self)
            else:
                # aktive fonds
                print "found aktiveFonds-onepage"
                for item in self._parse_kurse_html(html):
                    yield (item, self)
        Log.debug("Finished Searching " + searchstring)
        
    def _parse_kurse_html(self, kursPage, tdInd=fondTDS, stockType = stock.FUND):
        base = BeautifulSoup(kursPage).find('div', 'content')
        #print base
        regex404 = re.compile("http://www\\.onvista\\.de/404\\.html")
        if regex404.search(str(base)):
            Log.info("Encountered 404 while Searching")
            print "Ditching 404"
            return
        name = unicode(base.h1.contents[0])
        isin = str(base.findAll('tr','hgrau2')[1].findAll('td')[1].contents[0].replace('&nbsp;',''))
        try:
            yearTable = base.find('div','tt_hl').findNextSibling('table','weiss abst').find('tr','hgrau2')
        except:
            print "Error getting year in ", kursPage
            yearTable = None
        if yearTable:
            year = yearTable.td.string.split(".")[2]
        else:
            #fallback to the hardcoded current year
            year = unicode(str(date.today().year)[2:])
        for row in base.findAll('div','t')[tdInd['table']].find('table'):
            tds = row.findAll('td')
            if len(tds)>3:
                exchangeTag = tds[0]
                if not exchangeTag.contents[0] in self.exchangeBlacklist:
                    exchange = ""
                    if not isinstance(exchangeTag.contents[0], NavigableString):
                        exchange = exchangeTag.a.contents[0]
                    else:
                        exchange = exchangeTag.contents[0]
                    exchange = unicode(exchange)
                    currency = unicode(tds[tdInd['currency']].contents[0])
                    price = to_float(tds[tdInd['price']].contents[0])
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
                file = opener.open("http://fonds.onvista.de/kurse.html", urllib.urlencode({"ISIN": st.isin}))
                generator = self._parse_kurse_html(file)
            elif st.type == stock.ETF:
                file = opener.open("http://www.onvista.de/etf/kurse.html", urllib.urlencode({"ISIN": st.isin}))
                generator = self._parse_kurse_html(file, tdInd=etfTDS, stockType=stock.ETF)
            else:
                print "Unknown stock type in onvistaplugin.update_stocks"
            for item in generator:
                if st.date < item['date']: #found newer price
                    st.exchange = item['exchange']
                    st.price = item['price']
                    st.date = item['date']
                    st.change = item['change']
                    st.volume = item['volume']
                    st.updated = True
                    break

    def update_historical_prices(self, st, start_date, end_date):
        delta = relativedelta(start_date, end_date)
        #print delta
        months = min(60,abs(delta.years)*12 + abs(delta.months))
        url = ''
        width = ''
        if st.type == stock.FUND:
            url = 'http://fonds.onvista.de/kurshistorie.html'
            width = '100%'
        elif st.type == stock.ETF:
            url = 'http://etf.onvista.de/kurshistorie.html'
            width = '640'
        else:
            Log.error("Uknown stock type in onvistaplugin.search_kurse")
        #url += "?ISIN="+str(stock.isin) + "&RANGE=" + str(months) +"M"
        #get = FileGetter(url)
        #get.start()
        #get.join()
        #file = get.get_result()
        file = opener.open(url,urllib.urlencode({'ISIN':st.isin, 'RANGE':str(months)+'M'}))
        soup = BeautifulSoup(file)
        #print soup
        tables = soup.html.body.findAll('table',{'width':width})
        table = tables[2]
        #for t in tables:
        #    print t
        lines = table.findAll('tr',{'align':'right'})
        for line in lines:
            tds = line.findAll('td')
            day = to_datetime(tds[0].contents[0].replace('&nbsp;','')).date()
            kurs = to_float(tds[1].contents[0].replace('&nbsp;',''))
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

    def test_update():

        plugin.update_stocks([s1])
        print s1.price, s1.change, s1.date
        #print s2.price, s2.change, s2.date

    def test_search():
        for res in  plugin.search('A0F5G9'):
            print res
        for res in plugin.search('DBX0AE'):
            print res

    def test_historicals():
        print "los"
        for quot in plugin.update_historical_prices(s1, date(1920,1,1), date.today()):
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
    s3 = Stock('LU0382362290', ex, stock.ETF)
    test_search()
    #print plugin.search_kurse(s1)
    #print plugin.search_kurse(s3)
    #test_parse_kurse()
    #test_update()
    #test_historicals()
