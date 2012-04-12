from avernus.objects.container import PortfolioPosition, WatchlistPosition
from avernus.objects import session

def new_watchlist_position(price, date, watchlist, asset):
    position = WatchlistPosition(price = price,
                                 date = date,
                                 watchlist = watchlist,
                                 asset = asset)
    session.add(position)
    return position

def new_portfolio_position(price, date, shares, portfolio, asset):
    position = PortfolioPosition(price = price,
                                 date = date,
                                 quantity = shares,
                                 portfolio = portfolio,
                                 asset = asset)
    session.add(position)
    return position

def get_buy_value(position):
    return position.quantity * position.price

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
    return position.asset.change, position.asset.percent
