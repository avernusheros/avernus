from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.selector import HtmlXPathSelector
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.spider import BaseSpider
from scrapy.http import Request

from finanzpartner.items import OnvistaSearchStockItem, OnvistaHistoricalRateItem

class OnvistaHistorySpider(BaseSpider):

    domain_name = "onvista.de"
    #http://fonds.onvista.de/kurshistorie.html?ID_NOTATION=4198043&RANGE=60M
    #problem: WAS IST DIE NUMMER HINTER ID_NOTATION
    start_urls = []

    def __init__(self, wkn):
        self.wkn = wkn
        self.history_url = "http://fonds.onvista.de/kurshistorie.html?ID_NOTATION=%%KEY%%&RANGE=60M"
        self.search_url = "http://www.onvista.de/suche.html?SELECTED_TOOL=FUN&SEARCH_TEXT=WKN,ISIN,Name&SEARCH_VALUE="+ wkn
        self.start_urls = [self.search_url]

    def parse(self, response):
        self.log('Response page: %s' % response.url)
        hxs = HtmlXPathSelector(response)
        keyLink = hxs.select('html/body/div[@id="ONVISTA"]/table[@class="RAHMEN"]/tr/td[@class="WEBSEITE"]/div[@class="content"]/div[@class="hp_50_l"]/div[@class="t"]/table[@class="weiss"]/tr[@class="hgrau2"]/td/img/@src').extract()
        key = unicode(keyLink[0].partition("=")[2].partition("&")[0])
        yield Request(self.history_url.replace('%%KEY%%', key), callback=self.parse_history)
        
    def parse_history(self, response):
        self.log('Response history page: %s' % response.url)
        hxs = HtmlXPathSelector(response)
        for rowXs in hxs.select('html/body/table[@width="100%"]/tr'):
            date = rowXs.select('td[1]/text()').extract()
            kurs = rowXs.select('td[2]/text()').extract()
            item = OnvistaHistoricalRateItem()
            item['wkn'] = self.wkn
            item['date'] = date
            item['rate'] = kurs
            yield item
        

class OnvistaSpider(CrawlSpider):

    domain_name = "onvista.de"
    modes = {
            'ALL':'WKN,ISIN,Name',
            }
    start_urls = []

    rules = (
             Rule(SgmlLinkExtractor(allow=('http://fonds\\.onvista\\.de/snapshot\\.html\?ID_INSTRUMENT=\d+',)), callback='detail_page_snapshot'),
             )

    search_URL ='http://www.onvista.de/suche.html?SELECTED_TOOL=FUN&SEARCH_TEXT=%%MODE%%&SEARCH_VALUE=%%SEARCH%%'

    def __init__(self):
        CrawlSpider.__init__(self)
        self.state = "SEARCH"

    def schedule_search(self, value, mode='ALL', only=True):
        url = self.search_URL
        url = url.replace('%%MODE%%', self.modes[mode])
        url = url.replace('%%SEARCH%%', value)
        if only:
            self.start_urls = [url]
        else:
            self.start_urls.append(url)


    def detail_page_snapshot(self, response):
        #self.log("Parsing Response from " + response.url)
        hxs = HtmlXPathSelector(response)
        name = hxs.select('html/body/div[@id="ONVISTA"]/table[@class="RAHMEN"]/tr/td[@class="WEBSEITE"]/div[@class="content"]/h2/text()').extract()
        #print "Name: ", name
        wkn = hxs.select('html/body/div[@id="ONVISTA"]/table[@class="RAHMEN"]/tr/td[@class="WEBSEITE"]/div[@class="content"]/table[@class="hgrau1"][1]/tr/td/table[@class="weiss"]/tr[@class="hgrau2"][1]/td[2]/text()').extract()
        isin = hxs.select('html/body/div[@id="ONVISTA"]/table[@class="RAHMEN"]/tr/td[@class="WEBSEITE"]/div[@class="content"]/table[@class="hgrau1"][1]/tr/td/table[@class="weiss"]/tr[@class="hgrau2"][2]/td[2]/text()').extract()
        kurs = hxs.select('html/body/div[@id="ONVISTA"]/table[@class="RAHMEN"]/tr/td[@class="WEBSEITE"]/div[@class="content"]/table[@class="hgrau1"][2]/tr/td/table[@class="weiss"]/tr[@class="hgrau1"]/td/span[@class="g"]/text()').extract()
        kursSearch = hxs.select('html/body/div[@id="ONVISTA"]/table[@class="RAHMEN"]/tr/td[@class="WEBSEITE"]/div[@class="content"]/div[@class="hp_50_l"]/div[@class="t"]/table[@class="weiss"]').extract()
        #print "KursSearch: ", kursSearch
        #boerse = [unicode(kursinfo[0].partition("(")[2].partition(",")[0])]
        currency = [unicode(kurs[0][-3:])]
        rate = [unicode(kurs[0][:-4])] 
        item = OnvistaSearchStockItem()
        item['name'] = name
        item['wkn'] = wkn
        item['isin'] = isin
        item['rate'] = rate
        item['currency'] = currency
        return item

SPIDER = OnvistaHistorySpider("926200")
#SPIDER = OnvistaSpider()
#SPIDER.schedule_search("multi invest")
