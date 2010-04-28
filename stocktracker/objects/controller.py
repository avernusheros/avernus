#!/usr/bin/env python

import datetime
from stocktracker.objects import model
from stocktracker.objects.model import SQLiteEntity, Meta
from stocktracker.objects.container import Portfolio, Watchlist, Index, Tag
from stocktracker.objects.transaction import Transaction
from stocktracker.objects.position import PortfolioPosition, WatchlistPosition
from stocktracker.objects.stock import Stock
from stocktracker.objects.exchange import Exchange
from stocktracker.objects.dividend import Dividend
from stocktracker.objects.quotation import Quotation
from stocktracker import updater
from stocktracker import pubsub
from stocktracker import logger


modelClasses = [Portfolio, Transaction, Tag, Watchlist, Index, Dividend,
                PortfolioPosition, WatchlistPosition, Exchange,
                Quotation, Stock, Meta]
version = 1

def createTables():
    for cl in modelClasses:
        cl.createTable()
    if model.store.new:
        m = Meta(id=1, version=version)
        m.insert()
    else:
        db_version = Meta.getByPrimaryKey(1).version
        if db_version < version:
            upgrade_db(db_version)

def upgrade_db(from_version):
    print "need to upgrade db from version", from_version,'to version', version
    #1. do upgrade
    #2. update version number



def update_all():
    updater.update_stocks(getAllStock()+getAllIndex())
    for container in getAllPortfolio()+getAllWatchlist()+getAllIndex():
        container.last_update = datetime.datetime.now()

def load_stocks():
    #FIXME should check for duplicates
    from stocktracker import yahoo
    for ind in ['^GDAXI', '^TECDAX', '^STOXX50E', '^DJI', '^IXIC']:
        yahoo.get_index(ind)
    

def newPortfolio(name, id=None, last_update = datetime.datetime.now(), comment="",cash=0.0):
    # Check for existence of name
    #FIXME name isnt primary key
    pre = None#Portfolio.getByPrimaryKey(name)
    if pre:
        return pre
    result = Portfolio(id=id, name=name,last_update=last_update,comment=comment,cash=cash)
    result.insert()
    return result
    
def newWatchlist(name, id=None, last_update = datetime.datetime.now(), comment=""):
    # Check for existence of name
    #FIXME name isnt primary key
    pre = None#Watchlist.getByPrimaryKey(name)
    if pre:
        return pre
    result = Watchlist(id=id, name=name,last_update=last_update,comment=comment)
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
    

def newIndex(name='', isin='', currency='', date=datetime.datetime.now(), exchange=None, yahoo_symbol=''):
    result = Index(id=None, name=name, currency=currency, isin=isin, date=date, exchange=exchange, yahoo_symbol=yahoo_symbol, price=0, change=0)
    result.insert()
    pubsub.publish('index.created',result)
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


def newExchange(name):
    #FIXME
    #pre = Exchange.getAllFromOneColumn('name', name)
    #if pre:
        #return pre
    result = Exchange(name=name)
    result.insert()
    return result

def newTag(name):
    result = Tag(name=name)
    result.insert()
    pubsub.publish('tag.created',result)
    return result
  
def newStock(price=0.0, change=0.0, currency='', type=0, name='', isin='', date=datetime.datetime.now(), exchange=None, yahoo_symbol=''):
    result = Stock(id=None, price=price, currency=currency, type=type, name=name, isin=isin, change=change, date=date, exchange=exchange, yahoo_symbol=yahoo_symbol)
    result.insert()
    return result

def newQuotation(date=datetime.date.today(),\
                 stock=None,\
                 open=0,\
                 high=0,\
                 low=0,\
                 close=0,\
                 vol=0):
    result = Quotation(id=None,\
                       date=date,\
                       open=open,\
                       high=high,\
                       low=low,\
                       close=close,\
                       stock=stock,\
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

def getAllTag():
    return Tag.getAll()
    
def getAllStock():
    return Stock.getAll()

def getPositionForPortfolio(portfolio):
    key = portfolio.getPrimaryKey()
    erg = PortfolioPosition.getAllFromOneColumn("portfolio",key)
    return erg
    
def getPositionForWatchlist(watchlist):
    key = watchlist.getPrimaryKey()
    return WatchlistPosition.getAllFromOneColumn("watchlist",key)

def getPositionForTag(tag):
    possible = getAllPosition()
    #FIXME
    #print "all: ", possible, possible[0].tags
    for pos in possible:
        if not pos.__composite_retrieved__:
            pos.retrieveAllComposite()
    possible = filter(lambda pos: pos.hasTag(tag), possible)
    return possible

def getTransactionForPortfolio(portfolio):
    key = portfolio.getPrimaryKey()
    erg = Transaction.getAllFromOneColumn("portfolio",key)
    return erg


def getQuotationsFromStock(stock, start):
    erg = Quotation.getAllFromOneColumn('stock', stock.getPrimaryKey())
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
    
def onPositionNewTag(position=None,tagText=None):
    if not position or not tagText:
        logger.logger.error("Malformed onPositionNewTag Call (position,tagText)" + str((position,tagText)))
    tag = None
    if Tag.primaryKeyExists(tagText):
        tag = Tag.getByPrimaryKey(tagText)
    else:
        tag = newTag(tagText)
    position.tags.append(tag)

pubsub.subscribe('position.newTag', onPositionNewTag)
