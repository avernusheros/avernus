# -*- coding: utf-8 -*-
from BeautifulSoup import BeautifulSoup, NavigableString
from datetime import datetime, date
import pytz
from dateutil.relativedelta import relativedelta
import threading, re
from Queue import Queue
import urllib
import urllib2
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



class Onvista():
    configurable = False

    def __init__(self):
        self.name = 'onvista.de'
        self.exchangeBlacklist = ['Summe:','Realtime-Kurse','Neartime-Kurse',\
                                 'Leider stehen zu diesem Fonds keine Informationen zur Verfügung.']

    def search(self, searchstring):
        page = opener.open("http://www.onvista.de/suche.html", urllib.urlencode({"TARGET": "kurse", "SEARCH_VALUE": searchstring,'ID_TOOL':'FUN' }))
        soup = BeautifulSoup(page.read())
        linkTagsFonds = soup.findAll(attrs={'href' : re.compile('http://fonds\\.onvista\\.de/kurse\\.html\?ID_INSTRUMENT=\d+')})
        linkTagsETF = soup.findAll(attrs={'href' : re.compile('http://etf\\.onvista\\.de/kurse\\.html\?ID_INSTRUMENT=\d+')})
        filePara = FileDownloadParalyzer([tag['href'] for tag in linkTagsFonds])
        pages = filePara.perform()
        for kursPage in pages:
            for item in self._parse_kurse_html_fonds(kursPage):
                yield (item, self)
        #print "finished fonds"
        filePara = FileDownloadParalyzer([tag['href'] for tag in linkTagsETF])
        pages = filePara.perform()
        #print "got Pages: ", pages
        for kursPage in pages:
            for item in self._parse_kurse_html_etf(kursPage):
                yield (item, self)
        #print "fertig ganz"

    def _parse_kurse_html_fonds(self, kursPage):
        base = BeautifulSoup(kursPage).find('div', 'content')
        try:
            yearTable = base.find('div','tt_hl').findNextSibling('table','weiss abst').find('tr','hgrau2')
        except:
            print "Error getting year in ", kursPage
            yearTable = None
        # is there any entry?
        if yearTable:
            year = yearTable.td.string.split(".")[2]
        else:
            #fallback to the hardcoded current year
            year = date.today().year
        name = str(base.h1.contents[0])
        isin = base.findAll('tr','hgrau2')[1].findAll('td')[1].contents[0].replace('&nbsp;','')
        #print isin
        for row in base.findAll('div','t')[1].find('table'):
            tds = row.findAll('td')
            if len(tds)>3:
                exchangeTag = tds[0]
                if not exchangeTag.contents[0] in self.exchangeBlacklist:
                    exchange = ""
                    #print type(exchangeTag.contents[0])
                    if not isinstance(exchangeTag.contents[0], NavigableString):
                        exchange = exchangeTag.a.contents[0]
                    else:
                        exchange = exchangeTag.contents[0]
                    currency = tds[1].contents[0]
                    price = to_float(tds[11].contents[0])
                    #sellPrice = tds[6].contents[0]
                    temp_date = to_datetime(tds[8].contents[0]+year, tds[9].contents[0])
                    volume = to_int(tds[12].contents[0])
                    change = tds[14]
                    if change.span:
                        change = change.span
                    change = to_float(change.contents[0])
                    yield {'name':name,'isin':isin,'exchange':exchange,'price':price,
                      'date':temp_date,'currency':currency,'volume':volume,
                      'type':stocks.FUND,'change':change}

    def _parse_kurse_html_etf(self, kursPage):
        base = BeautifulSoup(kursPage).find('div', 'content')
        name = str(base.h1.contents[0])
        try:
            yearTable = base.find('div','tt_hl').findNextSibling('table','weiss abst').find('tr','hgrau2')
        except:
            print "Error getting year in ", kursPage
            yearTable = None
        # is there any entry?
        if yearTable:
            year = yearTable.td.string.split(".")[2]
        else:
            #fallback to the hardcoded current year
            year = date.today().year
        year = year.split(".")[2]
        isin = base.findAll('tr','hgrau2')[1].findAll('td')[1].contents[0].replace('&nbsp;','')
        #print base.findAll('div','t')[2]
        for row in base.findAll('div','t')[2].find('table'):
            tds = row.findAll('td')
            if len(tds)>3:
                exchangeTag = tds[0]
                if not exchangeTag.contents[0] in self.exchangeBlacklist:
                    exchange = ""
                    if not isinstance(exchangeTag.contents[0], NavigableString):
                        exchange = exchangeTag.a.contents[0]
                    else:
                        exchange = exchangeTag.contents[0]
                    #print exchange
                    currency = tds[5].contents[0]
                    price = to_float(tds[12].contents[0])
                    temp_date = to_datetime(tds[6].contents[0]+year, tds[7].contents[0])
                    volume = to_int(tds[11].contents[0])
                    change = tds[3]
                    if change.span:
                        change = change.span
                    change = to_float(change.contents[0])
                    yield {'name':name,'isin':isin,'exchange':exchange,'price':price,
                      'date':temp_date,'currency':currency,'volume':volume,
                      'type':stocks.ETF,'change':change}

    def update_stocks(self, stocks):
        for stock in stocks:
            if stock.type == stocks.FUND:
                file = opener.open("http://fonds.onvista.de/kurse.html", urllib.urlencode({"ISIN": stock.isin}))
                generator = self._parse_kurse_html_fonds(file)
            elif stock.type == stocks.ETF:
                file = opener.open("http://etf.onvista.de/kurse.html", urllib.urlencode({"ISIN": stock.isin}))
                generator = self._parse_kurse_html_etf(file)
            else:
                print "Unknown stock type in onvistaplugin.update_stocks"
            for item in generator:
                if item['exchange'] == stock.exchange and \
                        item['currency'] == stock.currency:
                    stock.price = item['price']
                    stock.date = item['date']
                    stock.change = item['change']
                    stock.volume = item['volume']
                    stock.updated = True
                    break

    def update_historical_prices(self, stock, start_date, end_date):
        delta = relativedelta(start_date, end_date)
        #print delta
        months = min(60,abs(delta.years)*12 + abs(delta.months))
        url = ''
        width = ''
        if stock.type == stocks.FUND:
            url = 'http://fonds.onvista.de/kurshistorie.html'
            width = '100%'
        elif stock.type == stocks.ETF:
            url = 'http://etf.onvista.de/kurshistorie.html'
            width = '640'
        else:
            Log.error("Uknown stock type in onvistaplugin.search_kurse")
        #url += "?ISIN="+str(stock.isin) + "&RANGE=" + str(months) +"M"
        #get = FileGetter(url)
        #get.start()
        #get.join()
        #file = get.get_result()
        file = opener.open(url,urllib.urlencode({'ISIN':stock.isin, 'RANGE':str(months)+'M'}))
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
            yield (stock,day,kurs,kurs,kurs,kurs,0)



if __name__ == "__main__":

    class Exchange():
        name = 'KAG-Kurs'

    class Stock():
        def __init__(self, isin, ex, type):
            self.isin = isin
            self.type = type
            self.exchange = ex
            self.currency = 'EUR'

    ex = Exchange()
    s1 = Stock('DE0008474248', ex, stocks.FUND)
    s2 = Stock('LU0382362290', ex, stocks.ETF)

    def test_update():

        plugin.update_stocks([s1, s2])
        print s1.price, s1.change, s1.date
        print s2.price, s2.change, s2.date

    def test_search():
        for res in  plugin.search('dws performance'):
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
        for item in plugin._parse_kurse_html_fonds(page):
            print item
        print "---------------------------------"
        page = opener.open('http://etf.onvista.de/kurse.html?ID_INSTRUMENT=21384252')
        for item in plugin._parse_kurse_html_etf(page):
            print item

    plugin = Onvista()
    ex = Exchange()
    s1 = Stock('LU0136412771', ex, stocks.FUND)
    s2 = Stock('LU0103598305', ex, stocks.FUND)
    s3 = Stock('LU0382362290', ex, stocks.ETF)
    print test_search()
    #print plugin.search_kurse(s1)
    #print plugin.search_kurse(s3)
    #test_parse_kurse()
    #test_update()
    #test_historicals()
