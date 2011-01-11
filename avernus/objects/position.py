from avernus.objects.model import SQLiteEntity
from avernus.objects.container import Portfolio, Watchlist
from avernus.objects.stock import Stock
import datetime


class Position(object):

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
        if self.price * self.quantity == 0:
            percent = 0
        else:
            percent = absolute * 100 / (self.price*self.quantity)
        return absolute, percent

    @property
    def current_change(self):
        if not self.stock:
            return 0,0
        return self.stock.change, self.stock.percent

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

    @property
    def portfolio_fraction(self):
        if self.portfolio.cvalue == 0:
            return 0
        else:
            return 100 * self.cvalue / self.portfolio.cvalue


class PortfolioPosition(SQLiteEntity, Position):

    __primaryKey__ = "id"
    __tableName__ = 'portfolioposition'
    __columns__ = {
                   "id": "INTEGER",
                   "date": "TIMESTAMP",
                   "price": "FLOAT",
                   "quantity": "INTEGER",
                   "portfolio": Portfolio,
                   "stock": Stock,
                   "comment": "TEXT"
                   }

    def onDelete(self, **kwargs):
        self.controller.deleteAllPositionTransaction(self)

    __callbacks__ = {
                     'onDelete':onDelete
                     }

    @property
    def buy_transaction(self):
        return self.controller.getBuyTransaction(self)

    @property
    def dividends(self):
        for div in self.controller.getDividendForPosition(self):
            yield div

    def get_value_over_time(self, start_day, end_day=datetime.datetime.today()):
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
                        pass
            res.append((current, ta.quantity*price))
        return res

    def get_value_at_date(self, t):
        # this will on purpose ignore any transactions and assume the current
        # quantity is the all-true one
        i=1
        price = self.controller.getPriceFromStockAtDate(self.stock, t)
        while not price and i<4:
            t -= datetime.timedelta(days = i)
            price = self.controller.getPriceFromStockAtDate(self.stock, t)
            i+=1
        if price:
            return self.quantity*price
        return 0.0


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


class MetaPosition(Position):

    def __init__(self, position):
        self.stock = position.stock
        self.quantity = position.quantity
        self.price = position.price
        self.date = position.date
        self.portfolio = position.portfolio
        self.positions = [position]

    def add_position(self, position):
        self.positions.append(position)
        self._recalc_values_after_adding(position)

    def _recalc_values_after_adding(self, position):
        amount = self.price*self.quantity + position.bvalue
        self.quantity += position.quantity
        self.price = amount / self.quantity
        if position.date < self.date:
            self.date = position.date

    def recalculate(self):
        self.quantity = 0
        self.date = self.positions[0].date
        for position in self.positions:
            self._recalc_values_after_adding(position)
