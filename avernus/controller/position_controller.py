from avernus.objects.container import PortfolioPosition, WatchlistPosition
from avernus.objects import session
from avernus.controller import asset_controller

import datetime


def new_watchlist_position(price=0.0, date=datetime.datetime.now(), watchlist=None, asset=None):
    position = WatchlistPosition(price = price,
                                 date = date,
                                 watchlist = watchlist,
                                 asset = asset)
    session.add(position)
    return position

def new_portfolio_position(price=0.0, date=datetime.datetime.now(), shares=1.0, portfolio=None, asset=None):
    position = PortfolioPosition(price = price,
                                 date = date,
                                 quantity = shares,
                                 portfolio = portfolio,
                                 asset = asset)
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
