# -*- coding: utf-8 -*-
from BeautifulSoup import BeautifulSoup, NavigableString
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import threading, re
from Queue import Queue
import urllib
import urllib2

QUEUE_THRESHOLD = 3
QUEUE_DIVIDEND = 10
QUEUE_MAX = 10

TYPE_FUND = 0
TYPE_ETF  = 2

def to_float(s):
    return float(s.replace('.','').replace(',','.'))

def to_datetime(date, time=''):
    if time == '':
        return datetime.strptime(date+time, "%d.%m.%y")
    return datetime.strptime(date+time, "%d.%m.%y%H:%M:%S")


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
    
    def __init__(self, logger):
        self.logger = logger
        self.producerArgs = self.consumerArgs = ()
        
    def perform(self):
        self.logger.debug('Performing Tasks #' + str(self.taskSize))
        self.finished = []
        queueSize = min(QUEUE_THRESHOLD, self.taskSize)
        calcSize = self.taskSize/QUEUE_DIVIDEND
        size = max(queueSize,calcSize)
        size = min(size, QUEUE_MAX)
        self.logger.debug("ThreadQueue Size: " + str(size))
        self.q = Queue(size)
        prod_thread = threading.Thread(target=self.producer, args=self.producerArgs)
        cons_thread = threading.Thread(target=self.consumer, args=self.consumerArgs)
        prod_thread.start()
        cons_thread.start()
        prod_thread.join()
        self.logger.debug('Producer Thread joined')
        cons_thread.join()
        self.logger.debug('Consumer Thread joined')
        return self.finished
    
    def consumer(self):
        while len(self.finished) < self.taskSize:
            thread = self.q.get(True)
            thread.join()
            self.finished.append(thread.get_result())
        

class FileDownloadParalyzer(Paralyzer):
    
    def __init__(self, files, logger):
        Paralyzer.__init__(self, logger)
        self.files = files
        self.taskSize = len(files)
        
    def producer(self):
        for file in self.files:
            thread = URLGetter(file)
            thread.start()
            self.q.put(thread, True)
            
    
            
class KursParseParalyzer(Paralyzer):
    
    def __init__(self, pages, func, logger):
        Paralyzer.__init__(self, logger)
        self.pages = pages
        self.func = func
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
        filePara = FileDownloadParalyzer([tag['href'] for tag in linkTagsFonds],logger=self.api.logger)
        pages = filePara.perform()
        #kursPara = KursParseParalyzer(pages, self._parse_kurse_html_fonds, self.api.logger)
        #for kurse in kursPara.perform():
        #    for kurs in kurse:
        #        yield (kurs, self)
        for kursPage in pages:
            for item in self._parse_kurse_html_fonds(kursPage):
                yield (item, self)
        filePara.files = [tag['href'] for tag in linkTagsETF]
        for kursPage in filePara.perform():
            for item in self._parse_kurse_html_etf(kursPage):
                yield (item, self)

    def _parse_kurse_html_fonds(self, kursPage):
        erg = []
        base = BeautifulSoup(kursPage).find('div', 'content')
        name = base.h1.contents[0]
        #print name
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
                    #FIXME fetch year from html
                    date = to_datetime(tds[8].contents[0]+'10', tds[9].contents[0])
                    volume = to_int(tds[12].contents[0])
                    change = tds[14]
                    if change.span:
                        change = change.span
                    change = to_float(change.contents[0])
                    erg.append({'name':name,'isin':isin,'exchange':exchange,'price':price,
                                'date':date,'currency':currency,'volume':volume,
                                'type':TYPE_FUND,'change':change})
        return erg
                    #yield {'name':name,'isin':isin,'exchange':exchange,'price':price,
                    #  'date':date,'currency':currency,'volume':volume,
                    #  'type':TYPE_FUND,'change':change}

    def _parse_kurse_html_etf(self, kursPage):
        base = BeautifulSoup(kursPage).find('div', 'content')
        name = base.h1.contents[0]
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
                    #FIXME fetch year from html
                    date = to_datetime(tds[6].contents[0]+'10', tds[7].contents[0])
                    volume = to_int(tds[11].contents[0])
                    change = tds[3]
                    if change.span:
                        change = change.span
                    change = to_float(change.contents[0])
                    yield {'name':name,'isin':isin,'exchange':exchange,'price':price,
                      'date':date,'currency':currency,'volume':volume,
                      'type':TYPE_ETF,'change':change}

    def update_stocks(self, stocks):
        for stock in stocks:
            if stock.type == TYPE_FUND:
                file = opener.open("http://fonds.onvista.de/kurse.html", urllib.urlencode({"ISIN": stock.isin}))
                generator = self._parse_kurse_html_fonds(file)
            elif stock.type == TYPE_ETF:
                file = opener.open("http://etf.onvista.de/kurse.html", urllib.urlencode({"ISIN": stock.isin}))
                generator = self._parse_kurse_html_etf(file)
            else:
                print "Unknown stock type in onvistaplugin.update_stocks"
            for item in generator:
                if item['exchange'] == stock.exchange.name and \
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
        if stock.type == TYPE_FUND:
            url = 'http://fonds.onvista.de/kurshistorie.html'
            width = '100%'
        elif stock.type == TYPE_ETF:
            url = 'http://etf.onvista.de/kurshistorie.html'
            width = '640'
        else:
            self.api.logger.error("Uknown stock type in onvistaplugin.search_kurse")
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
    s1 = Stock('DE0008474248', ex, TYPE_FUND)
    s2 = Stock('LU0382362290', ex, TYPE_ETF)
    
    def test_update():
        
        plugin.update_stocks([s1, s2])
        print s1.price, s1.change, s1.date
        print s2.price, s2.change, s2.date

    def test_search():
        for res in  plugin.search('etflab'):
            print res
            #break
            
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

    plugin = OnvistaPlugin()
    ex = Exchange()
    s1 = Stock('LU0136412771', ex, TYPE_FUND)
    s2 = Stock('LU0103598305', ex, TYPE_FUND)
    s3 = Stock('LU0382362290', ex, TYPE_ETF)
    #print test_search()
    #print plugin.search_kurse(s1)
    #print plugin.search_kurse(s3)
    #test_parse_kurse()
    #test_update()
    test_historicals()
