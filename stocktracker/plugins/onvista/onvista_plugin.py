# -*- coding: utf-8 -*-
from BeautifulSoup import BeautifulSoup 
from BeautifulSoup import NavigableString
import re
    
    
TYPE = 0

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
        fd, tempname = tempfile.mkstemp(prefix='scrape')
        command = 'curl --include --insecure --silent ' + url
        #print "Command: ", command
        os.system(command + ' > ' + tempname)
        reply = open(tempname).read()
        os.remove(tempname)
        return reply
        
    def search(self, searchstring, callback):
        print "searching using ", self.name
        exchangeBlacklist = ['KAG-Kurs','Summe:','Realtime-Kurse','Neartime-Kurse', 'Leider stehen zu diesem Fonds keine Informationen zur Verfügung.']
        search_URL ='http://www.onvista.de/suche.html?TARGET=snapshot&ID_TOOL=FUN&SEARCH_VALUE='+searchstring
        soup = BeautifulSoup(self.curlURL(search_URL))
        linkTags = soup.findAll(attrs={'href' : re.compile('http://fonds\\.onvista\\.de/snapshot\\.html\?ID_INSTRUMENT=\d+')})
        links = [tag['href'] for tag in linkTags]
        for link in links:
            snapshot = self.curlURL(link)
            ssoup = BeautifulSoup(snapshot)
            base = ssoup.html.body.find('div', {'id':'ONVISTA'}).find('table','RAHMEN').tr.find('td','WEBSEITE').find('div','content')
            name = base.h2.contents[0]
            isin = base.find('table','hgrau1').tr.td.find('table','weiss').findAll('tr','hgrau2')[1].findAll('td')[1].contents[0].replace('&nbsp;','')
            kagKursText = base.find('span','KURSRICHTUNG').findNextSibling('span').contents[0]
            kagKursCurrency = kagKursText[-3:]
            kagKurs = kagKursText[:-3].replace('&nbsp;','')
            kagDateText = base.find('div',{'id':'KURSINFORMATIONEN'}).find('div','sm').contents[0]
            kagDateTimeBase = kagDateText.partition('(')[2].partition(';')[2]
            kagDate = kagDateTimeBase.partition(',')[0]
            kagTime = kagDateTimeBase.partition(';')[2].partition(')')[0]
            kagChange = base.findAll('table','hgrau1')[3].tr.td.find('table','weiss').findAll('tr','hgrau2')[1].findAll('td')[1].span.contents[0]
            print "Returning KAG"
            callback({'name':name,'isin':isin,'exchange':'KAG','price':kagKurs,
                      'date':kagDate,'time':kagTime,'currency':kagKursCurrency,
                      'type':TYPE,'change':kagChange,'yahoo_symbol':'FURZ'}
            ,self)
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
                        buyPrice = tds[3].contents[0]
                        sellPrice = tds[6].contents[0]
                        day = tds[8].contents[0]
                        timeOfDay = tds[9].contents[0]
                        volume = tds[12].contents[0]
                        change = tds[14]
                        if change.span:
                            change = change.span
                        change = change.contents[0]
                        #print name, isin, exchange, currency, buyPrice,sellPrice,day,timeOfDay,volume
                        print "Returning ",exchange
                        callback({'name':name,'isin':isin,'exchange':exchange,
                                  'currency':currency,'price':buyPrice,'sell':sellPrice,
                                  'date':day,'time':timeOfDay,'volume':volume,
                                  'type':TYPE,'change':change,'yahoo_symbol':'FURZ'}
                        ,self)
        
if __name__ == "__main__":
    plugin = OnvistaPlugin()
    searchstring = "emerging"
    plugin.search(searchstring, lambda a,b:None)