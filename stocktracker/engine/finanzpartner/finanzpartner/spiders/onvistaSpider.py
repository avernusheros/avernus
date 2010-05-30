from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.selector import HtmlXPathSelector
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.spider import BaseSpider

from finanzpartner.items import OnvistaSearchStockItem

class OnvistaHistorySpider(BaseSpider):

    domain_name = "onvista.de"
    #http://fonds.onvista.de/kurshistorie.html?ID_NOTATION=4198043&RANGE=60M
    #problem: WAS IST DIE NUMMER HINTER ID_NOTATION
    start_urls = ["http://fonds.onvista.de/kurshistorie.html?ID_NOTATION=4198043&RANGE=60M"]

    def parse(self, response):
        self.log('Fonds page: %s' % response.url)
        hxs = HtmlXPathSelector(response)

class OnvistaSpider(CrawlSpider):

    domain_name = "onvista.de"
    tools = {
             'ALL':'ALL_TOOLS',
             'AKTIE':'STO',
             'FONDS':'FUN',
             'OPTION':'WAR',
             'ZERTIFIKAT':'CER',
             'INDEX':'IND',
             }
    modes = {
            'ALL':'WKN,ISIN,Name',
            }
    start_urls = []

    rules = (
             Rule(SgmlLinkExtractor(allow=('http://[^\\.]+\.onvista\.de/snapshot\.html\\?ID_OSI=\\d+',)), callback='detail_page_snapshot'),
             )

    search_URL ='http://www.onvista.de/suche.html?SELECTED_TOOL=%%TOOL%%&SEARCH_TEXT=%%MODE%%&SEARCH_VALUE=%%SEARCH%%&q.x=38&q.y=6&q=q'

    def __init__(self):
        CrawlSpider.__init__(self)
        self.state = "SEARCH"

    def schedule_search(self, value, tool='ALL', mode='ALL', only=True):
        url = self.search_URL.replace('%%TOOL%%',self.tools[tool])
        url = url.replace('%%MODE%%', self.modes[mode])
        url = url.replace('%%SEARCH%%', value)
        if only:
            self.start_urls = [url]
        else:
            self.start_urls.append(url)


    def detail_page_snapshot(self, response):
        #self.log("Parsing Response from " + response.url)
        hxs = HtmlXPathSelector(response)
        name = hxs.select('html/body/div[@id="ONVISTA"]/table[@class="RAHMEN"]/tr/td[@class="WEBSEITE"]/div[@class="content"]/h2[@class="EINZELANSICHTEN"]/text()').extract()
        wkn = hxs.select('html/body/div[@id="ONVISTA"]/table[@class="RAHMEN"]/tr/td[@class="WEBSEITE"]/div[@class="content"]/div[@class="t"]/table[@class="weiss abst"]/tr[@class="hgrau2"]/td[2]/text()').extract()
        isin = hxs.select('html/body/div[@id="ONVISTA"]/table[@class="RAHMEN"]/tr/td[@class="WEBSEITE"]/div[@class="content"]/div[@class="t"]/table[@class="weiss abst"]/tr[@class="hgrau2"]/td[4]/text()').extract()
        kurs = hxs.select('html/body/div[@id="ONVISTA"]/table[@class="RAHMEN"]/tr/td[@class="WEBSEITE"]/div[@class="content"]/div[@class="t"]/table[@class="weiss abst"]/tr/td[@class="s2b hgrau1 hc"]/span/text()').extract()
        kursinfo = hxs.select('html/body/div[@id="ONVISTA"]/table[@class="RAHMEN"]/tr/td[@class="WEBSEITE"]/div[@class="content"]/div[@id="KURSINFORMATIONEN"]/div/text()').extract()
        #print type(kursinfo[0])
        boerse = [unicode(kursinfo[0].partition("(")[2].partition(",")[0])]
        kursdatum = [unicode(kursinfo[0].partition(",")[2].partition(",")[0].lstrip())]
        item = OnvistaSearchStockItem()
        item['name'] = name
        item['wkn'] = wkn
        item['isin'] = isin
        item['exchange'] = boerse
        item['rate'] = kurs
        item['date'] = kursdatum
        return item

SPIDER = OnvistaHistorySpider()
#SPIDER = OnvistaSpider()
#SPIDER.schedule_search("Telekom")
