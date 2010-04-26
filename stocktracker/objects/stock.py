from stocktracker.objects.model import SQLiteEntity
from stocktracker.objects.exchange import Exchange
from stocktracker import updater


class Stock(SQLiteEntity):

    __primaryKey__ = 'id'
    __tableName__ = "stock"
    __columns__ = {
                   'id': 'INTEGER',
                   'isin': 'VARCHAR',
                   'exchange': Exchange,
                   'type': 'INTEGER',
                   'name': 'VARCHAR',
                   'currency': 'VARCHAR',
                   'yahoo_symbol': 'VARCHAR',
                   'price': 'FLOAT',
                   'date': 'TIMESTAMP',
                   'change': 'FLOAT'
                  }

    #needed for some treeviews, e.g. news_tab
    @property
    def stock(self):
        return self
    
    @property
    def country(self):
        return COUNTRIES[self.isin[0:2].lower()]
                    
    @property      
    def percent(self):
        try: 
            return round(self.change * 100 / (self.price - self.change),2)
        except:
            return 0
    
    def update(self):
        updater.update_stocks([self])
    
    def __str__(self):
        return self.name +' | '+self.isin+' | '+self.exchange.name
