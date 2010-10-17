#!/usr/bin/env python

import gtk
from stocktracker import pubsub
from stocktracker.gui.gui_utils import Tree, float_to_red_green_string, get_price_string, get_name_string, ContextMenu   
from stocktracker.objects import controller


class ContainerOverviewTab(gtk.VBox):
    
    def __init__(self, item):
        gtk.VBox.__init__(self)
        if item.name == 'Accounts':
            tree = AccountOverviewTree()
        else:
            tree = ContainerOverviewTree(item)
        sw = gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.add(tree)
        
        self.pack_start(sw)
        self.show_all()
        

class AccountOverviewTree(Tree):
    
    def __init__(self):
        Tree.__init__(self)
        self.set_rules_hint(True)
        self.model = gtk.ListStore(object, str, float, int)
        self.set_model(self.model)
        self.create_column(_('Name'), 1)
        self.create_column(_('Amount'), 2)
        self.create_column(_('# Transactions'), 3)
        self._load_accounts()
    
    def _load_accounts(self):
        for acc in controller.getAllAccount():
            self.model.append([acc, 
                               acc.name,  
                               acc.amount, 
                               acc.transaction_count])
        

class ContainerOverviewTree(Tree):
    
    def __init__(self, container):
        self.container = container
        
        Tree.__init__(self)
        self.cols = {'obj':0,
                     'name':1, 
                     'last_price':2, 
                     'change':3, 
                     'change_percent':4,
                      }
        
        self.set_model(gtk.ListStore(object,str, str,float, float))
        
        self.create_column(_('Name'), self.cols['name'])
        self.create_column(_('Last price'), self.cols['last_price'])
        col, cell = self.create_column(_('Change'), self.cols['change'])
        col.set_cell_data_func(cell, float_to_red_green_string, self.cols['change'])
        col, cell = self.create_column(_('Change %'), self.cols['change_percent'])
        col.set_cell_data_func(cell, float_to_red_green_string, self.cols['change_percent'])
        
        def sort_price(model, iter1, iter2):
            item1 = model.get_value(iter1, self.cols['obj'])
            item2 = model.get_value(iter2, self.cols['obj'])
            if item1.price == item2.price: return 0
            elif item1.price < item2.price: return -1
            else: return 1

        self.get_model().set_sort_func(self.cols['last_price'], sort_price)

        self.set_rules_hint(True)    
        self.load_items()
        self.connect("destroy", self.on_destroy)
        self.connect("row-activated", self.on_row_activated)
        self.subscriptions = (
            ('stocks.updated', self.on_stocks_updated),
            ('shortcut.update', self.on_update)
        )
        for topic, callback in self.subscriptions:
            pubsub.subscribe(topic, callback)
            
        self.selected_item = None

    def on_update(self):
        self.container.update_positions()

    def on_row_activated(self, treeview, path, view_column):
        item = self.get_model()[path][0]
        pubsub.publish('overview.item.selected', item)

    def on_destroy(self, x):
        for topic, callback in self.subscriptions:
            pubsub.unsubscribe(topic, callback)

    def load_items(self):
        items = []
        if self.container.name == 'Tags':
            items = controller.getAllTag()
        elif self.container.name == 'Watchlists':
            items = controller.getAllWatchlist()
        elif self.container.name == 'Portfolios':
            items = controller.getAllPortfolio()
        elif self.container.name == 'Indices':
            items = controller.getAllIndex()
        for item in items:
            self.insert_item(item)

    def on_stocks_updated(self, container):
        if container.id == self.container.id:
            for row in self.get_model():
                item = row[0]
                row[self.cols['last_price']] = get_price_string(item)
                row[self.cols['change']] = item.change
                row[self.cols['change_percent']] = item.percent
        
    def insert_item(self, item):
        self.get_model().append([item, 
                               item.name,  
                               get_price_string(item), 
                               item.change,
                               item.percent])
