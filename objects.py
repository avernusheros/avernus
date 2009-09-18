# -*- coding: iso-8859-15 -*-

from pubsub import pub
import updater

class Model(object):
    def __init__(self, store):
        self.store = store
        pub.subscribe(self.on_update_clicked, 'positionstoolbar.update')
        
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
    
    def create_position(self, symbol, buy_price, buy_date, quantity, container_id):
        stock = self.get_stock(symbol)
        id = self.store.create_position(container_id, stock.id, buy_price, buy_date, quantity)
        return Position(id, container_id, stock.id, self, buy_price, buy_date, {}, quantity)
           
    def remove(self, item):
        if isinstance(item, Watchlist):
            del self.watchlists[item.id] 
            pub.sendMessage("watchlist.removed", item = item)
        elif isinstance(item, Portfolio):
            del self.portfolios[item.id]
            pub.sendMessage("portfolio.removed", item = item)
     
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
        pub.sendMessage('container.updated.name', item = self)
        
    name = property(get_name, set_name)
    
    def add_position(self, symbol, buy_price, buy_date, quantity):
        pos = self.model.create_position(symbol, buy_price, buy_date, quantity, self.id)
        self.positions[pos.id] = pos
        pub.sendMessage("container.position.added", item = pos, container = self)
        return pos
        
    def remove_position(self, position):
        del self.positions[position.id]
        pub.sendMessage("container.position.removed", item = position, container = self)
   
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
        pub.sendMessage("portfolio.created",item =  self)
        

    
    
class Watchlist(Container):
    def __init__(self, *args, **kwargs):
        Container.__init__(self, *args, **kwargs)
        pub.sendMessage("watchlist.created", item = self)
    
   
class Transaction(object):
    def __init__(self, id, pos_id, type, date, quantity, price, ta_costs):
        self.id = id
        self.pos_id = pos_id
        self.type = type
        self.date = date
        self.quantity = quantity
        self.price = price
        self.ta_costs = ta_costs
        
        pub.sendMessage("transaction.created", item = self)
        
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
        
        pub.sendMessage("stock.created", item = self)
          
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
        pub.sendMessage("position.created",item = self)
        
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
        pub.sendMessage("position.updated", item = self)
    
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
        pub.sendMessage("position.transaction.added", item = ta, position = self)
        
    def remove_transaction(self, transaction):
        del self.positions[transaction.id]
        pub.sendMessage("position.transaction.removed", item = transaction, position = self)
    
    def __iter__(self):
        return self.transactions.itervalues()  

 
        
if __name__ == "__main__":
    pass    
