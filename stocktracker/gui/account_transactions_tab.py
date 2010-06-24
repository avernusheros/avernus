#!/usr/bin/env python

import gtk
from stocktracker import pubsub
from stocktracker.gui.gui_utils import Tree, get_datetime_string
import stocktracker.objects
from stocktracker.objects import controller


class AccountTransactionTab(gtk.HPaned):
    def __init__(self, item):
        gtk.HPaned.__init__(self)
        
        sw = gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        self.transactions_tree = TransactionsTree(item)
        sw.add(self.transactions_tree)
        self.pack1(sw)
        
        sw = gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        self.category_tree = CategoriesTree()
        sw.add(self.category_tree)
        self.pack2(sw)        
        
        self.show_all()
    
    def show(self):
        self.transactions_tree.clear()
        self.transactions_tree.load_transactions()
        self.category_tree.clear()
        self.category_tree.load_categories()


class TransactionsTree(Tree):
    def __init__(self, account):
        self.account = account
        Tree.__init__(self)
        #object, name, price, change
        self.set_model(gtk.TreeStore(object,str, int, str,str))
        
        self.create_column(_('Description'), 1)
        self.create_column(_('Amount'), 2)
        self.create_column(_('Category'), 3)
        self.create_column(_('Date'), 4)
        
        #pubsub.subscribe('transaction.added', self.on_transaction_created)
        
    def load_transactions(self):
        for ta in controller.getTransactionsForAccount(self.account):
            self.insert_transaction(ta)
    
    def insert_transaction(self, ta):
        self.get_model().append(None, [ta, ta.description, ta.category.name, get_datetime_string(ta.date)])


class CategoriesTree(Tree):
    def __init__(self):
        Tree.__init__(self)
        #object, name, price, change
        self.set_model(gtk.TreeStore(object, str))
        
        self.create_column(_('Name'), 1)
        
    def load_categories(self):
        for cat in controller.getAllAccountCategories():
            self.insert_item(cat)
    
    def insert_item(self, cat):
        self.get_model().append(None, [cat, cat.name])

