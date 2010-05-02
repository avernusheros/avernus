#!/usr/bin/env python

import gtk
from stocktracker import pubsub
from stocktracker.gui.gui_utils import Tree, float_to_red_green_string, get_price_string, get_name_string, ContextMenu   
from stocktracker.gui.plot import ChartWindow


class IndexPositionsTab(gtk.VBox):
    def __init__(self, index):
        gtk.VBox.__init__(self)
        self.index = index
        index_tree = IndexPositionsTree(index)
        hbox = gtk.HBox()
        tb = IndexToolbar(index, index_tree)
        hbox.pack_start(tb, expand = True, fill = True)
        
        self.price_label = label = gtk.Label()
        hbox.pack_start(label)
        hbox.pack_start(gtk.VSeparator(), expand = False, fill = False)
        self.change_label = label = gtk.Label()
        hbox.pack_start(label, expand = False, fill = False)
        self.last_update_label = label = gtk.Label()
        hbox.pack_start(label, expand = False, fill = False)
        
        #hbox.pack_start(gtk.VSeparator(), expand = False, fill = False)
        
        sw = gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.add(index_tree)
        self.pack_start(hbox, expand=False, fill=False)
        self.pack_start(sw)
        
        #pubsub.subscribe('container.updated', self.on_container_update)
        
        
        self.show_all()
        
    
class IndexToolbar(gtk.Toolbar):
    def __init__(self, index, tree):
        gtk.Toolbar.__init__(self)
        self.index = index
        self.tree = tree
        self.conditioned = []
        
        button = gtk.ToolButton('gtk-edit')
        #button.set_label('Remove tag'
        button.connect('clicked', self.on_edit_clicked)
        button.set_tooltip_text('Edit selected stock') 
        self.insert(button,-1)
        #FIXME
        #self.conditioned.append(button)
        button.set_sensitive(False)
                
        button = gtk.ToolButton('gtk-info')
        button.connect('clicked', self.on_chart_clicked)
        button.set_tooltip_text('Chart selected stock')
        self.conditioned.append(button) 
        self.insert(button,-1)        
        
        self.insert(gtk.SeparatorToolItem(),-1)
        
        button = gtk.ToolButton('gtk-refresh')
        button.connect('clicked', self.on_update_clicked)
        button.set_tooltip_text('Update stock quotes') 
        self.insert(button,-1)
        
        button = gtk.ToolButton('gtk-info')
        button.connect('clicked', self.on_indexchart_clicked)
        button.set_tooltip_text('Chart index '+self.index.name)
        self.insert(button,-1) 
        
        self.on_unselect()
        pubsub.subscribe('indextree.unselect', self.on_unselect)
        pubsub.subscribe('indextree.select', self.on_select)
        
    def on_unselect(self):
        for button in self.conditioned:
            button.set_sensitive(False)       
        
    def on_select(self, obj):
        for button in self.conditioned:
            button.set_sensitive(True)
           
    def on_add_clicked(self, widget):
        pubsub.publish('positionstoolbar.add')  
      
    def on_update_clicked(self, widget):
        self.index.update_positions()
           
    def on_edit_clicked(self, widget):
        #FIXME
        pass
        
    def on_chart_clicked(self, widget):
        if self.tree.selected_item is None:
            return
        stock, iter = self.tree.selected_item
        d = ChartWindow(stock)
    
    def on_indexchart_clicked(self, widget):
        d = ChartWindow(self.index)
        
        
class StockContextMenu(ContextMenu):
    def __init__(self, position):
        ContextMenu.__init__(self)
        self.position = position
        
        #self.add_item(_('Edit position'),  self.__edit_position, 'gtk-edit')
        self.add_item(_('Chart position'),  self.on_chart_position, 'gtk-info')
       
    def __edit_position(self, *arg):
        #FIXME
        pass
    
    def on_chart_position(self, *arg):
        ChartWindow(self.stock)
        

class IndexPositionsTree(Tree):
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
    
        self.load_positions()
        
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
            if obj.__name__ == 'Stock':
                pubsub.publish('indextree.select', obj)
                return
        pubsub.publish('indextree.unselect')

    def on_destroy(self, x):
        for topic, callback in self.subscriptions:
            pubsub.unsubscribe(topic, callback)

    def load_positions(self):
        for pos in self.container.positions:
            self.insert_position(pos)

    def on_stocks_updated(self, container):
        if container.id == self.container.id:
            for row in self.get_model():
                item = row[0]
                row[self.cols['last_price']] = get_price_string(item)
                row[self.cols['change']] = item.change
                row[self.cols['change_percent']] = item.percent
        
    def insert_position(self, stock):
        self.get_model().append(None, [stock, 
                                       get_name_string(stock),  
                                       get_price_string(stock), 
                                       stock.change,
                                       stock.percent])
