from avernus.objects import model
from avernus.objects.stock import Stock
from avernus.objects.container import Portfolio, Watchlist
from avernus.objects.position import PortfolioPosition, WatchlistPosition
from avernus.objects.source_info import SourceInfo
from avernus.objects.transaction import Transaction
from avernus.objects.quotation import Quotation
from avernus.objects.dimension import Dimension, DimensionValue, \
    AssetDimensionValue
from avernus.controller.shared import check_duplicate, detect_duplicate
from avernus.controller import position_controller

# sqlalchemy version
from avernus.objects import session


import datetime
import sys

datasource_manager = None
initialLoadingClasses = []
controller = sys.modules[__name__]


def getAllPortfolio():
    return session.query(Portfolio).all()


def getAllWatchlist():
    return session.query(Watchlist).all()

def get_current_value(portfolio):
    value = 0.0
    for pos in portfolio:
        value += pos.cvalue
    return value

def get_buy_value(portfolio):
    value = 0.0
    for pos in portfolio:
        value += position_controller.get_buy_value()
    return value

def get_current_change(portfolio):
    return 0.1, 0.2

def get_overall_change(portfolio):
    end = get_current_value(portfolio)
    start = get_buy_value(portfolio)
    absolute = end - start
    if start == 0:
        percent = 0
    else:
        percent = round(100.0 / start * absolute, 2)
    return absolute, percent




# Mordor from here



def getAllPosition():
    return PortfolioPosition.getAll()


def getPositionForPortfolio(portfolio):
    return PortfolioPosition.getAllFromOneColumn("portfolio", portfolio.getPrimaryKey())

def getBenchmarksForPortfolio(portfolio):
    return Benchmark.getAllFromOneColumn("portfolio", portfolio.getPrimaryKey())

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
    items = set()
    for pf in getAllPortfolio():
        for pos in pf:
            if pos.quantity > 0:
                items.add(pos.stock)
    for wl in getAllWatchlist():
        for pos in wl:
            items.add(pos.stock)
    return items

def update_all():
    items = get_all_used_stocks()
    itemcount = len(items)
    count = 0.0
    for item in datasource_manager.update_stocks(items):
        count += 1.0
        yield count / itemcount
    for container in getAllPortfolio() + getAllWatchlist():
        container.last_update = datetime.datetime.now()
    pubsub.publish("stocks.updated", self)
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
    args = {'stock': stock.getPrimaryKey()}
    erg = Quotation.getByColumns(args, create=True)
    if start:
        erg = filter(lambda quote: quote.date > start, erg)
    erg = sorted(erg, key=lambda stock: stock.date)
    return erg


def newPortfolio(name, pf_id=None, last_update=datetime.datetime.now()):
    result = Portfolio(id=pf_id, name=name, last_update=last_update)
    session.add(result)
    return result

def newWatchlist(name, wl_id=None, last_update=datetime.datetime.now()):
    result = Watchlist(id=wl_id, name=name, last_update=last_update)
    session.add(result)
    return result

def getAssetDimensionValueForStock(stock, dim):
    stockADVs = AssetDimensionValue.getAllFromOneColumn('stock', stock.id)
    #for adv in stockADVs:
    #    print adv, adv.dimensionValue
    stockADVs = filter(lambda adv: adv.dimensionValue.dimension == dim, stockADVs)
    return stockADVs

def newAssetDimensionValue(stock, dimensionValue, value):
    adv = detect_duplicate(AssetDimensionValue, stock=stock.id, dimensionValue=dimensionValue.id,
                          value=value)
    return adv


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


def getBuyTransaction(portfolio_position):
    for ta in Transaction.getByColumns({'position': portfolio_position.id, 'type':1}, create=True):
        return ta

def yieldSellTransactions(portfolio_position):
    for ta in Transaction.getByColumns({'position': portfolio_position.id, 'type':0}, create=True):
        yield ta


def newStock(insert=True, **kwargs):
    result = Stock(**kwargs)
    result.controller = controller
    if insert:
        result.insert()
    return result

def newBenchmark(portfolio, percentage):
    bm = Benchmark(id=None,portfolio = portfolio.id, percentage = percentage)
    bm.insert()
    return bm

def newWatchlistPosition(price=0, \
                         date=datetime.datetime.now(), \
                         quantity=1, \
                         watchlist=None, \
                         stock=None, \
                         comment=''\
                         ):
    result = WatchlistPosition(id=None, \
                               price=price, \
                               date=date, \
                               watchlist=watchlist, \
                               stock=stock, \
                               comment=comment\
                               )
    result.insert()
    return result

def newPortfolioPosition(price=0, \
                         date=datetime.datetime.now(), \
                         quantity=1, \
                         portfolio=None, \
                         stock=None, \
                         comment=''\
                         ):
    result = PortfolioPosition(id=None, \
                               price=price, \
                               date=date, \
                               quantity=quantity, \
                               portfolio=portfolio, \
                               stock=stock, \
                               comment=comment\
                               )
    result.controller = controller
    result.insert()
    return result


def newSourceInfo(source='', stock=None, info=''):
    if check_duplicate(SourceInfo, source=source, stock=stock.id, info=info) is not None:
        return None
    si = SourceInfo(source=source, stock=stock, info=info)
    si.insert()
    return si
