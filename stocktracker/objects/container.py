from stocktracker.objects.model import SQLiteEntity
from stocktracker.objects.exchange import Exchange
from stocktracker.objects.stock import Stock
import controller
from stocktracker import updater, pubsub
from datetime import datetime

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
        updater.update_stocks([pos.stock for pos in self])
        self.last_update = datetime.now()
        pubsub.publish("stocks.updated", self)


class Portfolio(SQLiteEntity, Container):

    __primaryKey__ = "id"
    __tableName__ = 'portfolio'
    __columns__ = {
                   "id"  : "INTEGER",
                   "name": "VARCHAR",
                   "last_update": "TIMESTAMP",
                   "comment": "TEXT",
                   "cash": "FLOAT",
                   }
    
    def __iter__(self):
        return controller.getPositionForPortfolio(self).__iter__()
    
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
        last_date = self.transactions[-1].date
        #FIXME should be last day - 1 day
        res.append((date(last_date.year, last_date.month, 1) , cash))
        return res   
    
    @property
    def transactions(self):
        return controller.getTransactionForPortfolio(self)
                    
                   
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
        return controller.getPositionForWatchlist(self).__iter__()


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
                   'exchange': Exchange,
                   'yahoo_symbol': 'VARCHAR',
                   'currency': 'VARCHAR'
                  }
    
    __relations__ = {
                    'positions': Stock,
                    }

    def update_positions(self):
        #update stocks and index
        updater.update_stocks(self.positions+[self]) 
        self.last_update = datetime.now()
        pubsub.publish("stocks.updated", self)
   
    @property      
    def percent(self):
        try: 
            return round(self.change * 100 / (self.price - self.change),2)
        except:
            return 0
