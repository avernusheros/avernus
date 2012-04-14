from avernus.objects.container import Portfolio, Watchlist
from avernus.controller import position_controller, asset_controller
from avernus.objects import session
from . import dsm

import datetime



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

def get_all_portfolio_position():
    return session.query(PortfolioPosition).all()

def get_current_value(portfolio):
    value = 0.0
    for pos in portfolio:
        value += position_controller.get_current_value(pos)
    return value

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
        return 100.0 * position_controller.get_current_value(position) / cvalue

def get_closed_positions(portfolio):
    return []

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
    if get_dividends_count(pf) == 0:
        return datetime.date.today()
    current = None
    # could not test it, probably won't work
    for dividend in pf.dividends:
        if not current or dividend.date > current:
            current = dividend.date
    return current

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
    for item in dsm.update_stocks(items):
        count += 1.0
        yield count / itemcount
    self.last_update = datetime.now()
    pubsub.publish("stocks.updated", self)
    yield 1



#  =============================================
# Mordor from here




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



def deleteAllDimensionValue(dimension):
    for val in getAllDimensionValueForDimension(dimension):
        deleteAllAssetDimensionValue(val)
        val.delete()


def deleteAllWatchlistPosition(watchlist):
    for pos in getPositionForWatchlist(watchlist):
        pos.delete()



def getAssetDimensionValueForStock(stock, dim):
    stockADVs = AssetDimensionValue.getAllFromOneColumn('stock', stock.id)
    #for adv in stockADVs:
    #    print adv, adv.dimensionValue
    stockADVs = filter(lambda adv: adv.dimensionValue.dimension == dim, stockADVs)
    return stockADVs


def getPriceFromStockAtDate(stock, date):
    args = {'stock': stock.id, 'date':date.date()}
    res = Quotation.getByColumns(args, create=False)
    for item in res:
        return item[5]
    return None

def getBuyTransaction(portfolio_position):
    for ta in Transaction.getByColumns({'position': portfolio_position.id, 'type':1}, create=True):
        return ta

def yieldSellTransactions(portfolio_position):
    for ta in Transaction.getByColumns({'position': portfolio_position.id, 'type':0}, create=True):
        yield ta


def newSourceInfo(source='', stock=None, info=''):
    if check_duplicate(SourceInfo, source=source, stock=stock.id, info=info) is not None:
        return None
    si = SourceInfo(source=source, stock=stock, info=info)
    si.insert()
    return si
