from avernus.objects.model import SQLiteEntity
from avernus.objects.stock import Stock
from avernus import pubsub

from datetime import datetime, date


class Container(object):

    def __len__(self):
        count = 0
        for pos in self:
            count+=1
        return count

    @property
    def ter(self):
        ter = 0
        val = 0
        for pos in self:
            pos_val = pos.cvalue
            ter+=pos_val*pos.stock.ter
            val+=pos_val
        if val==0:
            return 0.0
        return ter/val

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
    def amount(self):
        return self.cvalue

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
        self.controller.datasource_manager.update_stocks([pos.stock for pos in self if pos.quantity>0])
        self.last_update = datetime.now()
        pubsub.publish("stocks.updated", self)
        yield 1


class PortfolioBase(Container):
    
    container_type = 'portfolio'
    
    def get_value_at_date(self, t):
        #FIXME
        #does not consider sold positions
        return sum(pos.get_value_at_date(t) for pos in self if t>pos.date)

    @property
    def transactions(self):
        for pos in self:
            for ta in pos.transactions:
                yield ta

    @property
    def closed_positions(self):
        for tran in self.transactions:
            if tran.is_sell():
                yield ClosedPosition(tran)

    @property
    def dividends(self):
        for pos in self:
            for div in pos.dividends:
                yield div

    @property
    def dividends_count(self):
        return sum(1 for div in self.dividends)

    @property
    def dividends_sum(self):
        return sum(div.total for div in self.dividends)

    @property
    def date_of_last_dividend(self):
        if self.dividends_count == 0:
            return None
        return max(div.date for div in self.dividends)

    @property
    def birthday(self):
        return min(t.date for t in self.transactions)
    

class Portfolio(SQLiteEntity, PortfolioBase):

    __primaryKey__ = "id"
    __tableName__ = 'portfolio'
    __columns__ = {
                   "id"  :          "INTEGER",
                   "name":          "VARCHAR",
                   "last_update":   "TIMESTAMP",
                   "comment":       "TEXT",
                   }

    def __iter__(self):
        return self.controller.getPositionForPortfolio(self).__iter__()

    def onUpdate(self, **kwargs):
        pubsub.publish('container.updated', self)

    def onDelete(self, **kwargs):
        for trans in self.transactions:
            trans.delete()
        for pos in self:
            pos.delete()

    __callbacks__ = {
                     'onUpdate':onUpdate,
                     #'onInsert':onInsert,
                     'onDelete':onDelete,
                     #'onRemoveRelationEntry':onRemoveRelationEntry,
                     #'onAddRelationEntry':onAddRelationEntry,
                     #'onRetrieveComposite':onRetrieveComposite,
                     }


class AllPortfolio(PortfolioBase):
    name = ''
    __name__ = 'Portfolio'
    
    def __iter__(self):
        return self.controller.getAllPosition().__iter__()
    
    @property
    def last_update(self):
        return min([pf.last_update for pf in self.controller.getAllPortfolio()])
        

class Watchlist(SQLiteEntity, Container):

    __primaryKey__ = 'id'
    __tableName__ = "watchlist"
    __columns__ = {
                   'id': 'INTEGER',
                   'name': 'VARCHAR',
                   'last_update':'TIMESTAMP',
                   'comment':'TEXT',
                  }
    container_type = 'watchlist'

    def __iter__(self):
        return self.controller.getPositionForWatchlist(self).__iter__()

    def onDelete(self, **kwargs):
        for pos in self:
            pos.delete()

    __callbacks__ = {
                     'onDelete':onDelete,
                     }


class ClosedPosition(object):

    def __init__(self, sell_transaction):
        position = sell_transaction.position
        buy_transaction = position.buy_transaction
        self.quantity = sell_transaction.quantity
        self.buy_date = buy_transaction.date
        self.buy_price = buy_transaction.price
        self.buy_costs = buy_transaction.costs * self.quantity / buy_transaction.quantity
        self.buy_total = self.quantity*self.buy_price + self.buy_costs
        self.sell_date = sell_transaction.date
        self.sell_price = sell_transaction.price
        self.sell_costs = sell_transaction.costs
        self.sell_total = sell_transaction.total
        self.gain = self.sell_total - self.buy_total
        self.gain_percent = round(self.gain*100 / self.buy_total, 2)
        self.name = position.name
        self.type = sell_transaction.type
        self.stock = position.stock
