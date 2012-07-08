from avernus.objects.container import PortfolioPosition, WatchlistPosition
from avernus.objects import session, Session
from avernus.controller import asset_controller

import datetime


class MetaPosition():

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
        amount = self.price * self.quantity + get_buy_value(position)
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



def new_watchlist_position(price=0.0, date=datetime.datetime.now(), watchlist=None, asset=None):
    position = WatchlistPosition(price = price,
                                 date = date,
                                 watchlist = watchlist,
                                 asset = asset)
    session.add(position)
    watchlist.emit("position_added", position)
    return position

def new_portfolio_position(price=0.0, date=datetime.datetime.now(), shares=1.0, portfolio=None, asset=None, comment=""):
    position = PortfolioPosition(price = price,
                                 date = date,
                                 quantity = shares,
                                 portfolio = portfolio,
                                 asset = asset,
                                 comment="")
    session.add(position)
    portfolio.emit("position_added", position)
    return position


def get_all_portfolio_position():
    return Session().query(PortfolioPosition).all()

def get_buy_value(position):
    return position.quantity * position.price

def get_days_gain(position):
    return position.asset.change * position.quantity

def get_gain(position):
    if position.asset:
        change = position.asset.price - position.price
    else:
        return 0, 0
    absolute = change * position.quantity
    if position.price * position.quantity == 0:
        percent = 0
    else:
        percent = absolute * 100 / (position.price * position.quantity)
    return absolute, percent

def get_gain_with_dividends(position):
    absolute = get_gain(position)[0]
    absolute += sum([asset_controller.get_total_for_dividend(div) for div in position.dividends])
    percent = absolute * 100 / (position.price * position.quantity)
    return absolute, percent

def get_quantity_at_date(position, t):
    if t < position.date:
        return 0
    q = position.quantity
    for sell_ta in asset_controller.get_sell_transactions(position):
        if t < sell_ta.date:
            q += sell_ta.quantity
    return q


def get_value_at_date(position, t):
    quantity = get_quantity_at_date(position, t)
    if quantity == 0:
        return 0
    t1 = t - datetime.timedelta(days=3)
    price = asset_controller.get_price_at_date(position.asset, t, t1)
    if price:
        return quantity * price
    return 0.0

def get_value_at_daterange(portfolio, asset, days):
    quantity = 0
    delta = datetime.timedelta(days=3)
    transactions = asset_controller.get_transactions(portfolio, asset)
    for day in days:
        # adjust quantity
        while len(transactions)>0 and transactions[0].date <= day:
            ta = transactions.pop(0)
            if ta.type == "portfolio_buy_transaction":
                quantity += ta.quantity
            else:
                quantity -= ta.quantity
        # get price
        if quantity == 0.0:
            yield 0
        else:
            price = asset_controller.get_price_at_date(asset, day, day-delta)
            if price:
                yield quantity * price
            else:
                yield 0

def get_current_value(position):
    return position.quantity * position.asset.price

def get_current_change(position):
    return position.asset.change, asset_controller.get_change_percent(position.asset)
