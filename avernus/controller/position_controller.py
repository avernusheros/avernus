from avernus.objects.container import PortfolioPosition, WatchlistPosition
from avernus.objects import session
from avernus.controller import asset_controller

import datetime


#FIXME find a good place for this type of objects that do not exist in our db
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


def new_watchlist_position(price=0.0, date=datetime.datetime.now(), watchlist=None, asset=None):
    position = WatchlistPosition(price = price,
                                 date = date,
                                 watchlist = watchlist,
                                 asset = asset)
    session.add(position)
    return position

def new_portfolio_position(price=0.0, date=datetime.datetime.now(), shares=1.0, portfolio=None, asset=None, comment=""):
    position = PortfolioPosition(price = price,
                                 date = date,
                                 quantity = shares,
                                 portfolio = portfolio,
                                 asset = asset,
                                 comment="")
    session.add(position)
    return position

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

def get_current_value(position):
    return position.quantity * position.asset.price

def get_current_change(position):
    return position.asset.change, asset_controller.get_change_percent(position.asset)
