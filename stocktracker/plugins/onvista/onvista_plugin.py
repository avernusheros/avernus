# -*- coding: utf-8 -*-
from BeautifulSoup import BeautifulSoup, NavigableString
from datetime import datetime 
import threading, re
from Queue import Queue
import urllib
import urllib2

    
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


class FileGetter(threading.Thread):
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
            
def get_files(files):
    def producer(q, files):
        for file in files:
            thread = FileGetter(file)
            thread.start()
            q.put(thread, True)
    
    print "Getting ", len(files), " Files."
    finished = []
    
    def consumer(q, total_files):
        while len(finished) < total_files:
            thread = q.get(True)
            thread.join()
            finished.append(thread.get_result())
            
    q = Queue(3)
    prod_thread = threading.Thread(target=producer, args=(q, files))
    cons_thread = threading.Thread(target=consumer, args=(q, len(files)))
    prod_thread.start()
    cons_thread.start()
    prod_thread.join()
    cons_thread.join()
    return finished


class OnvistaPlugin():
    configurable = False
    
    def __init__(self):
        self.name = 'onvista.de'
        self.exchangeBlacklist = ['Summe:','Realtime-Kurse','Neartime-Kurse',\
                                 'Leider stehen zu diesem Fonds keine Informationen zur Verfügung.']

    def activate(self):
        self.api.register_datasource(self, self.name)
                        
    def deactivate(self):
        self.api.deregister_datasource(self, self.name)
    
    def search(self, searchstring):
        page = opener.open("http://www.onvista.de/suche.html", urllib.urlencode({"TARGET": "kurse", "SEARCH_VALUE": searchstring,'ID_TOOL':'FUN' }))
        soup = BeautifulSoup(page.read())
        linkTagsFonds = soup.findAll(attrs={'href' : re.compile('http://fonds\\.onvista\\.de/kurse\\.html\?ID_INSTRUMENT=\d+')})
        linkTagsETF = soup.findAll(attrs={'href' : re.compile('http://etf\\.onvista\\.de/kurse\\.html\?ID_INSTRUMENT=\d+')})
        for kursPage in get_files([tag['href'] for tag in linkTagsFonds]):
            for item in self._parse_kurse_html_fonds(kursPage):
                yield (item, self)
        for kursPage in get_files([tag['href'] for tag in linkTagsETF]):
            for item in self._parse_kurse_html_etf(kursPage):
                yield (item, self)
        
    def _parse_kurse_html_fonds(self, kursPage):
        base = BeautifulSoup(kursPage).find('div', 'content')
        name = base.h2.contents[0]
        isin = base.findAll('tr','hgrau2')[1].findAll('td')[1].contents[0].replace('&nbsp;','')
        for row in base.find('div','t', style=None).find('table'):
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
                    yield {'name':name,'isin':isin,'exchange':exchange,'price':price,
                      'date':date,'currency':currency,'volume':volume,
                      'type':TYPE_FUND,'change':change}
    
    def _parse_kurse_html_etf(self, kursPage):
        base = BeautifulSoup(kursPage).find('div', 'content')
        name = base.h2.contents[0]
        isin = base.findAll('tr','hgrau2')[1].findAll('td')[1].contents[0].replace('&nbsp;','')
        for row in base.find('div','t', style=None).find('table'):
            tds = row.findAll('td')
            if len(tds)>3:
                exchangeTag = tds[0]
                if not exchangeTag.contents[0] in self.exchangeBlacklist:
                    exchange = ""
                    if not isinstance(exchangeTag.contents[0], NavigableString):
                        exchange = exchangeTag.a.contents[0]
                    else:
                        exchange = exchangeTag.contents[0]
                    currency = tds[4].contents[0]
                    price = to_float(tds[15].contents[0])
                    #FIXME fetch year from html
                    date = to_datetime(tds[5].contents[0]+'10', tds[6].contents[0])
                    volume = to_int(tds[14].contents[0])
                    change = tds[7]
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
                break
            for item in generator:
                if item['exchange'] == stock.exchange.name and \
                        item['currency'] == stock.currency:
                    stock.price = item['price']
                    stock.date = item['date']
                    stock.change = item['change']
                    stock.volume = item['volume']
                    stock.updated = True
                    break
                
    def search_kurse(self, stock):
        file = opener.open('http://fonds.onvista.de/kurshistorie.html',urllib.urlencode({'ISIN':stock.isin, 'RANGE':'60M'}))
        soup = BeautifulSoup(file)
        lines = soup.html.body.findAll('table',{'width':'100%'})[2].findAll('tr',{'align':'right'})
        erg = []
        for line in lines:
            tds = line.findAll('td')
            day = to_datetime(tds[0].contents[0])
            kurs = to_float(tds[1].contents[0])
            erg.append((day, kurs))
        return erg
        

        
if __name__ == "__main__":
    
    class Exchange():
        name = 'KAG-Kurs'
    
    class Stock():
        def __init__(self, isin, ex, type):
            self.isin = isin
            self.type = type
            self.exchange = ex
            self.currency = 'EUR'
    
    def test_update():
        ex = Exchange()
        s1 = Stock('DE0008474248', ex, TYPE_FUND)
        s2 = Stock('LU0382362290', ex, TYPE_ETF)
        plugin.update_stocks([s1, s2])
        print s1.price, s1.change, s1.date
        print s2.price, s2.change, s2.date
    
    def test_search():
        for res in  plugin.search('easyetf'):
            print res
            #break
    
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
    print plugin.search_kurse(s1)
    #test_parse_kurse()
    #test_update()