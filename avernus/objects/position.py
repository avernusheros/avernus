from avernus import objects
from avernus.objects import asset, portfolio_transaction
from avernus import math
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, asc
from sqlalchemy.orm import relationship, reconstructor
import datetime


class Position(objects.Base):
    __tablename__ = 'position'
    discriminator = Column('type', String(30))
    __mapper_args__ = {'polymorphic_on': discriminator}

    id = Column(Integer, primary_key=True)
    comment = Column(String, default='')

    asset_id = Column(Integer, ForeignKey('asset.id'))
    asset = relationship('Asset', backref='positions')

    def __iter__(self):
        return self.transactions.__iter__()

    @property
    def buy_value(self):
        return self.price

    @property
    def days_gain(self):
        return self.asset.change * self.quantity

    def get_quantity_at_date(self, t):
        if t < self.date:
            return 0.0
        q = 0.0
        for ta in self.transactions:
            if t >= ta.date:
                if ta.type == "portfolio_sell_transaction":
                    q -= ta.quantity
                else:
                    q += ta.quantity
        return q

    def get_value_at_date(self, t):
        quantity = self.get_quantity_at_date(self, t)
        if quantity == 0.0:
            return 0.0
        t1 = t - datetime.timedelta(days=3)
        price = self.asset.get_price_at_date(t, t1)
        if price:
            return quantity * price
        return 0.0

    @property
    def price_per_share(self):
        return self.price / self.quantity

    @property
    def gain(self):
        try:
            change = self.asset.price - self.price_per_share
            absolute = change * self.quantity
            if self.price == 0.0:
                percent = 0.0
            else:
                percent = absolute / self.price
            return absolute, percent
        except:
            return 0.0, 0.0

    @property
    def gain_with_dividends(self):
        absolute = self.gain[0]
        absolute += sum([div.total for div in self.dividends])
        if self.price == 0.0:
            percent = 0.0
        else:
            percent = absolute / self.price
        return absolute, percent

    @property
    def current_value(self):
        try:
            return self.quantity * self.asset.price
        except:
            return 0.0

    @property
    def current_change(self):
        try:
            return self.asset.change, self.asset.change_percent
        except:
            return 0.0, 0.0

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


class PortfolioPosition(Position):
    __tablename__ = 'portfolio_position'
    __mapper_args__ = {'polymorphic_identity': 'portfolioposition'}
    id = Column(Integer, ForeignKey('position.id'), primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolio.id'))

    # to prevent some warnings
    portfolio = None

    @reconstructor
    def _init(self):
        self.recalculate()

    def recalculate(self):
        try:
            self.date = min([ta.date for ta in self])
        except:
            self.date = None
        self.quantity = 0.0
        self.price = 0.0
        self.cost = 0.0

        sold_quantity = 0.0
        for sell_ta in self.get_sell_transactions():
            sold_quantity += sell_ta.quantity

        for buy_ta in self.get_buy_transactions():
            if sold_quantity >= buy_ta.quantity:
                sold_quantity -= buy_ta.quantity
            elif sold_quantity > 0:
                remaining_quantity = buy_ta.quantity - sold_quantity
                sold_quantity = 0
                self.price += buy_ta.price * remaining_quantity / buy_ta.quantity
                self.cost += buy_ta.cost * remaining_quantity / buy_ta.quantity
                self.quantity += remaing_quantity
            else:
                self.price += buy_ta.price
                self.cost += buy_ta.cost
                self.quantity += buy_ta.quantity

    def get_buy_transactions(self):
        return objects.session.query(portfolio_transaction.BuyTransaction)\
                       .filter_by(position=self)\
            .order_by(asc(portfolio_transaction.BuyTransaction.date)).all()

    def get_sell_transactions(self):
        return objects.Session().query(portfolio_transaction.SellTransaction)\
                        .filter_by(position=self)\
                        .order_by(asc(portfolio_transaction.BuyTransaction.date))\
                        .all()

    def delete(self, *args):
        Position.delete(self)
        self.portfolio.emit("positions_changed")


class WatchlistPosition(Position):
    __tablename__ = 'watchlist_position'
    __mapper_args__ = {'polymorphic_identity': 'watchlistposition'}
    id = Column(Integer, ForeignKey('position.id'), primary_key=True)
    date = Column(Date)
    price = Column(Float)
    quantity = 1

    watchlist_id = Column(Integer, ForeignKey('watchlist.id'))

    def __init__(self, **kwargs):
        Position.__init__(self, **kwargs)
        self.watchlist.emit("position_added", self)


class ClosedPosition(object):

    def __init__(self, sell_transaction):
        position = sell_transaction.position
        self.asset = sell_transaction.position.asset
        self.sell_date = sell_transaction.date
        self.quantity = sell_transaction.quantity
        self.sell_price = sell_transaction.price
        self.sell_cost = sell_transaction.cost
        self.sell_total = sell_transaction.total
        self.buy_date = sell_transaction.position.date

        buy_price = 0.0
        buy_quantity = 0.0
        buy_costs = 0.0
        sold_quantity = 0.0
        for sell_ta in position.get_sell_transactions():
            if sell_ta != sell_transaction and sell_ta.date < sell_transaction.date:
                sold_quantity += sell_ta.quantity

        for buy_ta in position.get_buy_transactions():
            # only consider buys before the sell date
            if buy_ta.date <= sell_transaction.date:
                if sold_quantity >= buy_ta.quantity:
                    sold_quantity -= buy_ta.quantity
                elif sold_quantity > 0:
                    remaining_quantity = buy_ta.quantity - sold_quantity
                    sold_quantity = 0
                    buy_price += buy_ta.price * remaining_quantity / buy_ta.quantity
                    buy_costs += buy_ta.cost * remaining_quantity / buy_ta.quantity
                    buy_quantity += remaing_quantity
                else:
                    buy_price += buy_ta.price
                    buy_costs += buy_ta.cost
                    buy_quantity += buy_ta.quantity
        self.buy_price = buy_price / buy_quantity
        self.buy_cost = buy_costs * self.quantity / buy_quantity

        self.buy_total = self.buy_cost + self.quantity * self.buy_price
        self.gain = self.sell_total - self.buy_total
        self.gain_percent = self.gain / self.buy_total


def get_all_portfolio_positions():
    return objects.Session().query(PortfolioPosition).all()


def get_all_used_assets():
    return objects.Session().query(asset.Asset).join(Position).distinct().all()


def get_position(portfolio, asset):
    return objects.Session().query(PortfolioPosition).\
            filter_by(portfolio=portfolio, asset=asset).first()
