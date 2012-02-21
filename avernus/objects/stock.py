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

    __comparisonPositives__ = ['isin', 'currency', 'source']
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

    def updateAssetDimensionValue(self, dimension, dimVals):
        from avernus.controller import portfolio_controller
        for adv in self.getAssetDimensionValue(dimension):
            adv.delete()
        for dimVal, value in dimVals:
            portfolio_controller.newAssetDimensionValue(self,dimVal,value)

    def getAssetDimensionValue(self, dim):
        from avernus.controller import portfolio_controller
        assDimVals = portfolio_controller.getAssetDimensionValueForStock(self, dim)
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
        from avernus.controller import portfolio_controller
        portfolio_controller.datasource_manager.update_stock(self)

    def get_price_at_date(self, date):
        from avernus.controller import portfolio_controller
        return portfolio_controller.getPriceFromStockAtDate(self, date)
