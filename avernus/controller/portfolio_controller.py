from avernus.objects import model
from avernus.objects.stock import Stock
from avernus.objects.container import Portfolio, Watchlist
from avernus.objects.position import PortfolioPosition, WatchlistPosition


import datetime

datasource_manager = None
initialLoadingClasses = [Portfolio]


def getAllPortfolio():
    return Portfolio.getAll()


def getAllWatchlist():
    return Watchlist.getAll()


def getAllPosition():
    return PortfolioPosition.getAll()


def getPositionForPortfolio(portfolio):
    return PortfolioPosition.getAllFromOneColumn("portfolio", portfolio.getPrimaryKey())


def update_historical_prices():
    stocks = get_all_used_stocks()
    l = len(stocks)
    i = 0.0
    for st in stocks:
        for qt in datasource_manager.get_historical_prices(st):
            yield i / l
        i += 1.0
        yield i / l
    yield 1


def get_all_used_stocks():
    query = """
    select distinct stock from portfolioposition
    union
    select distinct stock from watchlistposition
    """
    return [Stock.getByPrimaryKey(stockid[0]) for stockid in model.store.select(query)]


def update_all():
    for ret in datasource_manager.update_stocks(get_all_used_stocks()):
        yield 0
    for container in getAllPortfolio() + getAllWatchlist():
        container.last_update = datetime.datetime.now()
    yield 1
