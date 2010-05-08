
from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector


from finanzpartner.items import FinanzpartnerItem

class SingleISINSpider(BaseSpider):
    
    domain_name = "finanzpartner.de"
    start_urls = [
                  'http://www.finanzpartner.de/fi/'
                  ]
    
    def __init__(self, isin):
        self.start_urls = [u+isin+"/" for u in self.start_urls]
    
    def parse(self, response):
        hxs = HtmlXPathSelector(response)
        name = hxs.select('html/body/div[@class="page_margins"]/div[@class="page"]/div[@id="main"]/div[@id="col3"]/div[@id="col3_content"]/center/table[1]/tr[2]/td[2]/text()').extract()
        isin = hxs.select('html/body/div[@class="page_margins"]/div[@class="page"]/div[@id="main"]/div[@id="col3"]/div[@id="col3_content"]/center/table[1]/tr[4]/td[2]/text()').extract()
        wkn = hxs.select('html/body/div[@class="page_margins"]/div[@class="page"]/div[@id="main"]/div[@id="col3"]/div[@id="col3_content"]/center/table[1]/tr[5]/td[2]/text()').extract()
        buyLine = hxs.select('html/body/div[@class="page_margins"]/div[@class="page"]/div[@id="main"]/div[@id="col3"]/div[@id="col3_content"]/center/table[1]/tr[6]/td[2]/text()').extract()
        buystring = buyLine[0]
        buyList = buystring.split()
        buyDate = buyList[2][1:-1]
        sellLine = hxs.select('html/body/div[@class="page_margins"]/div[@class="page"]/div[@id="main"]/div[@id="col3"]/div[@id="col3_content"]/center/table[1]/tr[7]/td[2]/text()').extract()
        sellstring = sellLine[0]
        sellList = sellstring.split()
        erg = FinanzpartnerItem()
        erg['name'] = name
        erg['ISIN'] = isin
        erg['WKN'] = wkn
        erg['buy'] = buyList[0]
        erg['currency'] = buyList[1]
        erg['date'] = buyDate
        erg['sell'] = sellList[0]
        return [erg]
    
SPIDER = SingleISINSpider('LU0068337053')

#name
#hxs.select('html/body/div[@class="page_margins"]/div[@class="page"]/div[@id="main"]/div[@id="col3"]/div[@id="col3_content"]/center/table[1]/tr[2]/td[2]/text()').extract()

if __name__ == "__main__":
    pass