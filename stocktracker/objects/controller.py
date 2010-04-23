#!/usr/bin/env python

import model
import datetime
from stocktracker.objects.container import Portfolio, Watchlist, Index
from stocktracker.objects.tag import Tag
from stocktracker.objects.transaction import Transaction
from stocktracker.objects.position import PortfolioPosition, WatchlistPosition
from stocktracker.objects.stock import Stock
from stocktracker.objects.exchange import Exchange
from stocktracker.objects.dividend import Dividend
from stocktracker.objects.quotation import Quotation

modelClasses = [Portfolio, Transaction, Tag, Watchlist, Index, Dividend,
                PortfolioPosition, WatchlistPosition, Exchange,
                Quotation, Stock]

def createTables():
    for cl in modelClasses:
        cl.createTable()

def newPortfolio(name, id=None, last_update = datetime.datetime.now(), comment="",cash=0.0):
    # Check for existence of name
    pre = Portfolio.getByPrimaryKey(name)
    if pre:
        return pre
    result = Portfolio(id=id, name=name,last_update=last_update,comment=comment,cash=cash)
    result.insert()
    return result
    
def newWatchlist(name, id=None, last_update = datetime.datetime.now(), comment=""):
    # Check for existence of name
    pre = Watchlist.getByPrimaryKey(name)
    if pre:
        return pre
    result = Watchlist(id=id, name=name,last_update=last_update,comment=comment)
    result.insert()
    return result

def newTransaction(date=datetime.datetime.now(),portfolio=None,type=0,quantity=0,price=0.0,costs=0.0):
    result = Transaction(id=None, portfolio=portfolio, date=date, type=type, quantity=quantity, price=price, costs=costs)
    result.insert()
    return result

def newTag(name):
    result = Tag(name=name)
    result.insert()
    return result

def getAllPortfolio():
    return Portfolio.getAll()

def getAllTransaction():
    return Transaction.getAll()

def getAllWatchlist():
    return Watchlist.getAll()

def getAllIndex():
    return Index.getAll()

def getAllTag():
    return Tag.getAll()

def getTransactionForPortfolio(portfolio):
    key = portfolio.__primaryKey__

