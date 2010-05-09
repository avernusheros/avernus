'''
Created on May 9, 2010

@author: bastian
'''
from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector

class YahooNameSearchSpider(BaseSpider):

    domain_name = "de.finsearch.yahoo.com"
    start_urls = [
                  'http://de.finsearch.yahoo.com/de/?s=de_sort&tp=S&nm='
                  ]
    
    def __init__(self, search):
        self.start_urls = [u+search for u in self.start_urls]
        BaseSpider.__init__(self)
        
    def parse(self, response):
        #self.log("Parsing response from %s", response.url)
        #print "ARSCH"
        hxs = HtmlXPathSelector(response)
        #print hxs.select('html/body/center/p/table/tr/td/center/table/tr/td[@class="yfnc_tableout1"]/table/tr/td/a').extract()
        #print "Names: ", hxs.select('html/body/center[1]/table/tr/td/table/tr/td/center/table/tr/td[@class="yfnc_tableout1"]/table/tr/td[@class="yfnc_h" and not(@align)]/a/text()').extract()
        #print "Symbols: ", hxs.select('html/body/center[1]/table/tr/td/table/tr/td/center/table/tr/td[@class="yfnc_tableout1"]/table/tr/td[2]/text()').extract()
        #print "ISINs: ", hxs.select('html/body/center[1]/table/tr/td/table/tr/td/center/table/tr/td[@class="yfnc_tableout1"]/table/tr/td[3]/text()').extract()
        #print "Exchanges: ", hxs.select('html/body/center[1]/table/tr/td/table/tr/td/center/table/tr/td[@class="yfnc_tableout1"]/table/tr/td[4]/text()').extract()
        for selector in hxs.select('html/body/center[1]/table/tr/td/table/tr/td/center/table/tr/td[@class="yfnc_tableout1"]/table/tr'):
            temp = {}
            temp['name'] = selector.select('td[1]/a/text()').extract()
            temp['symbol'] = selector.select('td[2]/text()').extract()
            temp['isin'] = selector.select('td[3]/text()').extract()
            temp['exchange'] = selector.select('td[4]/text()').extract()
            print temp
        
        
SPIDER = YahooNameSearchSpider("Telekom")