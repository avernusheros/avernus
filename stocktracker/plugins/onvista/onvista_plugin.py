# -*- coding: utf-8 -*-
from BeautifulSoup import BeautifulSoup, NavigableString
from datetime import datetime 
import threading, re
from Queue import Queue
import urllib
import urllib2

    
TYPE = 0

def to_float(s):
    return float(s.replace('.','').replace(',','.'))

def to_datetime(date, time):
    return datetime.strptime(date+time, "%d.%m.%y%H:%M:%S")


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
        self.exchangeBlacklist = ['Summe:','Realtime-Kurse','Neartime-Kurse', 'Leider stehen zu diesem Fonds keine Informationen zur Verfügung.']

    def activate(self):
        self.api.register_datasource(self, self.name)
                        
    def deactivate(self):
        self.api.deregister_datasource(self, self.name)
    
    def search(self, searchstring):
        #blacklist to filter table rows that do not contain a price
        #search_URL ="http://www.onvista.de/suche.html?TARGET=kurs&ID_TOOL=FUN&SEARCH_VALUE=%s" % (searchstring,)
        page = opener.open("http://www.onvista.de/suche.html", urllib.urlencode({"TARGET": "kurse", "SEARCH_VALUE": searchstring,'ID_TOOL':'FUN' }))
        soup = BeautifulSoup(page.read())
        #all the tags that lead to a snapshot page on the search result page
        linkTags = soup.findAll(attrs={'href' : re.compile('http://fonds\\.onvista\\.de/kurse\\.html\?ID_INSTRUMENT=\d+')})
        links = [tag['href'] for tag in linkTags]
        for kursPage in get_files(links):
            for item in self._parse_kurse_html(kursPage):
                yield (item, self)
        
    def _parse_kurse_html(self, kursPage):
        soup = BeautifulSoup(kursPage)
        base = soup.html.body.find('div', {'id':'ONVISTA'}).find('table','RAHMEN').tr.find('td','WEBSEITE').find('div','content')
        name = base.h2.contents[0]
        isin = base.find('table','hgrau1').tr.td.find('table','weiss').findAll('tr','hgrau2')[1].findAll('td')[1].contents[0].replace('&nbsp;','')
        for row in soup.find('table','weiss abst').findAll('tr'):
            tds = row.findAll('td')
            if len(tds)>1:
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
                    volume = tds[12].contents[0]
                    change = tds[14]
                    if change.span:
                        change = change.span
                    change = to_float(change.contents[0])
                    yield {'name':name,'isin':isin,'exchange':exchange,'price':price,
                      'date':date,'currency':currency,'volume':volume,
                      'type':TYPE,'change':change}
                        
    def update_stocks(self, stocks):
        for stock in stocks:
            file = opener.open("http://fonds.onvista.de/kurse.html", urllib.urlencode({"ISIN": stock.isin}))
            for item in self._parse_kurse_html(file):
                if item['exchange'] == stock.exchange.name and \
                        item['currency'] == stock.currency:
                    stock.price = item['price']
                    stock.date = item['date']
                    stock.change = item['change']
                    stock.volume = item['volume']
                    stock.updated = True
                    break

        
if __name__ == "__main__":
    
    class Exchange():
        name = 'KAG-Kurs'
    
    class Stock():
        def __init__(self, isin, ex):
            self.isin = isin
            self.exchange = ex
            self.currency = 'EUR'
    
    plugin = OnvistaPlugin()
    for res in  plugin.search('emerging'):
        print res
        break
    ex = Exchange()
    s1 = Stock('LU0136412771', ex)
    s2 = Stock('LU0103598305', ex)
    plugin.update_stocks([s1, s2])
    print s1.price, s1.change, s1.date
