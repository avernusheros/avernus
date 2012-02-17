from avernus.objects import model
from avernus.objects.stock import Stock
from avernus.objects.container import Portfolio, Watchlist
from avernus.objects.position import PortfolioPosition, WatchlistPosition
from avernus.objects.dividend import Dividend
from avernus.objects.transaction import Transaction
from avernus.objects.quotation import Quotation
from avernus.objects.dimension import Dimension, DimensionValue, \
    AssetDimensionValue

import datetime
import sys

datasource_manager = None
initialLoadingClasses = [Transaction, Portfolio, Dividend, Watchlist, \
                        PortfolioPosition, WatchlistPosition, Dimension, \
                        DimensionValue, AssetDimensionValue]
controller = sys.modules[__name__]


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


def getDividendsForPosition(pos):
    return Dividend.getAllFromOneColumn("position", pos.getPrimaryKey())


def getTransactionsForPosition(position):
    return Transaction.getAllFromOneColumn("position", position.getPrimaryKey())


def deleteAllPositionTransaction(position):
    for trans in getTransactionsForPosition(position):
        trans.delete()


def deleteAllPositionDividend(position):
    for d in getDividendsForPosition(position):
        d.delete()


def deleteAllAssetDimensionValue(dimvalue):
    for adm in AssetDimensionValue.getAll():
        if adm.dimensionValue == dimvalue:
            adm.delete()


def deleteAllQuotationsFromStock(stock):
    query = """
    DELETE FROM quotation
    WHERE stock = ?
    """
    model.store.execute(query, [stock.id])


def getPositionForWatchlist(watchlist):
    key = watchlist.getPrimaryKey()
    return WatchlistPosition.getAllFromOneColumn("watchlist", key)


def getAllDimensionValueForDimension(dim):
    for value in DimensionValue.getAll():
        if value.dimension == dim:
            yield value


def deleteAllDimensionValue(dimension):
    for val in getAllDimensionValueForDimension(dimension):
        deleteAllAssetDimensionValue(val)
        val.delete()


def deleteAllWatchlistPosition(watchlist):
    for pos in getPositionForWatchlist(watchlist):
        pos.delete()


def getQuotationsFromStock(stock, start=None):
    args = {'stock': stock.getPrimaryKey(), 'exchange':stock.exchange}
    erg = Quotation.getByColumns(args, create=True)
    if start:
        erg = filter(lambda quote: quote.date > start, erg)
    erg = sorted(erg, key=lambda stock: stock.date)
    return erg



def newPortfolio(name, pf_id=None, last_update=datetime.datetime.now(), comment=""):
    result = Portfolio(id=pf_id, name=name, last_update=last_update, comment=comment)
    result.controller = controller
    result.insert()
    return result

def newWatchlist(name, wl_id=None, last_update=datetime.datetime.now(), comment=""):
    result = Watchlist(id=wl_id, name=name, last_update=last_update, comment=comment)
    result.controller = controller
    result.insert()
    return result


def getPriceFromStockAtDate(stock, date):
    args = {'stock': stock.id, 'date':date.date()}
    res = Quotation.getByColumns(args, create=False)
    for item in res:
        return item[5]
    return None

def getAllQuotationsFromStock(stock, start=None):
    """from all exchanges"""
    erg = Quotation.getByColumns({'stock': stock.id}, create=True)
    return sorted(erg, key=lambda stock: stock.date)

def getNewestQuotation(stock):
    key = stock.getPrimaryKey()
    erg = Quotation.getAllFromOneColumn("stock", key)
    if len(erg) == 0:
        return None
    else:
        return erg[0].date

def getBuyTransaction(portfolio_position):
    for ta in Transaction.getByColumns({'position': portfolio_position.id, 'type':1}, create=True):
        return ta

def yieldSellTransactions(portfolio_position):
    for ta in Transaction.getByColumns({'position': portfolio_position.id, 'type':0}, create=True):
        yield ta
