#!/usr/bin/env python

import gtk
from stocktracker import pubsub
from stocktracker.gui.gui_utils import Tree, get_datetime_string, get_name_string
import stocktracker.objects
from stocktracker.objects import controller


class TransactionsTab(gtk.ScrolledWindow):
    def __init__(self, item):
        gtk.ScrolledWindow.__init__(self)
        transactions_tree = TransactionsTree(item)
        self.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        self.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        self.add(transactions_tree)
        self.show_all()


class TransactionsTree(Tree):
    def __init__(self, portfolio):
        self.portfolio = portfolio
        Tree.__init__(self)
        #object, name, price, change
        self.set_model(gtk.TreeStore(object,str, str, str,str, str, str))
        
        self.create_column(_('Action'), 1)
        self.create_column(_('Name'), 2)
        self.create_column(_('Date'), 3)
        self.create_column(_('Shares'), 4)
        self.create_column(_('Price'), 5)
        self.create_column(_('Transaction Costs'), 6)
        
        self.load_transactions()
        pubsub.subscribe('transaction.added', self.on_transaction_created)
        
    def load_transactions(self):
        list = []
        if isinstance(self.portfolio, stocktracker.objects.container.Portfolio):
            list = [self.portfolio]
        else:
            list = self.portfolio
        for port in list:
            for ta in controller.getTransactionForPortfolio(port):
                self.insert_transaction(ta)
      
    def on_transaction_created(self, ta):
        if ta.portfolio is None:
            portfolio = ta.position.portfolio
        else:
            portfolio = ta.portfolio
        if portfolio.id == self.portfolio.id:
            self.insert_transaction(ta)    
    
    def get_action_string(self, type):
        if type == 1:
            return 'BUY'
        elif type == 0:
            return 'SELL'
        elif type == 2:
            return 'SPLIT'
        elif type == 3:
            return 'DEPOSIT'
        elif type == 4:
            return 'WITHDRAW'
        else:
            return ''
        
    def insert_transaction(self, ta):
        model = self.get_model()
        if model:
            if ta.position is None: #a portfolio related transaction
                model.append(None, [ta, self.get_action_string(ta.type), '', get_datetime_string(ta.date), ta.quantity, ta.price, ta.costs])
            else:
                model.append(None, [ta, self.get_action_string(ta.type), get_name_string(ta.position.stock), get_datetime_string(ta.date), ta.quantity, ta.price, ta.costs])

