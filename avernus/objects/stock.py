from avernus.objects.model import SQLiteEntity
import datetime


FUND  = 0
STOCK = 1
ETF   = 2
BOND  = 3

TYPES = {FUND: 'FUND',
         STOCK: 'STOCK',
         ETF: 'ETF',
         BOND: 'BOND'
         }


class Stock(SQLiteEntity):
    __primaryKey__ = 'id'
    __tableName__ = "stock"
    __columns__ = {
                   'id': 'INTEGER',
                   'isin': 'VARCHAR',
                   'type': 'INTEGER',
                   'name': 'VARCHAR',
                   'exchange': 'VARCHAR',
                   'currency': 'VARCHAR',
                   'price': 'FLOAT',
                   'date': 'TIMESTAMP',
                   'change': 'FLOAT',
                   'ter': 'FLOAT',
                   'source': 'VARCHAR',
                  }

    __comparisonPositives__ = ['isin', 'currency']
    __defaultValues__ = {
                         'exchange':None,
                         'currency':'',
                         'price':0.0,
                         'date': datetime.datetime(2000, 1, 1),
                         'change':0.0,
                         'type':1,
                         'name':'',
                         'isin':'',
                         'ter':0.0
                         }

    #needed for some treeviews, e.g. news_tab
    @property
    def stock(self):
        return self

    def getDimensionText(self, dim):
        advs = self.getAssetDimensionValue(dim)
        if len(advs) == 1:
            # we have 100% this value in its dimension
            return str(advs.pop(0))
        erg = ""
        i = 0
        for adv in advs:
            i += 1
            erg += str(adv)
            if i<len(advs):
                erg += ", "
        return erg

    def updateAssetDimensionValue(self, dimension, dimVals):
        for adv in self.getAssetDimensionValue(dimension):
            adv.delete()
        for dimVal, value in dimVals:
            self.controller.newAssetDimensionValue(self,dimVal,value)

    def getAssetDimensionValue(self, dim):
        assDimVals = self.controller.getAssetDimensionValueForStock(self, dim)
        return assDimVals

    @property
    def percent(self):
        try:
            return round(self.change * 100 / (self.price - self.change),2)
        except:
            return 0

    @property
    def type_string(self):
        if self.type in TYPES:
            return TYPES[self.type]
        return ''

    def __str__(self):
        return self.name +' | '+self.isin+' | '+self.exchange

    def update_price(self):
        self.controller.datasource_manager.update_stock(self)

    def get_price_at_date(self, date):
        return self.controller.getPriceFromStockAtDate(self, date)
