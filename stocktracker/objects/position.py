from stocktracker.objects.model import SQLiteEntity
from stocktracker.objects.container import Portfolio, Watchlist, Tag
from stocktracker.objects.stock import Stock
from datetime import datetime

 
class Position(object):
    tagstring = ''
    
    @property
    def days_gain(self):
        return self.stock.change * self.quantity
    
    @property
    def gain(self):
        if self.stock:
            stock = self.stock.price - self.price
        else:
            return 0,0
        absolute = stock * self.quantity
        percent = round(absolute * 100 / (self.price*self.quantity),2)
        return absolute, percent

    @property
    def current_change(self):
        if not self.stock:
            return 0,0
        return self.stock.change, round(self.stock.percent,2)
    
    @property    
    def bvalue(self):
        return self.quantity * self.price
    
    @property
    def cvalue(self):
        if not self.stock:
            return 0
        return self.quantity * self.stock.price 
     
    @property
    def name(self):
        if not self.stock:
            return "No Stock"
        return self.stock.name    

   
class PortfolioPosition(SQLiteEntity, Position):
    
    __primaryKey__ = "id"
    __tableName__ = 'portfolioposition'
    __columns__ = {
                   "id": "INTEGER",
                   "date": "TIMESTAMP",
                   "price": "FLOAT",
                   "quantity":  "INTEGER",
                   "portfolio": Portfolio,
                   "stock":     Stock,
                   "comment":   "TEXT"
                   }
    __relations__  = {
                    "tags"       : Tag,
                    }

    @property
    def tagstring(self):
        ret = ''
        for t in self.tags:
            ret += t.name + ' '
        return ret 
    
    def hasTag(self, tag):
        return tag in self.tags
      

    def get_value_over_time(self, start_day, end_day=datetime.today()):
        #transactions on same day!
        #dividends?
        #transaction_costs?
        end_day = end_day.date()
        res = []
        quantity = 0
        one_day = timedelta(days = 1)
        current = start_day
 
        while current <= end_day:
            print current
            price = 1 #FIXME, get price at date
            current += one_day
            for ta in self.transactions:
                if ta.date == current:
                    if ta.type == 0: #sell
                        quantity -= ta.quantity    
                    elif ta.type == 1: #buy
                        quantity += ta.quantity
                    elif ta.type == 2: #split
                        #FIXME handle splits correctly
                        pass
            res.append((current, ta.quantity*price))    
        return res


class WatchlistPosition(SQLiteEntity, Position):

    __primaryKey__ = "id"
    __tableName__ = 'watchlistposition'
    __columns__ = {
                   "id": "INTEGER",
                   "date": "TIMESTAMP",
                   "price": "FLOAT",
                   "watchlist": Watchlist,
                   "stock":     Stock,
                   "comment":   "TEXT"
                   }

    quantity = 1
    #FIXME
    tags_string =''
