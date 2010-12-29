#!/usr/bin/env python

from avernus import pubsub
from avernus.logger import Log
from avernus.objects import model
from avernus.objects.account import Account, AccountTransaction, AccountCategory
from avernus.objects.asset_class import AssetClass
from avernus.objects.container import Portfolio, Watchlist, Index, Tag
from avernus.objects.dimension import Dimension, DimensionValue, \
    AssetDimensionValue
from avernus.objects.dividend import Dividend
from avernus.objects.model import SQLiteEntity, Meta
from avernus.objects.position import PortfolioPosition, WatchlistPosition
from avernus.objects.quotation import Quotation
from avernus.objects.region import Region
from avernus.objects.risk import Risk
from avernus.objects.sector import Sector
from avernus.objects.stock import Stock
from avernus.objects.transaction import Transaction
import datetime
import gobject
import sys
import thread
import threading
import time



modelClasses = [Portfolio, Transaction, Tag, Watchlist, Index, Dividend,
                PortfolioPosition, WatchlistPosition, AccountCategory,
                Quotation, Stock, Meta, Sector, Account, AccountTransaction,
                Region, AssetClass, Risk, Dimension, DimensionValue, AssetDimensionValue]

#these classes will be loaded with one single call and will also load composite
#relations. therefore it is important that the list is complete in the sense
#that there are no classes holding composite keys to classes outside the list
initialLoadingClasses = [Portfolio,Transaction,Tag,Watchlist,Index,Dividend,Sector,
                         PortfolioPosition, WatchlistPosition,Account, Meta, Stock, 
                         AccountTransaction, AccountCategory, Dimension, DimensionValue,
                         AssetDimensionValue]

VERSION = 5
datasource_manager = None

#FIXME very hackish, but allows to remove the circular controller imports in the objects
controller = sys.modules[__name__]

# SAMPLE DATA
SECTORS = ['Basic Materials','Conglomerates','Consumer Goods','Energy','Financial','Healthcare','Industrial Goods','Services','Technology','Transportation','Utilities']
REGIONS = ['Emerging Markets', 'Europe', 'America', 'Worldwide']
ASSET_CLASSES = ['large cap stocks', 'Bonds', 'real estate', 'insurance' ]
RISK = ['high', 'medium', 'low']
CATEGORIES = {
    _('Utilities'): [_('Gas'),_('Phone'), _('Water'), _('Electricity')],
    _('Entertainment'): [_('Books'),_('Movies'), _('Music'), _('Amusement')],
    _('Fees'):[],
    _('Gifts'):[],
    _('Health care'): [_('Doctor'),_('Pharmacy'), _('Health insurance')],
    _('Food'): [_('Groceries'),_('Restaurants'), _('Coffee')],
    _('Transport'): [_('Car'),_('Train'), _('Fuel')],
    _('Services'): [_('Shipping')],
    _('Home'): [_('Rent'), _('Home improvements')],
    _('Personal care'): [],
    _('Taxes'): [],
    _('Income'): [],
    _('Shopping'): [_('Clothes'),_('Electronics'),_('Hobbies'),_('Sporting Goods')],
    _('Travel'): [_('Lodging'), _('Transportation')]
}

def initialLoading():
    #first load all the objects from the database so that they are cached
    for cl in initialLoadingClasses:
        Log.debug("Loading Objects of Class: " + cl.__name__)
        cl.getAll()
    #now load all of the composite
    for cl in initialLoadingClasses:
        #this will now be much faster as everything is in the cache
        for obj in cl.getAll():
            obj.controller = controller
            Log.debug("Loading Composites of Objekt: " + str(obj))
            obj.retrieveAllComposite()

def is_duplicate(tp, **kwargs):
    sqlArgs = {}
    for req in tp.__comparisonPositives__:
        sqlArgs[req] = kwargs[req]
    present = tp.getByColumns(sqlArgs,operator=" AND ",create=True)
    if present:
        return True
    else: return False

def check_duplicate(tp, **kwargs):
    sqlArgs = {}
    for req in tp.__comparisonPositives__:
        sqlArgs[req] = kwargs[req]
    present = tp.getByColumns(sqlArgs,operator=" AND ",create=True)
    if present:
        return present
    return None

def detectDuplicate(tp,**kwargs):
    #print tp, kwargs
    sqlArgs = {}
    for req in tp.__comparisonPositives__:
        sqlArgs[req] = kwargs[req]
    present = tp.getByColumns(sqlArgs,operator=" AND ",create=True)
    if present:
        if len(present) == 1:
            #print "PRESENT!"
            return present[0]
        else:
            #print tp, kwargs
            #print present
            raise Exception("Multiple results for duplicate detection")
    #print "not Present!"
    new = tp(**kwargs)
    new.insert()
    return new

def createTables():
    for cl in modelClasses:
        cl.createTable()
    if not model.store.new:
        db_version = Meta.getByPrimaryKey(1).version
        if db_version < VERSION:
            print "Need to upgrade the database..."
            model.store.backup()
            upgrade_db(db_version)
    if model.store.new:
        m = Meta(id=1, version=VERSION)
        m.insert()
        load_sample_data()

def upgrade_db(db_version):
    if db_version==1:
        print "Updating database v.1 to v.2!"
        db_version+=1
    if db_version==2:
        print "Updating db to version 3..."
        model.store.execute('ALTER TABLE stock ADD COLUMN region INTEGER')
        for rname in REGIONS:
            newRegion(rname)
        db_version+=1
    if db_version==3:
        model.store.execute('ALTER TABLE stock ADD COLUMN asset_class INTEGER')
        for aclass in ASSET_CLASSES:
            newAssetClass(aclass)
        db_version+=1
    if db_version==4:
        model.store.execute('ALTER TABLE stock ADD COLUMN risk INTEGER')
        for risk in RISK:
            newRisk(risk)
        db_version+=1
    if db_version==VERSION:
        set_db_version(db_version)
        print "Successfully updated your database to the current version!"
    if db_version>VERSION:
        print "ERROR: unknown db version"

def set_db_version(version):
    m = Meta.getByPrimaryKey(1)
    m.version = version

def load_sample_data():
    for sname in SECTORS:
        newSector(sname)
    for rname in REGIONS:
        newRegion(rname)
    for aclass in ASSET_CLASSES:
        newAssetClass(aclass)
    for cat, subcats in CATEGORIES.iteritems():
        parent = newAccountCategory(name=cat)
        for subcat in subcats:
            newAccountCategory(name=subcat, parent=parent)
    acc = newAccount(_('sample account'))
    newAccountTransaction(account=acc, description='this is a sample transaction', amount=99.99, date=datetime.date.today())
    newAccountTransaction(account=acc, description='another sample transaction', amount=-33.90, date=datetime.date.today())
    pf = newPortfolio(_('sample portfolio'))
    wl = newWatchlist(_('sample watchlist'))

def update_all():
    datasource_manager.update_stocks(getAllStock()+getAllIndex())
    for container in getAllPortfolio()+getAllWatchlist()+getAllIndex():
        container.last_update = datetime.datetime.now()

def newPortfolio(name, id=None, last_update = datetime.datetime.now(), comment="",cash=0.0):
    result = Portfolio(id=id, name=name,last_update=last_update,comment=comment,cash=cash)
    result.controller = controller
    result.insert()
    return result

def newWatchlist(name, id=None, last_update = datetime.datetime.now(), comment=""):
    result = Watchlist(id=id, name=name,last_update=last_update,comment=comment)
    result.insert()
    return result

def newAccount(name, id=None, amount=0, accounttype=1):
    result = Account(id=id, name=name, amount=amount, type=accounttype)
    result.controller = controller
    result.insert()
    return result

def newAccountTransaction(id=None, description='', amount=0.0, account=None, category=None, date=datetime.date.today(), transferid=-1, detect_duplicates=False):
    if detect_duplicates:
        duplicates = check_duplicate(AccountTransaction,\
                               description=description, \
                               amount=amount, \
                               date=date, \
                               account=account, \
                               category=category)
        if duplicates:
            return None
    result = AccountTransaction(id=id, \
                                description=description, \
                                amount=amount, \
                                date=date, \
                                account=account, \
                                category=category, transferid=transferid)
    result.insert()
    account.amount += amount
    return result

def newAccountCategory(name='', cid=None, parent=None):
    if parent is None:
        parentid =-1
    else:
        parentid = parent.id
    result = AccountCategory(id=cid, name=name, parentid=parentid)
    result.insert()
    return result

def newDividend(new_id=None, price=0, date=datetime.date.today(), costs=0, position=None, shares=0):
    result = Dividend(id=new_id, price=price, date=date, costs=costs, position=position, shares=shares)
    result.insert()
    return result

def newTransaction(date=datetime.datetime.now(),\
                   portfolio=None,\
                   position=None,\
                   type=0,\
                   quantity=0,\
                   price=0.0,\
                   costs=0.0):
    result = Transaction(id=None,\
                         portfolio=portfolio,\
                         position=position,\
                         date=date,\
                         type=type,\
                         quantity=quantity,\
                         price=price,\
                         costs=costs)
    result.insert()
    return result


def newIndex(name='', isin='', currency='', date=datetime.datetime.now(), exchange='', yahoo_symbol=''):
    result = Index(id=None, name=name, currency=currency, isin=isin, date=date, exchange=exchange, yahoo_symbol=yahoo_symbol, price=0, change=0)
    result.insert()
    return result

def newPortfolioPosition(price=0,\
                         date=datetime.datetime.now(),\
                         quantity=1,\
                         portfolio=None,\
                         stock=None,\
                         comment=''\
                         ):
    result = PortfolioPosition(id=None,\
                               price=price,\
                               date=date,\
                               quantity=quantity,\
                               portfolio=portfolio,\
                               stock = stock,\
                               comment=comment\
                               )
    result.controller = controller
    result.insert()
    return result


def newWatchlistPosition(price=0,\
                         date=datetime.datetime.now(),\
                         quantity=1,\
                         watchlist=None,\
                         stock=None,\
                         comment=''\
                         ):
    result = WatchlistPosition(id=None,\
                               price=price,\
                               date=date,\
                               watchlist=watchlist,\
                               stock = stock,\
                               comment=comment\
                               )
    result.insert()
    return result


def newTag(name):
    result = Tag(name=name)
    result.insert()
    pubsub.publish('tag.created',result)
    return result

def newDimensionValue(dimension=None, name=""):
    print "New DimensionValue ", dimension, name
    return None

def newSector(name):
    return detectDuplicate(Sector, name=name)

def newAssetClass(name):
    return detectDuplicate(AssetClass, name=name)

def newAssetDimensionValue(stock, dimensionValue, value):
    adv = detectDuplicate(AssetDimensionValue, stock=stock.id, dimensionValue=dimensionValue.id,
                          value=value)
    return adv

def newRegion(name):
    return detectDuplicate(Region, name=name)

def newRisk(name):
    return detectDuplicate(Risk, name=name)

def newStock(insert=True, **kwargs):
    result = Stock(**kwargs)
    result.controller = controller
    if insert:
        result.insert()
    return result

def newQuotation(date=datetime.date.today(),\
                 stock=None,\
                 open=0,\
                 high=0,\
                 low=0,\
                 close=0,\
                 vol=0,\
                 exchange='',\
                 detectDuplicates = True):
    if detectDuplicates:
        return detectDuplicate(Quotation,\
                               date=date,\
                               open=open,\
                               high=high,\
                               low=low,\
                               close=close,\
                               stock=stock.id,\
                               exchange=exchange,\
                               volume=vol)
    else:
        result = Quotation(id=None,\
                           date=date,\
                           open=open,\
                           high=high,\
                           low=low,\
                           close=close,\
                           stock=stock,\
                           exchange=exchange,\
                           volume=vol)
        result.insert()
        return result


def getAllPortfolio():
    return Portfolio.getAll()

def getAllPosition():
    return PortfolioPosition.getAll()

def getAllTransaction():
    return Transaction.getAll()

def getAllWatchlist():
    return Watchlist.getAll()

def getAllIndex():
    return Index.getAll()

def getAllAccount():
    return Account.getAll()

def getAllAccountCategories():
    return AccountCategory.getAll()

def getAllAccountCategoriesHierarchical():
    hierarchy = {None:[]}
    for cat in getAllAccountCategories():
        if cat.parent is None:
            hierarchy[None].append(cat)
        elif cat.parent in hierarchy:
            hierarchy[cat.parent].append(cat)
        else:
            hierarchy[cat.parent] = [cat]
    return hierarchy

def getAllDimension():
    return Dimension.getAll()

def getDimensionValueForDimension(dim):
    erg = []
    for value in DimensionValue.getAll():
        if value.dimension == dim:
            erg.append(value)
    return erg

def getAssetDimensionValueForStock(stock, dim):
    stockADVs = AssetDimensionValue.getAllFromOneColumn('stock', stock.id)
    stockADVs = filter(lambda adv: adv.dimensionValue.dimension == dim, stockADVs)
    return stockADVs

def getAllSector():
    return Sector.getAll()
    
def getAllAssetClass():
    return AssetClass.getAll()

def getAllRisk():
    return Risk.getAll()

def getAllRegion():
    return Region.getAll()

def getAllTag():
    return Tag.getAll()

def getAllStock():
    return Stock.getAll()

def getPositionForPortfolio(portfolio):
    key = portfolio.getPrimaryKey()
    erg = PortfolioPosition.getAllFromOneColumn("portfolio",key)
    return erg

def deleteSectorFromStock(sector):
    for stock in getAllStock():
        if stock.sector == sector:
            stock.sector = None
    
def deleteRiskFromStock(risk):
    for stock in getAllStock():
        if stock.risk == risk:
            stock.risk = None
            
def deleteAssetClassFromStock(asset_class):
    for stock in getAllStock():
        if stock.asset_class == asset_class:
            stock.asset_class = None

def deleteRegionFromStock(region):
    for stock in getAllStock():
        if stock.region == region:
            stock.region = None

def getTransactionForPosition(position):
    key = position.getPrimaryKey()
    erg = Transaction.getAllFromOneColumn("position", key)
    return erg

def deleteAllPositionTransaction(position):
    for trans in getTransactionForPosition(position):
        trans.delete()

def getPositionForWatchlist(watchlist):
    key = watchlist.getPrimaryKey()
    return WatchlistPosition.getAllFromOneColumn("watchlist",key)

def deleteAllWatchlistPosition(watchlist):
    for pos in getPositionForWatchlist(watchlist):
        pos.delete()

def getPositionForTag(tag):
    possible = getAllPosition()
    for pos in possible:
        if not pos.__composite_retrieved__:
            pos.retrieveAllComposite()
    possible = filter(lambda pos: pos.hasTag(tag), possible)
    return possible

def getDividendForPosition(pos):
    return Dividend.getAllFromOneColumn("position", pos.getPrimaryKey())

def getTransactionForPortfolio(portfolio):
    key = portfolio.getPrimaryKey()
    erg = Transaction.getAllFromOneColumn("portfolio",key)
    return erg

def getTransactionsForAccount(account):
    key = account.getPrimaryKey()
    return AccountTransaction.getAllFromOneColumn("account",key)

def getAccountChangeInPeriodPerDay(account, start_date, end_date):
    query = """
    SELECT sum(trans.amount), trans.date
    FROM accounttransaction as trans, account
    WHERE account.id == ?
    AND account.id == trans.account
    AND trans.date <= ?
    AND trans.date >= ?
    GROUP BY trans.date
    ORDER BY trans.date DESC
    """
    for change, date in model.store.select(query, (account.id, end_date, start_date)):
        yield change, date

def getEarningsOrSpendingsSummedInPeriod(account, start_date, end_date, earnings=True, transfers=False):
    if earnings: operator = '>'
    else: operator = '<'
    query = """
    SELECT abs(sum(trans.amount))
    FROM accounttransaction as trans, account
    WHERE account.id == ?
    AND account.id == trans.account
    AND trans.amount"""+operator+"""0.0
    AND trans.date <= ?
    AND trans.date >= ?
    """
    if not transfers:
        query+=' AND trans.transferid == -1'
    #ugly, but [0] does not work
    for row in model.store.select(query, (account.id, end_date, start_date)):
        if row[0] == None:
            return 0.0
        return row[0]

def yield_matching_transfer_tranactions(transaction):
    for account in getAllAccount():
        if account != transaction.account:
            for ta in account.yield_matching_transfer_tranactions(transaction):
                yield ta

def deleteAllAccountTransaction(account):
    for trans in getTransactionsForAccount(account):
        trans.delete()

def getStockForSearchstring(searchstring):
    sqlArgs = {}
    for req in ['name', 'isin']:
        sqlArgs[req] = '%'+searchstring+'%'
    return Stock.getByColumns(sqlArgs,operator=" OR ",operator2=' LIKE ', create=True)

def getQuotationsFromStock(stock, start):
    args = {'stock': stock.getPrimaryKey(), 'exchange':stock.exchange}
    erg = Quotation.getByColumns(args, create=True)
    erg = filter(lambda quote: quote.date > start, erg)
    erg = sorted(erg, key=lambda stock: stock.date)
    return erg

def getNewestQuotation(stock):
    key = stock.getPrimaryKey()
    erg = Quotation.getAllFromOneColumn("stock", key)
    if len(erg) == 0:
        return None
    else:
        return erg[0].date

def getBuyTransaction(portfolio_position):
    key = portfolio_position.getPrimaryKey()
    for ta in Transaction.getAllFromOneColumn('position', key):
        if ta.type == 1:
            return ta

def onPositionNewTag(position=None,tagText=None):
    if not position or not tagText:
        Log.error("Malformed onPositionNewTag Call (position,tagText)" + str((position,tagText)))
    position.tags.append(detectDuplicate(Tag, name=tagText))

pubsub.subscribe('position.newTag', onPositionNewTag)


class GeneratorTask(object):
    """
    http://unpythonic.blogspot.com/2007/08/using-threads-in-pygtk.html
    Thanks!
    """
    def __init__(self, generator, loop_callback, complete_callback=None):
        self.generator = generator
        self.loop_callback = loop_callback
        self.complete_callback = complete_callback

    def _start(self, *args, **kwargs):
        self._stopped = False
        for ret in self.generator(*args, **kwargs):
            if self._stopped:
                thread.exit()
            gobject.idle_add(self._loop, ret)
        if self.complete_callback is not None:
            gobject.idle_add(self.complete_callback)

    def _loop(self, ret):
        if ret is None:
            ret = ()
        if not isinstance(ret, tuple):
            ret = (ret,)
        self.loop_callback(*ret)

    def start(self, *args, **kwargs):
        threading.Thread(target=self._start, args=args, kwargs=kwargs).start()

    def stop(self):
        self._stopped = True
