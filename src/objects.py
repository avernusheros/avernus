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

import updater, pubsub

class Model(object):
    def __init__(self, store):
        self.store = store
        pubsub.subscribe( 'positionstoolbar.update', self.on_update_clicked)
        
    def initialize(self):
        self.watchlists = self.store.get_watchlists()
        self.portfolios = self.store.get_portfolios()
        self.stocks = self.store.get_stocks()
    
    def create_watchlist(self, name):
        id = self.store.create_container(name,'',0,0.0)
        self.watchlists[id] = Watchlist(id, name, self, {})
        
    def create_portfolio(self, name, cash = 0.0):
        id = self.store.create_container(name,'',1,cash)
        self.portfolios[id] = Portfolio(cash, id, name, self, {})
        
    def get_stock(self, symbol, update = False):
        stock = None
        for key, val in self.stocks.iteritems():
            if val.symbol == symbol:
                stock = val
        if stock is None:
            name, isin, exchange, currency = updater.get_info(symbol)
            id = self.store.create_stock(name,symbol,isin, exchange, currency, None, None, None)
            stock = Stock(id, name, symbol,isin, exchange, currency, None, None, None)
            self.stocks[id] = stock
        if update:
            updater.update_stock(stock)
        return stock
    
    def on_update_clicked(self):
        updater.update_stocks([stock for key, stock in self.stocks.iteritems()])
    
    def create_position(self, symbol, buy_price, buy_date, quantity, container_id, type):
        stock = self.get_stock(symbol)
        id = self.store.create_position(container_id, stock.id, buy_price, buy_date, quantity)
        if type == 0:
            return WatchlistPosition(id, container_id, stock.id, self, buy_price, buy_date, {}, quantity)
        elif type ==1:
            return PortfolioPosition(id, container_id, stock.id, self, buy_price, buy_date, {}, quantity)
           
    def remove(self, item):
        if isinstance(item, Watchlist):
            del self.watchlists[item.id] 
            pubsub.publish("watchlist.removed", item)
        elif isinstance(item, Portfolio):
            del self.portfolios[item.id]
            pubsub.publish("portfolio.removed",  item)
     
    def save(self):
        self.store.save()


class Container(object):
    def __init__(self, id, name, model, positions, comment = '', **kwargs):
        self.id = id
        self._name = name
        self.comment = comment
        self.model = model
        self.positions = positions
            
    def get_name(self):
        return self._name
        
    def set_name(self, name):
        self._name = name
        pubsub.publish('container.updated.name',  self)
        
    name = property(get_name, set_name)
    

        
    def remove_position(self, position):
        del self.positions[position.id]
        pubsub.publish("container.position.removed", position,  self)
   
    def get_bvalue(self):
        value = 0.0
        for pos in self.positions.itervalues():
            value += pos.bvalue
        return value
    
    def get_cvalue(self):
        value = 0.0
        for pos in self.positions.itervalues():
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
        for pos in self.positions.itervalues():
            stock, percent, absolute = pos.current_change
            change +=absolute
        start = self.get_cvalue() - change
        if start == 0.0:
            percent = 0
        else:
            percent = round(100.0 / start * change,2)
        return change, percent    
    
    overall_change = property(get_overall_change)
    current_change = property(get_current_change)
    bvalue = property(get_bvalue)
    cvalue = property(get_cvalue)        
  
    def __cmp__(self, other):
        return cmp(self.id, other.id)

    def __eq__(self, other):
        return self.id == other.id
        
    def __iter__(self):
        return self.positions.itervalues()    
        
        
class Portfolio(Container):
    def __init__(self,cash, *args, **kwargs):
        Container.__init__(self, *args, **kwargs)
        self.cash = cash
        pubsub.publish("portfolio.created",  self)
        
    def add_position(self, symbol, buy_price, buy_date, quantity):
        pos = self.model.create_position(symbol, buy_price, buy_date, quantity, self.id,1)
        self.positions[pos.id] = pos
        pubsub.publish("container.position.added",  pos,  self)
        return pos
    
    
class Watchlist(Container):
    def __init__(self, *args, **kwargs):
        Container.__init__(self, *args, **kwargs)
        pubsub.publish("watchlist.created",  self)

    def add_position(self, symbol, buy_price, buy_date, quantity):
        pos = self.model.create_position(symbol, buy_price, buy_date, quantity, self.id, 0)
        self.positions[pos.id] = pos
        pubsub.publish("container.position.added",  pos,  self)
        return pos
    
   
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
    def __init__(self, id, name, symbol, isin, exchange, currency, price, date, change):
        self.id = id
        self.name = name
        self.symbol = symbol
        self.isin = isinstance
        self.exchange = exchange
        self._currency = currency
        self.price = price
        self.date = date
        self.change = change
        
        pubsub.publish("stock.created",  self)
          
    def get_currency(self):
        if self._currency == 'EUR':
            return '€'
        elif self._currency == 'USD':
            return '$'
        else:
            return ''
          
    def get_percent(self):
        return round(self.change * 100 / (self.price - self.change),2)
          
    percent_change = property(get_percent)
    currency = property(get_currency)
             

class Position(object):
    def __init__(self, id, container_id, stock_id, model, price, date, transactions, quantity = 1):
        self.id = id
        self.container_id = container_id
        self.stock_id = stock_id
        self.__quantity = quantity 
        self.model = model
        self.price = price
        self.date = date
        self.transactions = transactions
        pubsub.publish("position.created", self)
        
    def get_overall_change(self):
        stock = self.model.stocks[self.stock_id].price - self.price
        absolute = stock * self.__quantity
        percent = round(absolute * 100 / (self.price*self.__quantity),2)
        return stock, percent, absolute
    
    def get_current_change(self):
        stock = self.model.stocks[self.stock_id].change
        absolute = stock * self.__quantity
        percent = round(self.model.stocks[self.stock_id].percent_change,2)
        return stock, percent, absolute
        
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
    
    current_change =  property(get_current_change)
    cvalue = property(get_cvalue)
    bvalue = property(get_bvalue)
    quantity = property(get_quantity, set_quantity)
    overall_change = property(get_overall_change)
    currency = property(get_currency)
     
    def add_transaction(self, type, date, quantity, price, ta_costs):
        id = self.model.store.create_transaction(self.id, type, date, quantity, price, ta_costs)
        ta = Transaction(id, self.id, type, date, quantity, price, ta_costs) 
        self.transactions[ta.id] = ta
        pubsub.publish("position.transaction.added", ta, self)
        
    def remove_transaction(self, transaction):
        del self.positions[transaction.id]
        pubsub.publish("position.transaction.removed", transaction, self)
    
    def __iter__(self):
        return self.transactions.itervalues()  

class WatchlistPosition(Position):
    def __init__(self, *args, **kwargs):
        Position.__init__(self, *args, **kwargs)

class PortfolioPosition(Position):
    def __init__(self, *args, **kwargs):
        Position.__init__(self, *args, **kwargs)
 
        
if __name__ == "__main__":
    pass    
