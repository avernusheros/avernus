#!/usr/bin/env python

import gtk
from stocktracker import pubsub
from stocktracker.gui.treeviews import Tree
from stocktracker.gui.gui_utils import float_to_red_green_string, get_price_string, get_name_string, ContextMenu   
from stocktracker.gui.plot      import ChartWindow
from stocktracker.objects import controller


class ContainerOverviewTab(gtk.VBox):
    def __init__(self, item):
        gtk.VBox.__init__(self)
        tree = ContainerOverviewTree(item)

        sw = gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.add(tree)
        
        self.pack_start(sw)
        self.show_all()
        

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
        
        def float_to_string(column, cell, model, iter, user_data):
            text =  str(round(model.get_value(iter, user_data), 2))
            cell.set_property('text', text)
        
        self.set_model(gtk.TreeStore(object,str, str,float, float))
        
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
        
        self.connect('button-press-event', self.on_button_press_event)
        self.connect('cursor_changed', self.on_cursor_changed)
        self.connect("destroy", self.on_destroy)
        
        self.subscriptions = (
            ('stocks.updated', self.on_stocks_updated),
            ('shortcut.update', self.on_update)
        )
        for topic, callback in self.subscriptions:
            pubsub.subscribe(topic, callback)
            
        self.selected_item = None

    def on_update(self):
        self.container.update_positions()

    def on_button_press_event(self, widget, event):
        if event.button == 3:
            if self.selected_item is not None:
                obj, iter = self.selected_item
                StockContextMenu(obj).show(event)
    
    def on_cursor_changed(self, widget):
        #Get the current selection in the gtk.TreeView
        selection = widget.get_selection()
        # Get the selection iter
        treestore, selection_iter = selection.get_selected()
        if (selection_iter and treestore):
            #Something is selected so get the object
            obj = treestore.get_value(selection_iter, 0)
            self.selected_item = obj, selection_iter
            if isinstance(obj, model.Stock):
                pubsub.publish('indextree.select', obj)
                return
        pubsub.publish('indextree.unselect')

    def on_destroy(self, x):
        for topic, callback in self.subscriptions:
            pubsub.unsubscribe(topic, callback)

    def load_items(self):
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
        self.get_model().append(None, [item, 
                                       item.name,  
                                       get_price_string(item), 
                                       item.change,
                                       item.percent])
