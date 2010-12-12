from avernus.objects.model import SQLiteEntity
from avernus.objects.sector import Sector

import datetime

FUND  = 0
STOCK = 1
ETF   = 2


class Stock(SQLiteEntity):
    __primaryKey__ = 'id'
    __tableName__ = "stock"
    __columns__ = {
                   'id': 'INTEGER',
                   'isin': 'VARCHAR',
                   'type': 'INTEGER',
                   'name': 'VARCHAR',
                   'sector': Sector,
                   'exchange': 'VARCHAR',
                   'currency': 'VARCHAR',
                   'price': 'FLOAT',
                   'date': 'TIMESTAMP',
                   'change': 'FLOAT',
                   'source': 'VARCHAR'
                  }
    __comparisonPositives__ = ['isin', 'currency']
    __defaultValues__ = {
                         'exchange':None,
                         'currency':'',
                         'price':0.0,
                         'date':datetime.datetime.utcnow(),
                         'change':0.0,
                         'type':1,
                         'name':'',
                         'sector':None,
                         'isin':''
                         }

    #needed for some treeviews, e.g. news_tab
    @property
    def stock(self):
        return self

    @property
    def percent(self):
        try:
            return round(self.change * 100 / (self.price - self.change),2)
        except:
            return 0

    def __str__(self):
        return self.name +' | '+self.isin+' | '+self.exchange

    def update_price(self):
        self.controller.datasource_manager.update_stock(self)