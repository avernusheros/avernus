from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.selector import HtmlXPathSelector
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor

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
             Rule(SgmlLinkExtractor(allow=('http://[^\\.]+\.onvista\.de/snapshot\.html\\?ID_OSI=\\d+',)), callback='debug'),
             )

    search_URL ='http://www.onvista.de/suche.html?SELECTED_TOOL=%%TOOL%%&SEARCH_TEXT=%%MODE%%&SEARCH_VALUE=%%SEARCH%%&q.x=38&q.y=6&q=q'
    
    def schedule_search(self, value, tool='ALL', mode='ALL', only=True):
        url = self.search_URL.replace('%%TOOL%%',self.tools[tool])
        url = url.replace('%%MODE%%', self.modes[mode])
        url = url.replace('%%SEARCH%%', value)
        if only:
            self.start_urls = [url]
        else:
            self.start_urls.append(url)
        
            
    def debug(self, response):
        self.log("Parsing Response from " + response.url)
        hxs = HtmlXPathSelector(response)
        name = hxs.select('html/body/div[@id="ONVISTA"]/table[@class="RAHMEN"]/tr/td[@class="WEBSEITE"]/div[@class="content"]/h2[@class="EINZELANSICHTEN"]/text()').extract()
        print name
        
        
SPIDER = OnvistaSpider()
SPIDER.schedule_search("Telekom")
