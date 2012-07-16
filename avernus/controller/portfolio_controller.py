from avernus.objects import Portfolio, Watchlist, Benchmark
from avernus.objects import session, Session
from avernus.controller import position_controller, asset_controller
from avernus.controller.object_controller import delete_object
from avernus import math

from gi.repository import GObject
from . import dsm

import datetime


class AllPortfolio(GObject.GObject):

    __gsignals__ = {
        'position_added': (GObject.SIGNAL_RUN_LAST, None,
                      (object,))
    }

    def __iter__(self):
        return self.positions.__iter__()

    @property
    def positions(self):
        return position_controller.get_all_portfolio_position()

    @property
    def last_update(self):
        return min([pf.last_update for pf in get_all_portfolio()])

    @last_update.setter
    def last_update(self, value):
        for pf in get_all_portfolio():
            pf.last_update = value


class ClosedPosition:

    def __init__(self, buy_transaction, sell_transaction):
        self.quantity = sell_transaction.quantity
        self.asset = sell_transaction.position.asset
        self.buy_date = buy_transaction.date
        self.sell_date = sell_transaction.date
        self.buy_price = buy_transaction.price
        self.sell_price = sell_transaction.price
        self.buy_cost = buy_transaction.cost / buy_transaction.quantity * sell_transaction.quantity
        self.sell_cost = sell_transaction.cost
        self.buy_total = self.buy_cost + self.quantity * self.buy_price
        self.sell_total = self.sell_cost + self.quantity * self.sell_price
        self.gain = self.sell_total - self.buy_total
        self.gain_percent = self.gain / self.buy_total


def delete_position(position):
    session.delete(position)
    session.commit()

def new_portfolio(name):
    pf = Portfolio(name=name)
    session.add(pf)
    return pf

def new_watchlist(name):
    wl = Watchlist(name=name)
    session.add(wl)
    return wl

def new_benchmark(portfolio, percentage):
    bm = Benchmark(portfolio=portfolio, percentage=percentage)
    session.add(bm)
    return bm

def get_all_portfolio():
    return session.query(Portfolio).all()

def get_all_watchlist():
    return session.query(Watchlist).all()

def get_current_value(portfolio):
    value = 0.0
    for pos in portfolio:
        value += position_controller.get_current_value(pos)
    return value

def get_benchmarks_for_portfolio(portfolio):
    return Session().query(Benchmark).filter_by(portfolio=portfolio).all()

def get_birthday(portfolio):
    current = datetime.date.today()
    for position in portfolio.positions:
        for transaction in position.transactions:
            if transaction.date < current:
                current = transaction.date
    return current

def get_buy_value(portfolio):
    value = 0.0
    for pos in portfolio:
        value += position_controller.get_buy_value(pos)
    return value

def get_fraction(portfolio, position):
    cvalue = get_current_value(portfolio)
    if cvalue == 0:
        return 0.0
    else:
        return position_controller.get_current_value(position) / cvalue

def get_annual_return(portfolio):
    # get a list of all transactionsm and dividend payments sorted by date
    transactions = []
    for position in portfolio.positions:
        for ta in position.transactions:
            transactions.append((ta.date, asset_controller.get_total_for_transaction(ta)))
        for div in position.dividends:
            transactions.append((div.date, asset_controller.get_total_for_dividend(div)))
    # append current value
    transactions.append((portfolio.last_update.date(), get_current_value(portfolio)))
    transactions.sort()
    return math.xirr(transactions)


def get_closed_positions(portfolio):
    ret = []
    for position in portfolio:
        for sell_ta in asset_controller.get_sell_transactions(position):
            buy_ta = asset_controller.get_buy_transaction(position)
            ret.append(ClosedPosition(buy_ta, sell_ta))
    return ret

def get_current_change(portfolio):
    change = 0.0
    for pos in portfolio:
        stock, percent = position_controller.get_current_change(pos)
        change += stock * pos.quantity
    start = get_current_value(portfolio) - change
    if start == 0.0:
        percent = 0.0
    else:
        percent = round(100.0 / start * change, 2)
    return change, percent

def get_date_of_last_dividend(pf):
    current = None
    for pos in pf:
        for dividend in pos.dividends:
            if not current or dividend.date > current:
                current = dividend.date
    return current

def get_date_of_last_transaction(pf):
    current = None
    for pos in pf:
        for ta in pos.transactions:
            if not current or ta.date > current:
                current = ta.date
    return current

def get_transaction_count(pf):
    return sum([len(pos.transactions) for pos in pf])

def get_dividends(portfolio):
    ret = []
    for pos in portfolio:
        ret += pos.dividends
    return ret

def get_dividends_count(portfolio):
    return sum([len(pos.dividends) for pos in portfolio])

def get_dividends_sum(portfolio):
    ret = 0.0
    for pos in portfolio:
        ret += sum([div.price for div in pos.dividends])
    return ret

def get_overall_change(portfolio):
    end = get_current_value(portfolio)
    start = get_buy_value(portfolio)
    absolute = end - start
    if start == 0:
        percent = 0
    else:
        percent = round(100.0 / start * absolute, 2)
    return absolute, percent

def get_percent(portfolio):
    return get_current_change(portfolio)[1]

def get_ter(portfolio):
    ter = 0
    val = 0
    for pos in portfolio:
        pos_val = position_controller.get_current_value(pos)
        ter += pos_val * asset_controller.get_ter(pos)
        val += pos_val
    if val == 0:
        return 0.0
    return ter / val

def get_transactions(portfolio):
    ret = []
    for pos in portfolio:
        ret += pos.transactions
    return ret

def update_positions(portfolio):
    items = set(pos.asset for pos in portfolio if pos.quantity > 0)
    itemcount = len(items)
    count = 0.0
    for item in dsm.update_assets(items):
        count += 1.0
        yield count / itemcount
    portfolio.last_update = datetime.datetime.now()
    #pubsub.publish("stocks.updated", self)
    yield 1
