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
        self.watchlists[id] = Watchlist(id, name, self)
        
    def create_portfolio(self, name, cash = 0.0):
        id = self.store.create_container(name,'',1,cash)
        self.portfolios[id] = Portfolio(cash, id, name, self)
        
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
    
    def create_position(self, symbol, buy_price, buy_date, amount, container_id):
        stock = self.get_stock(symbol)
        id = self.store.create_position(container_id, stock.id, buy_price, buy_date, amount)
        return Position(id, container_id, stock.id, self, buy_price, buy_date, amount)
        
    def get_positions(self, container_id):
        return self.store.get_positions(container_id)
    
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
    def __init__(self, id, name, model, comment = '', **kwargs):
        self.id = id
        self._name = name
        self.comment = comment
        self.model = model
        self.positions = model.get_positions(id)
            
    def get_name(self):
        return self._name
        
    def set_name(self, name):
        self._name = name
        pub.sendMessage('container.updated.name', item = self)
        
    name = property(get_name, set_name)
    
    def add_position(self, symbol, buy_price, buy_date, amount):
        pos = self.model.create_position(symbol, buy_price, buy_date, amount, self.id)
        self.positions[pos.id] = pos
        pub.sendMessage("container.position.added", item = pos, container = self)
        
    def remove_position(self, position):
        del self.positions[position.id]
        pub.sendMessage("container.position.removed", item = position, container = self)
        
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
          
    currency = property(get_currency)
             
        
class Position(object):
    def __init__(self, id, container_id, stock_id, model, price, date, amount = 1):
        self.id = id
        self.container_id = container_id
        self.stock_id = stock_id
        self.amount = amount 
        self.model = model
        self.price = price
        self.date = date
        pub.sendMessage("position.created",item =  self)
        
    def get_change(self):
        return self.model.stocks[self.stock_id].price - self.price
    
    def get_currency(self):
        return self.model.stocks[self.stock_id].currency
    
    change = property(get_change)
    currency = property(get_currency)

if __name__ == "__main__":
    pass    
