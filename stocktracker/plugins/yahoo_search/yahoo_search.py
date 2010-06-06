# -*- coding: utf-8 -*-
from BeautifulSoup import BeautifulSoup
from urllib import urlopen
import re


TYPES = ['Fonds', 'Aktie']

class YahooSearch():
    configurable = False
    name = "yahoo search"
    
    def activate(self):
        self.api.register_datasource(self, self.name)
                
    def deactivate(self):
        self.api.deregister_datasource(self, self.name)
            
    def search(self, searchstring, callback):
        self.callback = callback
        self.__parse(self.__request(searchstring))
    
    def __request(self, searchstring):
        url = 'http://de.finsearch.yahoo.com/de/index.php?nm='+searchstring+'&tp=*&r=*&sub=Suchen'
        return urlopen(url)
    
    def __parse(self, doc):
        #1. beatifull soup does not like this part of the html file
        #2. remove newlines
        my_massage = [(re.compile('OPTION VALUE=>---------------------<'), ''), \
                      (re.compile('\n'), '')]
        soup = BeautifulSoup(doc, markupMassage=my_massage)
        for main_tab in soup.findAll('table', width="752"):
            for table in main_tab.findAll('table', cellpadding='3', cellspacing='1',width='100%'):
                for row in table('tr'):
                    item = []
                    for s in row('td', {'class':'yfnc_tabledata1'}, text=True):
                        s = s.strip()
                        if s is not None and s!=unicode(''):
                            item.append(s)
                    if len(item) == 12:
                        item = self.__to_dict(item[:-2])
                        if item is not None:
                            self.callback(item, self)
                    
    def __to_dict(self, item):
        if not item[5] in TYPES:
            return None
        res = {}
        res['name']         = item[0]
        res['yahoo_symbol'] = item[1]
        res['isin']         = item[2]
        res['wkn']          = item[3]
        res['exchange']     = item[4]
        res['type']         = TYPES.index(item[5])
        res['price']        = item[6]
        res['time']         = item[7]
        res['change']       = item[8]
        return res

if __name__ == '__main__':
    ys = YahooSearch()
    ys.search('yahoo', None)
