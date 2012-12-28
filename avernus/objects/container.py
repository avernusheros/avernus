from avernus import objects
from avernus import math
from avernus.objects import asset as asset_m, position, portfolio_transaction
from gi.repository import GObject
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import reconstructor, relationship
import datetime


class Benchmark(objects.Base):
    __tablename__ = 'benchmark'

    id = Column(Integer, primary_key=True)
    percentage = Column(Float)
    portfolio_id = Column(Integer, ForeignKey('portfolio.id'))
    portfolio = relationship('Portfolio')

    def __str__(self):
        return _('Benchmark ') + str(round(self.percentage * 100, 2)) + "%"


class PortfolioBase(GObject.GObject):
    """
    everything that is used by Portfolio and AllPortfolio
    """

    __gsignals__ = {
        'position_added': (GObject.SIGNAL_RUN_LAST, None, (object,)),
        'positions_changed': (GObject.SIGNAL_RUN_LAST, None, ()),
        'updated': (GObject.SIGNAL_RUN_LAST, None, ())
    }

    def __init__(self, *args, **kwargs):
        GObject.GObject.__init__(self)

    @reconstructor
    def _init(self):
        GObject.GObject.__init__(self)

    @property
    def percent(self):
        return self.current_change[1]

    @property
    def ter(self):
        ter = 0
        val = 0
        for pos in self:
            pos_val = pos.current_value
            ter += pos_val * pos.asset.ter
            val += pos_val
        if val == 0:
            return 0.0
        return ter / val

    @property
    def overall_change(self):
        end = self.get_current_value()
        start = self.get_buy_value()
        absolute = end - start
        if start == 0:
            percent = 0
        else:
            percent = round(100.0 / start * absolute, 2)
        return absolute, percent

    @property
    def current_change(self):
        change = 0.0
        for pos in self:
            stock, percent = pos.current_change
            change += stock * pos.quantity
        start = self.get_current_value() - change
        if start == 0.0:
            percent = 0.0
        else:
            percent = round(100.0 / start * change, 2)
        return change, percent

    @property
    def active_positions_count(self):
        return len(filter(lambda p: p.quantity > 0, self.positions))

    @property
    def transaction_count(self):
        return sum([len(pos.transactions) for pos in self])

    @property
    def date_of_last_dividend(self):
        # FIXME faster, simpler!
        current = None
        for pos in self:
            for dividend in pos.dividends:
                if not current or dividend.date > current:
                    current = dividend.date
        return current

    @property
    def date_of_last_transaction(self):
        current = None
        for pos in self:
            for ta in pos.transactions:
                if not current or ta.date > current:
                    current = ta.date
        return current

    def get_closed_positions(self):
        ret = []
        for pos in self:
            for sell_ta in pos.get_sell_transactions():
                buy_ta = pos.get_buy_transaction()
                ret.append(position.ClosedPosition(buy_ta, sell_ta))
        return ret

    def get_dividends_count(self):
        return sum([len(pos.dividends) for pos in self])

    def get_transactions(self):
        ret = []
        for pos in self:
            ret += pos.transactions
        return ret

    def get_dividends(self):
        ret = []
        for pos in self:
            ret += pos.dividends
        return ret

    def get_dividends_sum(self):
        ret = 0.0
        for pos in self:
            ret += sum([div.price for div in pos.dividends])
        return ret

    def get_used_assets(self):
        return objects.Session().query(asset_m.Asset)\
                       .join(position.PortfolioPosition)\
                       .filter(position.PortfolioPosition.portfolio == self)\
                       .distinct()\
                       .all()

    def get_current_value(self):
        value = 0.0
        for pos in self:
            value += pos.current_value
        return value

    def get_annual_return(self):
        # get a list of all transactionsm and dividend payments sorted by date
        transactions = []
        for position in self.positions:
            for ta in position.transactions:
                transactions.append((ta.date, ta.total))
            for div in position.dividends:
                transactions.append((div.date, div.total))
        # append current value
        if self.last_update:
            transactions.append((self.last_update.date(),
                                 self.get_current_value()))
        transactions.sort()
        return math.xirr(transactions)

    def get_birthday(self):
        current = datetime.date.today()
        for position in self.positions:
            for transaction in position.transactions:
                if transaction.date < current:
                    current = transaction.date
        return current

    def get_fraction(self, position):
        cvalue = self.get_current_value()
        if cvalue == 0:
            return 0.0
        else:
            return position.current_value / cvalue

    def get_buy_value(self):
        value = 0.0
        for pos in self:
            value += pos.buy_value
        return value

GObject.type_register(PortfolioBase)


class AllPortfolio(PortfolioBase):

    name = _("All")
    # FIXME dont use portfolio id for progress monitor
    id = 1233312

    def __iter__(self):
        return self.positions.__iter__()

    @property
    def positions(self):
        return position.get_all_portfolio_positions()

    @property
    def last_update(self):
        try:
            return min([pf.last_update for pf in get_all_portfolios()])
        except:
            return None

    @last_update.setter
    def last_update(self, value):
        for pf in get_all_portfolios():
            pf.last_update = value

    def get_current_value(self):
        value = 0.0
        for pos in self:
            value += pos.current_value
        return value


class Container(objects.Base):
    __tablename__ = 'container'
    discriminator = Column('type', String(30))
    __mapper_args__ = {'polymorphic_on': discriminator}

    id = Column(Integer, primary_key=True)
    name = Column(String)
    last_update = Column(DateTime)

    def __iter__(self):
        return self.positions.__iter__()


class Portfolio(Container, PortfolioBase):
    __tablename__ = 'portfolio'
    __mapper_args__ = {'polymorphic_identity': 'portfolio'}
    id = Column(Integer, ForeignKey('container.id'), primary_key=True)
    positions = relationship('PortfolioPosition',
                            backref='portfolio', cascade="all,delete")

    def __iter__(self):
        return self.positions.__iter__()

    def get_transactions_for_asset(self, asset):
        return objects.Session().query(portfolio_transaction.Transaction)\
                       .join(position.PortfolioPosition)\
                       .filter(position.PortfolioPosition.portfolio == self,
                               position.Position.asset == asset)\
                       .order_by(portfolio_transaction.Transaction.date).all()

    def get_benchmarks(self):
        return objects.Session().query(Benchmark)\
                    .filter_by(portfolio=self).all()

    def get_value_at_daterange(self, asset, days):
        quantity = 0
        delta = datetime.timedelta(days=3)
        transactions = self.get_transactions_for_asset(asset)
        for day in days:
            # adjust quantity
            while transactions and transactions[0].date <= day:
                ta = transactions.pop(0)
                if ta.type == "portfolio_buy_transaction":
                    quantity += ta.quantity
                else:
                    quantity -= ta.quantity
            # get price
            if not quantity:
                yield 0
            else:
                price = asset.get_price_at_date(day, day - delta)
                if price:
                    yield quantity * price
                else:
                    yield 0


class Watchlist(Container, GObject.GObject):
    __tablename__ = 'watchlist'
    __mapper_args__ = {'polymorphic_identity': 'watchlist'}
    id = Column(Integer, ForeignKey('container.id'), primary_key=True)
    positions = relationship('WatchlistPosition',
                    backref='watchlist', cascade="all,delete")

    __gsignals__ = {
        'position_added': (GObject.SIGNAL_RUN_LAST, None, (object,)),
        'positions_changed': (GObject.SIGNAL_RUN_LAST, None, ()),
        'updated': (GObject.SIGNAL_RUN_LAST, None, ())
    }

    def __init__(self, *args, **kwargs):
        GObject.GObject.__init__(self)

    @reconstructor
    def _init(self):
        GObject.GObject.__init__(self)

GObject.type_register(Watchlist)


def get_all_portfolios():
    return objects.Session().query(Portfolio).all()


def get_all_watchlists():
    return objects.session.query(Watchlist).all()
