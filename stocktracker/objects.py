#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/stocktracker
#    objects.py: Copyright 2009 Wolfgang Steitz <wsteitz(at)gmail.com>
#
#    This file is part of stocktracker.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

from stocktracker import pubsub
from stocktracker.utils import unique
from stocktracker.data_provider import DataProvider
import logging
from datetime import datetime
from stocktracker.session import session

logger = logging.getLogger(__name__)
TYPES = {None: 'n/a', 0:'stock', 1:'fund'}


class Model(object):
    def __init__(self, store):
        self.store = store
        pubsub.subscribe('positionstoolbar.update', self.on_update)
        pubsub.subscribe('menubar.update', self.on_update)
        pubsub.subscribe('shortcut.update', self.on_update)
        session['model'] = self
        
    def initialize(self):
        self.watchlists = self.store.get_watchlists()
        self.portfolios = self.store.get_portfolios()
        self.stocks = self.store.get_stocks()
        self.tags = self.store.get_tags()
        self.data_provider = DataProvider()
        logger.debug('database loaded')
        pubsub.publish('model.database.loaded')
    
    def create_watchlist(self, name):
        id = self.store.create_container(name,'',0,0.0)
        self.watchlists[id] = Watchlist(id, name, self, {})
        
    def create_portfolio(self, name, cash = 0.0):
        id = self.store.create_container(name,'',1,cash)
        self.portfolios[id] = Portfolio(cash, id, name, self, {})
     
    def get_tag(self,tag):
        if tag in self.tags:
            return self.tags[tag]
        else:
            id = self.store.create_tag(tag)
            new_tag = Tag(id, tag, self)
            self.tags[tag] = new_tag
            return new_tag
    
    def get_positions_from_tag(self, tag):
        pos = []
        for key, pf in self.portfolios.iteritems():
            for p in pf:
                if tag in p.tags:
                    pos.append(p)
        return pos
    
    def create_stock(self, symbol, name, type, exchange, currency, isin):
        id = self.store.create_stock(name,symbol, isin, exchange, type, currency, None, None, None)
        stock = Stock(id, name, symbol, isin, exchange, type, currency, None, None, None)
        self.stocks[id] = stock
        return stock
        
    def get_stock(self, symbol, type, update = False):
        stock = None
        for key, val in self.stocks.iteritems():
            if val.symbol == symbol:
                stock = val
        if stock is None:
            name, isin, exchange, currency = self.data_provider.get_info(symbol)
            id = self.store.create_stock(name,symbol,isin, exchange, type, currency, None, None, None)
            stock = Stock(id, name, symbol,isin, exchange, type, currency, None, None, None)
            self.stocks[id] = stock
        if update:
            self.data_provider.update_stock(stock)
        return stock
    
    def check_symbol(self, symbol):
        for key, val in self.stocks.iteritems():
            if symbol == val.symbol:
                return True
        else:
            return self.data_provider.check_symbol(symbol)
    
    def on_update(self, pf):
        self.data_provider.update_stocks([pos.stock for pos in pf])
        pf.last_update = datetime.today()
    
    def create_position(self, stock_id, buy_price, buy_date, quantity, container_id, type):
        id = self.store.create_position(container_id, stock_id, buy_price, buy_date, quantity)
        if type == 0:
            return WatchlistPosition(id, container_id, stock_id, self, buy_price, buy_date, {}, quantity)
        elif type ==1:
            return PortfolioPosition(id, container_id, stock_id, self, buy_price, buy_date, {}, quantity)
           
    def remove(self, item):
        if isinstance(item, Watchlist):
            del self.watchlists[item.id] 
            pubsub.publish("watchlist.removed", item)
        elif isinstance(item, Portfolio):
            del self.portfolios[item.id]
            pubsub.publish("portfolio.removed",  item)
        elif isinstance(item, Tag):
            del self.tags[item.name]
            pubsub.publish("tag.removed", item)
     
    def save(self):
        self.store.save()
    
    def clear(self):
        pubsub.publish('clear!')
        self.__init__(self.store)           


class Container(object):
    def __init__(self, id, name, model, positions, last_update = None, comment = '', **kwargs):
        self.id = id
        self._name = name
        self.comment = comment
        self.model = model
        self.positions = positions
        self._last_update = last_update
        self.type = 'container'
            
    def get_name(self):
        return self._name
        
    def set_name(self, name):
        self._name = name
        pubsub.publish('container.updated', self)
    
    def get_last_update(self):
        return self._last_update
        
    def set_last_update(self, last_update):
        self._last_update = last_update
        pubsub.publish('container.updated', self)
        
    name = property(get_name, set_name)
    last_update = property(get_last_update, set_last_update)
    
    def remove_position(self, position):
        del self.positions[position.id]
        pubsub.publish("container.position.removed", position,  self)
   
    def get_bvalue(self):
        value = 0.0
        for pos in self:
            value += pos.bvalue
        return value
    
    def get_cvalue(self):
        value = 0.0
        for pos in self:
            value += pos.cvalue
        return value
        
    def get_overall_change(self):
        end = self.get_cvalue()
        start = self.get_bvalue()
        absolute = end - start
        if start == 0:
            percent = 0
        else:
            percent = round(100.0 / start * absolute,2)
        return absolute, percent 
    
    def get_current_change(self):
        change = 0.0
        for pos in self:
            stock, percent = pos.current_change
            change +=stock * pos.quantity
        start = self.get_cvalue() - change
        if start == 0.0:
            percent = 0
        else:
            percent = round(100.0 / start * change,2)
        return change, percent    
    
    overall_change = property(get_overall_change)
    current_change = property(get_current_change)
    bvalue = property(get_bvalue)
    total = cvalue = property(get_cvalue)
    
    def __cmp__(self, other):
        return cmp(self.id, other.id)

    def __eq__(self, other):
        return self.id == other.id
        
    def __iter__(self):
        return self.positions.itervalues()    
        
        
class Portfolio(Container):
    def __init__(self,cash, *args, **kwargs):
        Container.__init__(self, *args, **kwargs)
        self._cash = cash
        pubsub.publish("portfolio.created",  self)
        self.type = 'portfolio'
          
    def get_cash(self):
        return self._cash
        
    def set_cash(self, cash):
        self._cash = cash
        pubsub.publish('portfolio.updated',  self)

    cash = property(get_cash, set_cash)            
        
    def add_position(self, stock_id, buy_price, buy_date, quantity):
        pos = self.model.create_position(stock_id, buy_price, buy_date, quantity, self.id,1)
        self.positions[pos.id] = pos
        pubsub.publish("container.position.added",  pos,  self)
        return pos
    
    def merge_positions(self, pos1, pos2):
        quantity = pos1.quantity + pos2.quantity
        buy_price = (pos1.quantity*pos1.price + pos2.quantity*pos2.price) / quantity
        if pos1.date < pos2.date:
            buy_date = pos2.date
        else:
            buy_date = pos1.date
        symbol = self.model.stocks[pos1.stock_id].symbol
        new_pos = self.add_position(symbol, buy_price, buy_date, quantity)
        new_pos.tag(unique(pos1.tags + pos2.tags))
        pubsub.publish('container.position.merged', pos1, pos2, new_pos)
        self.remove_position(pos1)
        self.remove_position(pos2)
    
    
class Watchlist(Container):
    def __init__(self, *args, **kwargs):
        Container.__init__(self, *args, **kwargs)
        logger.debug('watchlist created')
        pubsub.publish("watchlist.created",  self)
        self.type = 'watchlist'

    def add_position(self, symbol, buy_price, buy_date, quantity = 1):
        pos = self.model.create_position(symbol, buy_price, buy_date, quantity, self.id, 0)
        self.positions[pos.id] = pos
        pubsub.publish("container.position.added",  pos,  self)
        return pos
    
class Tag(Container):
    def __init__(self, id, name, model):
        self.id = id
        self._name = name
        self.model = model
        self.type = 'tag'
        
        pubsub.publish("tag.created", self)

    def __iter__(self):
        return iter(self.model.get_positions_from_tag(self.name))
   
class Transaction(object):
    def __init__(self, id, pos_id, type, date, quantity, price, ta_costs):
        self.id = id
        self.pos_id = pos_id
        self.type = type
        self.date = date
        self.quantity = quantity
        self.price = price
        self.ta_costs = ta_costs
        
        pubsub.publish("transaction.created",  self)
        
class Stock(object):
    def __init__(self, id, name, symbol, isin, exchange,type, currency, price, date, change):
        self.id = id
        self.name = name
        self.symbol = symbol
        self.isin = isin
        self.exchange = exchange
        self._currency = currency
        self.price = price
        self.date = date
        self._change = change
        self.type = type
        
        pubsub.publish("stock.created",  self)
          
    def get_currency(self):
        if self._currency == 'EUR':
            return '€'
        elif self._currency == 'USD':
            return '$'
        else:
            return ''
          
    def get_change(self):
        return self._change
        
    def set_change(self, change):
        self._change = change
        pubsub.publish('stock.updated', self)
    
    def update(self):
        session['model'].data_provider.update_stock(self)
          
    def get_percent(self):
        return round(self.change * 100 / (self.price - self.change),2)
          
    percent_change = property(get_percent)
    currency = property(get_currency)
    change = property(get_change, set_change)
    
    def __str__(self):
        return self.name +'  '+self.exchange+'   '+self.symbol#+'  '+self.isin             


class Position(object):
    def __init__(self, id, container_id, stock_id, model, price, date, transactions, quantity = 1, tags = None):
        self.id = id
        self.container_id = container_id
        self.stock_id = stock_id
        self.__quantity = quantity 
        self.model = model
        self.price = price
        self.date = date
        self.transactions = transactions
        if tags == None: 
            self.tags = []
        else: self.tags = tags
        pubsub.publish("position.created", self)
      
    def get_name(self):
        return self.model.stocks[self.stock_id].name
        
    def get_gain(self):
        stock = self.model.stocks[self.stock_id].price - self.price
        absolute = stock * self.quantity
        percent = round(absolute * 100 / (self.price*self.__quantity),2)
        return absolute, percent
    
    def get_current_change(self):
        stock = self.model.stocks[self.stock_id].change
        percent = round(self.model.stocks[self.stock_id].percent_change,2)
        return stock, percent
        
    def get_days_gain(self):
        return self.model.stocks[self.stock_id].change * self.quantity
        
    def get_currency(self):
        return self.model.stocks[self.stock_id].currency
    
    def get_quantity(self):
        return self.__quantity
        
    def set_quantity(self, x):
        self.__quantity = x
        pubsub.publish("position.updated", self)
    
    def get_bvalue(self):
        return self.__quantity * self.price
    
    def get_cvalue(self):
        return self.__quantity * self.model.stocks[self.stock_id].price
        
    def get_current_price(self):
        return self.model.stocks[self.stock_id].price
    
    def get_tags_string(self):
        ret = ''
        for t in self.tags:
            ret += t + ' '
        return ret
        
    def get_type(self):
        return self.model.stocks[self.stock_id].type
    
    def get_type_string(self):
        return TYPES[self.model.stocks[self.stock_id].type]
        
    def get_stock(self):
        return self.model.stocks[self.stock_id]
        
    
    current_price = property(get_current_price)
    current_change =  property(get_current_change)
    cvalue = property(get_cvalue)
    bvalue = property(get_bvalue)
    quantity = property(get_quantity, set_quantity)
    gain = property(get_gain)
    days_gain = property(get_days_gain)
    currency = property(get_currency)
    name = property(get_name)
    tags_string = property(get_tags_string)
    type = property(get_type)
    type_string = property(get_type_string)
    stock = property(get_stock)
     
    def add_transaction(self, type, date, quantity, price, ta_costs):
        id = self.model.store.create_transaction(self.id, type, date, quantity, price, ta_costs)
        ta = Transaction(id, self.id, type, date, quantity, price, ta_costs) 
        self.transactions[ta.id] = ta
        pubsub.publish("position.transaction.added", ta, self)
        
    def remove_transaction(self, transaction):
        del self.positions[transaction.id]
        pubsub.publish("position.transaction.removed", transaction, self)
    
    def tag(self, tags):
        for tagstring in tags:
            #ensure tag exists
            tag = self.model.get_tag(tagstring)
        self.tags = tags
        pubsub.publish("position.tags.changed", [self.model.tags[t] for t in tags], self)
            
    def split(self, n1, n2, date):
        self.quantity = self.quantity / n1 * n2
        self.price = self.price / n1 * n2
        #TODO die transactions müssen auch geändert werden
        self.add_transaction(2, date, 0, 0.0, 0.0)
        
            
    def __iter__(self):
        return self.transactions.itervalues()  

    def __str__(self):
        return str(self.quantity) +' '+ self.get_name()

class WatchlistPosition(Position):
    def __init__(self, *args, **kwargs):
        Position.__init__(self, *args, **kwargs)

class PortfolioPosition(Position):
    def __init__(self, *args, **kwargs):
        Position.__init__(self, *args, **kwargs)
   
        
if __name__ == "__main__":
    pass    
