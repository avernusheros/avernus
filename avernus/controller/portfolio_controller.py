from avernus.objects import model
from avernus.objects.stock import Stock
from avernus.objects.container import Portfolio, Watchlist
from avernus.objects.position import PortfolioPosition, WatchlistPosition
from avernus.objects.dividend import Dividend
from avernus.objects.source_info import SourceInfo
from avernus.objects.transaction import Transaction
from avernus.objects.quotation import Quotation
from avernus.objects.dimension import Dimension, DimensionValue, \
    AssetDimensionValue
from avernus.controller.shared import check_duplicate, detect_duplicate


import datetime
import sys

datasource_manager = None
initialLoadingClasses = [Transaction, Portfolio, Dividend, Watchlist, \
                        PortfolioPosition, WatchlistPosition, Dimension, \
                        DimensionValue, AssetDimensionValue, Stock]
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
