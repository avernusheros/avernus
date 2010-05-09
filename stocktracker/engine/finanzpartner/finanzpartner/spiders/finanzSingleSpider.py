
from scrapy.spider import BaseSpider
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.selector import HtmlXPathSelector
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.http import Request

from finanzpartner.items import FinanzpartnerItem

class FinanzpartnerSpider:
    
    def parse_fonds_page(self, response):
        #self.log('Fonds page: %s' % response.url)
        hxs = HtmlXPathSelector(response)
        name = hxs.select('html/body/div[@class="page_margins"]/div[@class="page"]/div[@id="main"]/div[@id="col3"]/div[@id="col3_content"]/center/table[1]/tr[2]/td[2]/text()').extract()
        isin = hxs.select('html/body/div[@class="page_margins"]/div[@class="page"]/div[@id="main"]/div[@id="col3"]/div[@id="col3_content"]/center/table[1]/tr[4]/td[2]/text()').extract()
        wkn = hxs.select('html/body/div[@class="page_margins"]/div[@class="page"]/div[@id="main"]/div[@id="col3"]/div[@id="col3_content"]/center/table[1]/tr[5]/td[2]/text()').extract()
        buyLine = hxs.select('html/body/div[@class="page_margins"]/div[@class="page"]/div[@id="main"]/div[@id="col3"]/div[@id="col3_content"]/center/table[1]/tr[6]/td[2]/text()').extract()
        buyList = []
        if len(buyLine)>0:
            buystring = buyLine[0]
            buyList = buystring.split()
        buyDate = ''
        buy = ''
        currency = ''
        if len(buyList)>0:
            #print "Liste: ", buyList, type(buyList)
            buy = buyList[0]
            if len(buyList)>1:
                currency = buyList[1]
                buyDate = buyList[2][1:-1]
        sellLine = hxs.select('html/body/div[@class="page_margins"]/div[@class="page"]/div[@id="main"]/div[@id="col3"]/div[@id="col3_content"]/center/table[1]/tr[7]/td[2]/text()').extract()
        sellstring = sellLine[0]
        sellList = sellstring.split()
        erg = FinanzpartnerItem()
        erg['name'] = name
        erg['ISIN'] = isin
        erg['WKN'] = wkn
        erg['buy'] = buy
        erg['currency'] = currency
        erg['date'] = buyDate
        erg['sell'] = sellList[0]
        return [erg]

class SingleISINSpider(BaseSpider, FinanzpartnerSpider):
    
    domain_name = "finanzpartner.de"
    start_urls = [
                  'http://www.finanzpartner.de/fi/'
                  ]
    
    def __init__(self, isin):
        self.start_urls = [u+isin+"/" for u in self.start_urls]
        self.parse = self.parse_fonds_page
        BaseSpider.__init__(self)
    
class AllFondsSpider(CrawlSpider, FinanzpartnerSpider):
    
    domain_name = "finanzpartner.de"
    start_urls = [
                  'http://www.finanzpartner.de/investmentfonds/'
                  ]
    rules = (
        Rule(SgmlLinkExtractor(allow=(r'osc/[^\\.]*\.htm', ))),
        Rule(SgmlLinkExtractor(allow=(r'/fi/', )), callback='parse_fonds_page'), 
             )
    
    
        
#SPIDER = AllFondsSpider()
SPIDER = SingleISINSpider('LU0068337053')

if __name__ == "__main__":
    pass