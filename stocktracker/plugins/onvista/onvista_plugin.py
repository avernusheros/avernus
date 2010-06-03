# -*- coding: utf-8 -*-
from BeautifulSoup import BeautifulSoup 
import re
    

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
        print url
        import os, tempfile
        fd, tempname = tempfile.mkstemp(prefix='scrape')
        command = 'curl --include --insecure --silent ' + url
        print "Command: ", command
        os.system(command + ' > ' + tempname)
        reply = open(tempname).read()
        os.remove(tempname)
        return reply
        
    def search(self, searchstring, callback):
        print "searching using ", self.name
        search_URL ='http://www.onvista.de/suche.html?TARGET=snapshot&ID_TOOL=FUN&SEARCH_VALUE='+searchstring
        soup = BeautifulSoup(self.curlURL(search_URL))
        linkTags = soup.findAll(attrs={'href' : re.compile('http://fonds\\.onvista\\.de/snapshot\\.html\?ID_INSTRUMENT=\d+')})
        links = [tag['href'] for tag in linkTags]
        erg = []
        for link in links:
            snapshot = self.curlURL(link)
            ssoup = BeautifulSoup(snapshot)
            name = ssoup.html.body.find('div', {'id':'ONVISTA'}).find('table','RAHMEN').tr.find('td','WEBSEITE').find('div','content').h2.contents[0]
            print name
        
if __name__ == "__main__":
    plugin = OnvistaPlugin()
    searchstring = "multi"
    plugin.search(searchstring, lambda:None)