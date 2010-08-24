#!/usr/bin/env python

from stocktracker.objects import model
from stocktracker.objects.model import SQLiteEntity, Meta
from stocktracker.objects.container import Portfolio, Watchlist, Index, Tag
from stocktracker.objects.transaction import Transaction
from stocktracker.objects.position import PortfolioPosition, WatchlistPosition
from stocktracker.objects.stock import Stock
from stocktracker.objects.dividend import Dividend
from stocktracker.objects.quotation import Quotation
from stocktracker.objects.sector import Sector
from stocktracker import pubsub
from stocktracker.objects.account import Account, AccountTransaction, AccountCategory
from stocktracker.logger import Log

import datetime
import gobject
import threading, thread
import time


modelClasses = [Portfolio, Transaction, Tag, Watchlist, Index, Dividend,
                PortfolioPosition, WatchlistPosition, AccountCategory,
                Quotation, Stock, Meta, Sector, Account, AccountTransaction]

#these classes will be loaded with one single call and will also load composite
#relations. therefore it is important that the list is complete in the sense
#that there are no classes holding composite keys to classes outside the list
initialLoadingClasses = [Portfolio,Transaction,Tag,Watchlist,Index,Dividend,Sector,
                         PortfolioPosition, WatchlistPosition,Account,  Meta, Stock, AccountTransaction, AccountCategory]

version = 1
datasource_manager = None

def initialLoading():
    #first load all the objects from the database so that they are cached
    for cl in initialLoadingClasses:
        Log.debug("Loading Objects of Class: " + cl.__name__)
        cl.getAll()
    #now load all of the composite
    for cl in initialLoadingClasses:
        #this will now be much faster as everything is in the cache
        for obj in cl.getAll():
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
    if model.store.new:
        m = Meta(version=version)
        m.insert()
        load_fixtures()
    else:
        db_version = Meta.getByPrimaryKey(1).version
        if db_version < version:
            upgrade_db(db_version)

def load_fixtures():
    for sname in ['Basic Materials','Conglomerates','Consumer Goods','Energy','Financial','Healthcare','Industrial Goods','Services','Technology','Transportation','Utilities']:
        s = Sector(name=sname)
        s.insert()

def update_all():
    datasource_manager.update_stocks(getAllStock()+getAllIndex())
    for container in getAllPortfolio()+getAllWatchlist()+getAllIndex():
        container.last_update = datetime.datetime.now()

def load_stocks():
    from stocktracker import yahoo
    from stocktracker.gui.progress_manager import add_monitor
    indices = ['^GDAXI', '^TECDAX', '^STOXX50E', '^DJI', '^IXIC']
    monitor = add_monitor(1, 'loading stocks...', 'gtk-refresh')
    GeneratorTask(yahoo.get_indices, monitor.progress_update, monitor.stop).start(indices)

def newPortfolio(name, id=None, last_update = datetime.datetime.now(), comment="",cash=0.0):
    result = Portfolio(id=id, name=name,last_update=last_update,comment=comment,cash=cash)
    result.insert()
    return result
    
def newWatchlist(name, id=None, last_update = datetime.datetime.now(), comment=""):
    result = Watchlist(id=id, name=name,last_update=last_update,comment=comment)
    result.insert()
    return result

def newAccount(name, id=None, amount=0, type=1):
    result = Account(id=id, name=name, amount=amount, type=type)
    result.insert()
    return result

def newAccountTransaction(id=None, description='', amount=0.0, type=1, account=None, category=None, date=datetime.date.today()):
    result = AccountTransaction(id=id, description=description, \
                    amount=amount, date=date, type=type, account=account, category=None)
    result.insert()
    return result

def newAccountCategory(name='', cid=None, parent=-1):
    result = AccountCategory(id=cid, name=name, parent=parent)
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
 
def newStock(insert=True, **kwargs):
    result = Stock(**kwargs)
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
    roots = []
    hierarchy = {}
    for cat in getAllAccountCategories():
        if cat.parent == -1:
            roots.append(cat)
        elif cat.parent in hierarchy: 
            hierarchy[cat.parent].append(cat)
        else:
            hierarchy[cat.parent] = [cat]
    return roots, hierarchy

def getAllSector():
    return Sector.getAll()

def getAllTag():
    return Tag.getAll()
    
def getAllStock():
    return Stock.getAll()

def getPositionForPortfolio(portfolio):
    key = portfolio.getPrimaryKey()
    erg = PortfolioPosition.getAllFromOneColumn("portfolio",key)
    return erg

def deleteAllPortfolioPosition(portfolio):
    #print "in deleteAllPortfolioPosition"
    for pos in getPositionForPortfolio(portfolio):
        #print "deleting ",pos
        pos.delete()
        
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

def getEarningsOrSpendingsSummedInPeriod(account, start_date, end_date, earnings=True):
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
    #ugly, but [0] does not work
    for row in model.store.select(query, (account.id, end_date, start_date)):
        if row[0] == None:
            return 0.0
        return row[0]
    
def deleteAllPortfolioTransaction(portfolio):
    for trans in getTransactionForPortfolio(portfolio):
        trans.delete() 

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
