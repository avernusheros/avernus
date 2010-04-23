#!/usr/bin/env python

import gtk
from stocktracker import pubsub, model
from stocktracker.gui.treeviews import Tree
from stocktracker.gui.gui_utils import get_datetime_string, get_name_string


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
        pubsub.subscribe('position.transaction.added', self.on_transaction_created)
        pubsub.subscribe('portfolio.transaction.added', self.on_pf_transaction_created)
        
    def load_transactions(self):
        for pos in self.portfolio.positions:
            for ta in pos.transactions:
                self.insert_transaction(ta, pos)
        if isinstance(self.portfolio, model.Portfolio):
            for ta in self.portfolio.transactions:
                self.insert_pf_transaction(ta)
    
    def on_pf_transaction_created(self, portfolio, ta):
        if portfolio.name == self.portfolio.name:
            self.insert_pf_transaction(ta)
    
    def on_transaction_created(self, position, item):
        if position.portfolio.name == self.portfolio.name:
            self.insert_transaction(item, position)    
    
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
        
    def insert_transaction(self, ta, pos):
        model = self.get_model()
        if model:
            model.append(None, [ta, self.get_action_string(ta.type), get_name_string(pos.stock), get_datetime_string(ta.date), ta.quantity, ta.price, ta.ta_costs])

    def insert_pf_transaction(self, ta):
        self.get_model().append(None, [ta, self.get_action_string(ta.type), '', get_datetime_string(ta.date), ta.quantity, ta.price, ta.ta_costs]) 

