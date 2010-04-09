#!/usr/bin/env python

import elixir
from elixir import Entity, Field, Unicode, String, Float, Integer, \
                    UnicodeText, DateTime, OneToMany, ManyToMany, ManyToOne
from stocktracker  import pubsub
from stocktracker  import updater
from elixir.events import *   
from datetime      import datetime
 
 
    
TYPES = {None: 'n/a', 0:'stock', 1:'fund'}


###############################################################
#################     BASE CLASSES      #######################
###############################################################

class Position(object):
    tagstring = ''
    
    @property
    def type_string(self):
        return TYPES[self.stock.type]
    
    @property
    def days_gain(self):
        return self.stock.change * self.quantity
    
    @property
    def gain(self):
        stock = self.stock.price - self.price
        absolute = stock * self.quantity
        percent = round(absolute * 100 / (self.price*self.quantity),2)
        return absolute, percent

    @property
    def current_change(self):
        return self.stock.change, round(self.stock.percent,2)
    
    @property    
    def bvalue(self):
        return self.quantity * self.price
    
    @property
    def cvalue(self):
        return self.quantity * self.stock.price 
     
    @property
    def name(self):
        return self.stock.name    
    

class Container(object):

    tagstring = ''
    
    @property
    def current_change(self):
        change = 0.0
        for pos in self.positions:
            stock, percent = pos.current_change
            change +=stock * pos.quantity
        start = self.cvalue - change
        if start == 0.0:
            percent = 0
        else:
            percent = round(100.0 / start * change,2)
        return change, percent
    
    @property
    def bvalue(self):
        value = 0.0
        for pos in self.positions:
            value += pos.bvalue
        return value
    
    @property
    def cvalue(self):
        value = 0.0
        for pos in self.positions:
            value += pos.cvalue
        return value
    
    @property
    def overall_change(self):
        end = self.cvalue
        start = self.bvalue
        absolute = end - start
        if start == 0:
            percent = 0
        else:
            percent = round(100.0 / start * absolute,2)
        return absolute, percent 
    
    @property
    def current_change(self):
        change = 0.0
        for pos in self.positions:
            stock, percent = pos.current_change
            change +=stock * pos.quantity
        start = self.cvalue - change
        if start == 0.0:
            percent = 0
        else:
            percent = round(100.0 / start * change,2)
        return change, percent 
     
    def update_positions(self):
        updater.update_stocks([pos.stock for pos in self.positions])
        self.last_update = datetime.now()
        pubsub.publish("stocks.updated", self)



###############################################################
##################       Entities      ########################
###############################################################


#FIXME
class Exchange(Entity):
    elixir.using_options(tablename='exchange')

    name = Field(Unicode(128))
    #stocks = OneToMany('Stock')
    

class Index(Entity):
    elixir.using_options(tablename='indices')
    
    name = Field(Unicode(128))
          
          
class Quotation(Entity):
    elixir.using_options(tablename='quotation')
    
    price = Field(Float)
    date = Field(DateTime)
    stock = ManyToOne('Stock') 

         
class Stock(Entity):
    elixir.using_options(tablename='stock')
    
    isin = Field(Unicode(128))
    name = Field(Unicode(128))
    type = Field(Integer, default=0)
    currency = Field(Unicode(5))
    yahoo_symbol = Field(Unicode(20))        
    exchange = Field(Unicode(128))
    quotations = OneToMany('Quotation')
    price = Field(Float, default=0.0)
    date = Field(DateTime)
    change = Field(Float, default=0.0)
            
    @property      
    def percent(self):
        try: 
            return round(self.change * 100 / (self.price - self.change),2)
        except:
            return 0
    
    def update(self):
        updater.update_stocks([self])
    
    def __str__(self):
        return self.name +' | '+self.exchange
    

class Watchlist(Entity, Container):
    elixir.using_options(tablename='watchlist')

    name = Field(String, primary_key=True)
    last_update = Field(DateTime)
    positions = OneToMany('WatchlistPosition')
    comment = Field(UnicodeText)
    
    def __init__(self, *args, **kwargs):
        Entity.__init__(self, *args, **kwargs)
        Container.__init__(self)
        pubsub.publish("watchlist.created",  self) 
    



class Tag(Entity, Container):
    elixir.using_options(tablename='tag')

    name = Field(String, primary_key=True)
    positions = ManyToMany('PortfolioPosition', inverse='_tags')
    
    def __init__(self, *args, **kwargs):
        Entity.__init__(self, *args, **kwargs)
        pubsub.publish("tag.created",  self) 
    

class Portfolio(Entity, Container):
    elixir.using_options(tablename='portfolio')

    name = Field(String, primary_key=True)
    last_update = Field(DateTime)
    comment = Field(UnicodeText)
    cash = Field(Float, default=0)
    positions = OneToMany('PortfolioPosition')
    transactions = OneToMany('PortfolioTransaction')
    
    def __init__(self, *args, **kwargs):
        Entity.__init__(self, *args, **kwargs)
        pubsub.publish("portfolio.created",  self) 
    
    

class PortfolioPosition(Entity, Position):
    elixir.using_options(tablename='portfolio_position')

    comment = Field(UnicodeText)
    stock = ManyToOne('Stock') 
    portfolio = ManyToOne('Portfolio')
    quantity = Field(Float)
    price = Field(Float)
    date = Field(DateTime)
    transactions = OneToMany('Transaction')
    _tags = ManyToMany('Tag')
    dividends = OneToMany('Dividend')
     
    @property
    def tagstring(self):
        ret = ''
        for t in self._tags:
            ret += t.name + ' '
        return ret 
    
    @property
    def tags(self):
        return self._tags
      
    @tags.setter
    def tags(self, tags):
        taglist = []
        for tagstring in tags:
            #ensure tag exists
            tag = Tag.query.get(tagstring)
            if tag is None:
                tag = Tag(name = tagstring)
            taglist.append(tag)
        self._tags = taglist
    


class WatchlistPosition(Entity, Position):
    elixir.using_options(tablename='watchlist_position')

    comment = Field(UnicodeText)
    stock = ManyToOne('Stock') 
    watchlist = ManyToOne('Watchlist')
    price = Field(Float)
    date = Field(DateTime)
    
    quantity = 1
    #FIXME
    tags_string =''
        

class Transaction(Entity):
    elixir.using_options(tablename='transactions')
    
    date = Field(DateTime)
    position = ManyToOne('PortfolioPosition')
    type = Field(Integer)
    quantity = Field(Integer)
    ta_costs = Field(Float)
    price = Field(Float)
      

class PortfolioTransaction(Entity):
    elixir.using_options(tablename='portolio_transaction')
    date = Field(DateTime)
    portfolio = ManyToOne('Portfolio')
    type = Field(Integer)
    quantity = Field(Integer)
    price = Field(Float)
    ta_costs = Field(Float)

class Dividend(Entity):
    elixir.using_options(tablename='dividend')
    
    date = Field(DateTime)
    positions = ManyToOne('PortfolioPosition')
    type = Field(Integer)
    shares = Field(Integer)
    ta_costs = Field(Float)
    price = Field(Float)
    



    
    
###############################################################
#################       FUNCTIONS      ########################
###############################################################
    
def commit():
    elixir.session.commit()


def flush():
    elixir.drop_all()
    elixir.create_all()
    commit()


def connect(database):
    elixir.metadata.bind = "sqlite:///"+database
    #elixir.metadata.bind.echo = True
    elixir.setup_all()
    elixir.create_all()
    #load_default_values()


def load_default_values():
    stock1 = Stock(name=u'Google', yahoo_symbol=u"GOOG", exchange=u"NASDAQ")
    pf = Portfolio(name=u'Example')
    PortfolioPosition(stock=stock1, portfolio=pf, quantity=10, price=500, tags=['tag1', 'tag2'])
    wl = Watchlist(name=u'Example')


def save_as(filename):
    #FIXME
    print "not implemented"
