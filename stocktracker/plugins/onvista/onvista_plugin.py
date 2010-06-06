# -*- coding: utf-8 -*-
from BeautifulSoup import BeautifulSoup 
from BeautifulSoup import NavigableString
import re
from datetime import datetime 
    
TYPE = 0

def to_float(s):
    return float(s.replace(',','.'))

def to_datetime(date, time):
    return datetime.strptime(date+time, "%d.%m.%Y%H:%M:%S")


class OnvistaPlugin():
    configurable = False
    
    def __init__(self):
        self.name = 'onvista.de'

    def activate(self):
        self.api.register_datasource(self, self.name)
                        
    def deactivate(self):
        self.api.deregister_datasource(self, self.name)
        
    def curlURL(self, url):
        url = "'" + url.replace("'", "'\\''") + "'"
        #print url
        import os, tempfile
        #make a temp file to store the data in
        fd, tempname = tempfile.mkstemp(prefix='scrape')
        command = 'curl --include --insecure --silent ' + url
        #download with curl into the tempfile
        os.system(command + ' > ' + tempname)
        #read, delete and return
        reply = open(tempname).read()
        os.remove(tempname)
        return reply
        
    def search(self, searchstring):
        print "searching using ", self.name
        #blacklist to filter table rows that do not contain a price
        exchangeBlacklist = ['KAG-Kurs','Summe:','Realtime-Kurse','Neartime-Kurse', 'Leider stehen zu diesem Fonds keine Informationen zur Verfügung.']
        search_URL ='http://www.onvista.de/suche.html?TARGET=snapshot&ID_TOOL=FUN&SEARCH_VALUE='+searchstring
        soup = BeautifulSoup(self.curlURL(search_URL))
        #all the tags that lead to a snapshot page on the search result page
        linkTags = soup.findAll(attrs={'href' : re.compile('http://fonds\\.onvista\\.de/snapshot\\.html\?ID_INSTRUMENT=\d+')})
        links = [tag['href'] for tag in linkTags]
        print "Found ", len(links)
        for link in links:
            print "Fetching ", links.index(link)+1, "/", len(links)
            snapshot = self.curlURL(link)
            ssoup = BeautifulSoup(snapshot)
            #the base content area containing everything of importance
            base = ssoup.html.body.find('div', {'id':'ONVISTA'}).find('table','RAHMEN').tr.find('td','WEBSEITE').find('div','content')
            name = base.h2.contents[0]
            isin = base.find('table','hgrau1').tr.td.find('table','weiss').findAll('tr','hgrau2')[1].findAll('td')[1].contents[0].replace('&nbsp;','')
            # the KAG kurs is on the snapshot page
            kagKursText = base.find('span','KURSRICHTUNG').findNextSibling('span').contents[0]
            kagKursCurrency = kagKursText[-3:]
            kagKurs = to_float(kagKursText[:-3].replace('&nbsp;',''))
            kagDateText = base.find('div',{'id':'KURSINFORMATIONEN'}).find('div','sm').contents[0]
            kagDateTimeBase = kagDateText.partition('(')[2].partition(';')[2]
            kagDate = kagDateTimeBase.partition(',')[0]
            kagTime = kagDateTimeBase.partition(';')[2].partition(')')[0]
            date = to_datetime(kagDate, kagTime)
            kagChange = base.findAll('table','hgrau1')[3].tr.td.find('table','weiss').findAll('tr','hgrau2')[1].findAll('td')[1]
            if kagChange.span:
                kagChange = kagChange.span
            kagChange = to_float(kagChange.contents[0])
            #print "Returning KAG"
            # return the result with the kag price
            yield ({'name':name,'isin':isin,'exchange':'KAG','price':kagKurs,
                      'date':date,'currency':kagKursCurrency,
                      'type':TYPE,'change':kagChange}
                ,self)
            #for the prices on the different stock exchanges, there is a detail page
            kurslink = ssoup.find(attrs={'href':re.compile('http://fonds\\.onvista\\.de/kurse\\.html')})['href']
            kursPage = self.curlURL(kurslink)
            kursSoup = BeautifulSoup(kursPage)
            tableRows = kursSoup.find('table','weiss abst').findAll('tr')
            for row in tableRows:
                tds = row.findAll('td')
                if len(tds)>0:
                    exchangeTag = tds[0]
                    if not exchangeTag.contents[0] in exchangeBlacklist:
                        exchange = ""
                        #print type(exchangeTag.contents[0])
                        if not isinstance(exchangeTag.contents[0], NavigableString):
                            exchange = exchangeTag.a.contents[0]
                        else:
                            exchange = exchangeTag.contents[0]
                        currencyTag = tds[1]
                        currency = currencyTag.contents[0]
                        buyPrice = to_float(tds[3].contents[0])
                        sellPrice = tds[6].contents[0]
                        date = to_datetime(tds[8].contents[0], tds[9].contents[0])
                        volume = tds[12].contents[0]
                        change = tds[14]
                        if change.span:
                            change = change.span
                        change = to_float(change.contents[0])
                        #print name, isin, exchange, currency, buyPrice,sellPrice,day,timeOfDay,volume
                        #print "Returning ",exchange
                        yield ({'name':name,'isin':isin,'exchange':exchange,
                                  'currency':currency,'price':buyPrice,'sell':sellPrice,
                                  'date':date,'volume':volume,
                                  'type':TYPE,'change':change}
                            ,self)
        
if __name__ == "__main__":
    plugin = OnvistaPlugin()
    searchstring = "emerging"
    for item in plugin.search(searchstring):
        print item
        break
