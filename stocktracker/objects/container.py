from stocktracker.objects.model import SQLiteEntity
from stocktracker.objects.stock import Stock
#FIXME why does the following import give an error
#from stocktracker.objects import controller
import stocktracker.objects.controller
from stocktracker import pubsub

from datetime import datetime, date


class Container(object):

    tagstring = ''
    
    @property
    def bvalue(self):
        value = 0.0
        for pos in self:
            value += pos.bvalue
        return value
    
    @property
    def cvalue(self):
        value = 0.0
        for pos in self:
            value += pos.cvalue
        return value
    
    @property
    def price(self):
        return self.cvalue
    
    @property
    def date(self):
        return self.last_update
        
    @property
    def change(self):
        return self.current_change[0]    
    
    @property
    def percent(self):
        return self.current_change[1]
    
    @property
    def overall_change(self):
        end = self.cvalue
        start = self.bvalue
        absolute = end - start
        if start == 0:
            percent = 0
        else:
            percent = round(100.0 / start * absolute,2)
        return absolute, percent 
    
    @property
    def current_change(self):
        change = 0.0
        for pos in self:
            stock, percent = pos.current_change
            change +=stock * pos.quantity
        start = self.cvalue - change
        if start == 0.0:
            percent = 0
        else:
            percent = round(100.0 / start * change,2)
        return change, percent 
     
    def update_positions(self):
        stocktracker.objects.controller.datasource_manager.update_stocks([pos.stock for pos in self])
        self.last_update = datetime.now()
        pubsub.publish("stocks.updated", self)


class Portfolio(SQLiteEntity, Container):

    __primaryKey__ = "id"
    __tableName__ = 'portfolio'
    __columns__ = {
                   "id"  :          "INTEGER",
                   "name":          "VARCHAR",
                   "last_update":   "TIMESTAMP",
                   "comment":       "TEXT",
                   "cash":          "FLOAT",
                   }
    
    def __iter__(self):
        return stocktracker.objects.controller.getPositionForPortfolio(self).__iter__()
    
    def get_cash_over_time(self):
        cash = self.cash
        res = []
        for ta in self.transactions:
            if ta.type == 1 or ta.type == 4:
                res.append((ta.date.date(), cash))
                cash += ta.quantity*ta.price+ta.ta_costs
            if ta.type == 2 or ta.type == 3 or ta.type == 10:
                res.append((ta.date.date(), cash))
                cash -= ta.quantity*ta.price-ta.ta_costs
        if len(self.transactions)>0:
            last_date = self.transactions[-1].date
            #FIXME should be last day - 1 day
            res.append((date(last_date.year, last_date.month, 1) , cash))
        return res
    
    def get_value_at_date(self, t):
        erg = 0
        for po in stocktracker.objects.controller.getPositionForPortfolio(self):
            if t > po.date.date():
                erg += po.get_value_at_date(t)
        return erg
    
    @property
    def transactions(self):
        return stocktracker.objects.controller.getTransactionForPortfolio(self)
        
    def birthday(self):
        current = date.today()
        for ta in self.transactions:
            if ta.date.date() < current:
                current = ta.date.date()
        return current
        
    def onUpdate(self, **kwargs):
        pubsub.publish('container.updated', self)
        
    def onInsert(self, **kwargs):
        pass
        
    def onDelete(self, **kwargs):
        stocktracker.objects.controller.deleteAllPortfolioPosition(self)
        stocktracker.objects.controller.deleteAllPortfolioTransaction(self)
        
    def onRemoveRelationEntry(self, **kwargs):
        pass
        
    def onAddRelationEntry(self, **kwargs):
        pass
        
    def onRetrieveComposite(self, **kwargs):
        pass
    
    __callbacks__ = {
                     'onUpdate':onUpdate,
                     'onInsert':onInsert,
                     'onDelete':onDelete,
                     'onRemoveRelationEntry':onRemoveRelationEntry,
                     'onAddRelationEntry':onAddRelationEntry,
                     'onRetrieveComposite':onRetrieveComposite,
                     }
                    
                   
class Watchlist(SQLiteEntity, Container):

    __primaryKey__ = 'id'
    __tableName__ = "watchlist"
    __columns__ = {
                   'id': 'INTEGER',
                   'name': 'VARCHAR',
                   'last_update':'TIMESTAMP',
                   'comment':'TEXT',
                  }
    
    def __iter__(self):
        return stocktracker.objects.controller.getPositionForWatchlist(self).__iter__()
    
    def onDelete(self, **kwargs):
        stocktracker.objects.controller.deleteAllWatchlistPosition(self)
        
    __callbacks__ = {
                     'onDelete':onDelete,
                     }


class Index(SQLiteEntity):

    __primaryKey__ = 'id'
    __tableName__ = "indices"
    __columns__ = {
                   'id': 'INTEGER',
                   'name': 'VARCHAR',
                   'isin': "VARCHAR",
                   'change': 'FLOAT',
                   'price': 'FLOAT',
                   'date': 'TIMESTAMP',
                   'exchange': "VARCHAR",
                   'yahoo_symbol': 'VARCHAR',
                   'currency': 'VARCHAR'
                  }
    
    __relations__ = {
                    'positions': Stock,
                    }
    __comparisonPositives__ = ['name']
    __defaultValues__ = {
                         'date':datetime.now(),
                         'isin':'',
                         'change':0.0,
                         'price':0.0,
                         }
    
    def update_positions(self):
        #update stocks and index
        updater.update_stocks(self.positions+[self]) 
        self.last_update = datetime.now()
        pubsub.publish("stocks.updated", self)
   
    def onInit(self, **kwargs):
        pubsub.publish('index.created', self)
    __callbacks__ = {'onInit':onInit}
   
    @property      
    def percent(self):
        try: 
            return round(self.change * 100 / (self.price - self.change),2)
        except:
            return 0

    def __iter__(self):
        for pos in self.positions:
            yield pos
    

class Tag(SQLiteEntity, Container):

    __primaryKey__ = 'id'
    __tableName__ = "tag"
    __columns__ = {
                   'id': 'INTEGER',
                   'name': 'VARCHAR',
                  }
    __comparisonPositives__ = ['name']

    def onInit(self, **kwargs):
        pubsub.publish('tag.created', self)
    __callbacks__ = {'onInit':onInit}
    
    def __iter__(self):
        return stocktracker.objects.controller.getPositionForTag(self).__iter__()

    @property
    def date(self):
        return None
