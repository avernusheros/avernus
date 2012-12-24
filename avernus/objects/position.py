from avernus import objects
from avernus.objects import asset, portfolio_transaction
from avernus import math
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
import datetime


class PositionBase(object):
    """
    everything used by PortfolioPosition and MetaPosition
    """

    @property
    def gain(self):
        if self.asset:
            change = self.asset.price - self.price
        else:
            return 0, 0
        absolute = change * self.quantity
        if self.price * self.quantity == 0:
            percent = 0
        else:
            percent = absolute / (self.price * self.quantity)
        return absolute, percent

    @property
    def gain_with_dividends(self):
        absolute = self.gain[0]
        absolute += sum([div.total for div in self.dividends])
        percent = absolute / (self.price * self.quantity)
        return absolute, percent

    @property
    def current_value(self):
        return self.quantity * self.asset.price

    @property
    def current_change(self):
        return self.asset.change, self.asset.change_percent

    def get_annual_return(self):
        # get a list of all transactions and dividend payments sorted by date
        transactions = []
        for ta in self.transactions:
            transactions.append((ta.date, ta.total))
        for div in self.dividends:
            transactions.append((div.date, div.total))
        # append current value
        transactions.append((self.asset.date.date(), self.current_value))
        transactions.sort()
        return math.xirr(transactions)


class MetaPosition(PositionBase):

    def __init__(self, position):
        self.asset = position.asset
        self.quantity = position.quantity
        self.price = position.price
        self.date = position.date
        self.portfolio = position.portfolio
        self.positions = [position]

    def add_position(self, position):
        self.positions.append(position)
        self.recalc_values_after_adding(position)

    def recalc_values_after_adding(self, position):
        amount = self.price * self.quantity + position.buy_value
        self.quantity += position.quantity
        self.price = amount / self.quantity
        if position.date < self.date:
            self.date = position.date

    def recalculate(self):
        self.quantity = 0
        self.date = self.positions[0].date
        for position in self.positions:
            self.recalc_values_after_adding(position)

    @property
    def transactions(self):
        for pos in self.positions:
            for ta in pos.transactions:
                yield ta

    @property
    def dividends(self):
        for pos in self.positions:
            for div in pos.dividends:
                yield div

    @property
    def current_value(self):
        return self.quantity * self.asset.price

    @property
    def buy_value(self):
        return self.quantity * self.price

    @property
    def days_gain(self):
        return self.asset.change * self.quantity


class Position(objects.Base, PositionBase):
    __tablename__ = 'position'
    discriminator = Column('type', String(30))
    __mapper_args__ = {'polymorphic_on': discriminator}

    id = Column(Integer, primary_key=True)
    date = Column(Date)
    price = Column(Float)
    comment = Column(String, default='')

    asset_id = Column(Integer, ForeignKey('asset.id'))
    asset = relationship('Asset', backref='positions')

    def __iter__(self):
        return self.positions.__iter__()

    @property
    def buy_value(self):
        return self.quantity * self.price

    @property
    def days_gain(self):
        return self.asset.change * self.quantity

    def get_quantity_at_date(self, t):
        if t < self.date:
            return 0
        q = self.quantity
        for sell_ta in self.get_sell_transactions():
            if t < sell_ta.date:
                q += sell_ta.quantity
        return q

    def get_value_at_date(self, t):
        quantity = self.get_quantity_at_date(self, t)
        if quantity == 0:
            return 0
        t1 = t - datetime.timedelta(days=3)
        price = self.asset.get_price_at_date(t, t1)
        if price:
            return quantity * price
        return 0.0


class PortfolioPosition(Position):
    __tablename__ = 'portfolio_position'
    __mapper_args__ = {'polymorphic_identity': 'portfolioposition'}
    id = Column(Integer, ForeignKey('position.id'), primary_key=True)
    quantity = Column(Float, default=0.0)
    portfolio_id = Column(Integer, ForeignKey('portfolio.id'))
    asset_category_id = Column(Integer, ForeignKey('asset_category.id'))

    # to prevent some warnings
    portfolio = None

    def __init__(self, **kwargs):
        Position.__init__(self, **kwargs)
        self.portfolio.emit("position_added", self)
        self.portfolio.emit("positions_changed")

    def get_buy_transaction(self):
        return objects.session.query(portfolio_transaction.BuyTransaction)\
                            .filter_by(position=self).first()

    def get_sell_transactions(self):
        return objects.Session().query(portfolio_transaction.SellTransaction)\
                        .filter_by(position=self).all()

    def delete(self, *args):
        Position.delete(self)
        self.portfolio.emit("positions_changed")


class WatchlistPosition(Position):
    __tablename__ = 'watchlist_position'
    __mapper_args__ = {'polymorphic_identity': 'watchlistposition'}
    id = Column(Integer, ForeignKey('position.id'), primary_key=True)
    quantity = 1

    watchlist_id = Column(Integer, ForeignKey('watchlist.id'))

    def __init__(self, **kwargs):
        Position.__init__(self, **kwargs)
        self.watchlist.emit("position_added", self)


class ClosedPosition(object):

    def __init__(self, buy_transaction, sell_transaction):
        self.quantity = sell_transaction.quantity
        self.asset = sell_transaction.position.asset
        self.buy_date = buy_transaction.date
        self.sell_date = sell_transaction.date
        self.buy_price = buy_transaction.price
        self.sell_price = sell_transaction.price
        self.buy_cost = buy_transaction.cost / buy_transaction.quantity \
                                * sell_transaction.quantity
        self.sell_cost = sell_transaction.cost
        self.buy_total = self.buy_cost + self.quantity * self.buy_price
        self.sell_total = self.sell_cost + self.quantity * self.sell_price
        self.gain = self.sell_total - self.buy_total
        self.gain_percent = self.gain / self.buy_total


def get_all_portfolio_positions():
    return objects.Session().query(PortfolioPosition).all()


def get_all_used_assets():
    return objects.Session().query(asset.Asset).join(Position).distinct().all()
