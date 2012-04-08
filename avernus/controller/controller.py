#!/usr/bin/env python

from avernus.objects import model
from avernus.objects.dimension import Dimension, DimensionValue, \
    AssetDimensionValue
from avernus.objects.dividend import Dividend
from avernus.objects.model import Meta
from avernus.objects.quotation import Quotation
from avernus.objects.benchmark import Benchmark
from avernus.objects.source_info import SourceInfo
from avernus.objects.stock import Stock
from avernus.objects.transaction import Transaction
import datetime
import itertools
import logging
import sys
from avernus.controller import portfolio_controller as pfctlr
from avernus.controller.shared import check_duplicate, detect_duplicate



# don't know where else to put this...
def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return itertools.izip(a, b)

logger = logging.getLogger(__name__)


modelClasses = []

#these classes will be loaded with one single call and will also load composite
#relations. therefore it is important that the list is complete in the sense
#that there are no classes holding composite keys to classes outside the list
initialLoadingClasses = []

VERSION = 2

#FIXME very hackish, but allows to remove the circular controller imports in the objects
controller = sys.modules[__name__]

DIMENSIONS = {_('Region'): [_('Emerging markets'), _('America'), _('Europe'), _('Pacific')],
              _('Asset Class'): [_('Bond'), _('Stocks developed countries'), _('Commodities')],
              _('Risk'): [_('high'), _('medium'), _('low')],
              _('Currency'): [_('Euro'), _('Dollar'), _('Yen')],
              _('Company Size'): [_('large'), _('medium'), _('small')],
              _('Sector'): ['Basic Materials', 'Conglomerates', 'Consumer Goods', 'Energy', 'Financial', 'Healthcare', 'Industrial Goods', 'Services', 'Technology', 'Transportation', 'Utilities']
              }
CATEGORIES = {
    _('Utilities'): [_('Gas'), _('Phone'), _('Water'), _('Electricity')],
    _('Entertainment'): [_('Books'), _('Movies'), _('Music'), _('Amusement')],
    _('Fees'):[],
    _('Gifts'):[],
    _('Health care'): [_('Doctor'), _('Pharmacy'), _('Health insurance')],
    _('Food'): [_('Groceries'), _('Restaurants'), _('Coffee')],
    _('Transport'): [_('Car'), _('Train'), _('Fuel')],
    _('Services'): [_('Shipping')],
    _('Home'): [_('Rent'), _('Home improvements')],
    _('Personal care'): [],
    _('Taxes'): [],
    _('Income'): [],
    _('Shopping'): [_('Clothes'), _('Electronics'), _('Hobbies'), _('Sporting Goods')],
    _('Travel'): [_('Lodging'), _('Transportation')]
}


def initialLoading(ctlr):
    #first load all the objects from the database so that they are cached
    for cl in ctlr.initialLoadingClasses:
        logger.debug("Loading Objects of Class: " + cl.__name__)
        cl.getAll()
    #now load all of the composite
    for cl in ctlr.initialLoadingClasses:
        #this will now be much faster as everything is in the cache
        for obj in cl.getAll():
            obj.controller = ctlr
            logger.debug("Loading Composites of object: " + unicode(obj))
            obj.retrieveAllComposite()


def is_duplicate(tp, **kwargs):
    sqlArgs = {}
    for req in tp.__comparisonPositives__:
        sqlArgs[req] = kwargs[req]
    present = tp.getByColumns(sqlArgs, operator=" AND ", create=True)
    if present:
        return True
    else: return False



def createTables():
    for cl in modelClasses:
        print cl
        cl.createTable()
    #if not model.store.new:
    #    db_version = Meta.getByPrimaryKey(1).version
    #    if db_version < VERSION:
    #        print "Need to upgrade the database..."
    #        model.store.backup()
    #        upgrade_db(db_version)
    #if model.store.new:
    #    m = Meta(id=1, version=VERSION)
    #    m.insert()
    #    load_sample_data()

def upgrade_db(db_version):
    if db_version == 1:
        print "Updating database v.1 to v.2!"
        model.store.execute('ALTER TABLE stock ADD COLUMN ter FLOAT DEFAULT 0.0')
        db_version += 1
    if db_version == VERSION:
        set_db_version(db_version)
        print "Successfully updated your database to the current version!"
    if db_version > VERSION:
        print "ERROR: unknown db version"

def set_db_version(version):
    #m = Meta.getByPrimaryKey(1)
    #m.version = version
    pass

def load_sample_data():
    for dim, vals in DIMENSIONS.iteritems():
        new_dim = newDimension(dim)
        for val in vals:
            newDimensionValue(new_dim, val)
    #for cat, subcats in CATEGORIES.iteritems():
    #    parent = newAccountCategory(name=cat)
    #    for subcat in subcats:
    #        newAccountCategory(name=subcat, parent=parent)
    acc = newAccount(_('sample account'))
    newAccountTransaction(account=acc, description='this is a sample transaction', amount=99.99, date=datetime.date.today())
    newAccountTransaction(account=acc, description='another sample transaction', amount= -33.90, date=datetime.date.today())
    pfctlr.newPortfolio(_('sample portfolio'))
    pfctlr.newWatchlist(_('sample watchlist'))



def newAccount(name, a_id=None, amount=0, accounttype=1):
    result = Account(id=a_id, name=name, amount=amount, type=accounttype)
    result.controller = controller
    result.insert()
    return result

def newAccountTransaction(id=None, description='', amount=0.0, account=None, category=None, date=datetime.date.today(), transferid= -1, detect_duplicates=False):
    if detect_duplicates:
        duplicates = check_duplicate(AccountTransaction, \
                               description=description, \
                               amount=amount, \
                               date=date, \
                               account=account, \
                               category=category)
        if duplicates:
            return None
    if type(category) == type(unicode()):
        cat = getAccountCategoryForName(category)
        if not cat:
            cat = newAccountCategory(category)
    else:
        cat = category

    result = AccountTransaction(id=id, \
                                description=description, \
                                amount=amount, \
                                date=date, \
                                account=account, \
                                category=cat,
                                transferid=transferid)
    result.insert()
    account.amount += amount
    return result


def newAccountCategory(name='', cid=None, parent=None):
    if parent is None:
        parentid = -1
    else:
        parentid = parent.id
    result = AccountCategory(id = cid, name=name, parentid=parentid)
    result.insert()
    return result

def newDividend(new_id=None, price=0, date=datetime.date.today(), costs=0, position=None, shares=0):
    result = Dividend(id=new_id, price=price, date=date, costs=costs, position=position, shares=shares)
    result.insert()
    return result

def newTransaction(date=datetime.datetime.now(), \
                   portfolio=None, \
                   position=None, \
                   type=0, \
                   quantity=0, \
                   price=0.0, \
                   costs=0.0):
    result = Transaction(id=None, \
                         portfolio=portfolio, \
                         position=position, \
                         date=date, \
                         type=type, \
                         quantity=quantity, \
                         price=price, \
                         costs=costs)
    result.insert()
    return result


def getSourceInfo(source='', stock=None):
    args = {'stock': stock.getPrimaryKey(), 'source':source}
    return SourceInfo.getByColumns(args, create=True)

def newDimensionValue(dimension=None, name=""):
    return detect_duplicate(DimensionValue, dimension=dimension.id, name=name)

def newDimension(name):
    dim = detect_duplicate(Dimension, name=name)
    dim.controller = controller
    return dim



def newQuotation(date=datetime.date.today(), \
                 stock=None, \
                 open=0, \
                 high=0, \
                 low=0, \
                 close=0, \
                 vol=0, \
                 exchange='', \
                 detectDuplicates=True):
    if detectDuplicates:
        return detect_duplicate(Quotation, \
                               date=date, \
                               open=open, \
                               high=high, \
                               low=low, \
                               close=close, \
                               stock=stock.id, \
                               exchange=exchange, \
                               volume=vol)
    else:
        result = Quotation(id=None, \
                           date=date, \
                           open=open, \
                           high=high, \
                           low=low, \
                           close=close, \
                           stock=stock, \
                           exchange=exchange, \
                           volume=vol)
        result.insert()
        return result


def getAllTransaction():
    return Transaction.getAll()


def getAllAccount():
    return Account.getAll()

def getAllAccountTransactions():
    return AccountTransaction.getAll()

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



def getAccountCategoryForName(name):
    cats = getAllAccountCategories()
    for cat in cats:
        if cat.name == name:
            return cat
    return None


def getAllStock():
    return Stock.getAll()


def getTransactionsForAccount(account):
    key = account.getPrimaryKey()
    return AccountTransaction.getAllFromOneColumn("account", key)

def yield_matching_transfer_tranactions(transaction):
    for account in getAllAccount():
        if account != transaction.account:
            for ta in account.yield_matching_transfer_transactions(transaction):
                yield ta

def deleteAllAccountTransaction(account):
    for trans in getTransactionsForAccount(account):
        trans.delete()

def getStockForSearchstring(searchstring):
    sqlArgs = {}
    for req in ['name', 'isin']:
        sqlArgs[req] = '%' + searchstring + '%'
    return Stock.getByColumns(sqlArgs, operator=" OR ", operator2=' LIKE ', create=True)



