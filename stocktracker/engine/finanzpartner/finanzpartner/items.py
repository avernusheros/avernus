# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/topics/items.html

from scrapy.item import Item, Field

class StockInfoItem(Item):
    # define the fields for your item here like:
    name = Field()
    ISIN = Field()
    WKN = Field()
    buy = Field()
    currency = Field()
    date = Field()
    sell = Field()
    
class OnvistaSearchStockItem(Item):
    name = Field()
    isin = Field()
    wkn = Field()
    exchange = Field()
    date = Field()
    rate = Field()