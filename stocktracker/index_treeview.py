#!/usr/bin/env python

from stocktracker.treeviews import Tree, get_name_string, datetime_format, get_datetime_string
import gtk, os
from stocktracker import pubsub


class IndexPositionsTab(gtk.VBox):
    def __init__(self, index):
        gtk.VBox.__init__(self)
        self.index = index
        positions_tree = IndexPositionsTree(index)
        hbox = gtk.HBox()
        #tb = PositionsToolbar(pf)
        #hbox.pack_start(tb, expand = True, fill = True)
        
        self.today_label = label = gtk.Label()
        hbox.pack_start(label)
        hbox.pack_start(gtk.VSeparator(), expand = False, fill = False)
        self.overall_label = label = gtk.Label()
        hbox.pack_start(label, expand = False, fill = False)
        
        hbox.pack_start(gtk.VSeparator(), expand = False, fill = False)
        self.last_update_label = label = gtk.Label()
        hbox.pack_start(label, expand = False, fill = False)
        sw = gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.add(positions_tree)
        self.pack_start(hbox, expand=False, fill=False)
        self.pack_start(sw)
        
        self.on_container_update(self.index)
        pubsub.subscribe('container.updated', self.on_container_update)
       
        self.show_all()
        
    def on_container_update(self, container):
        #FIXME
        return
        if self.pf == container:
            text = '<b>' + _('Day\'s gain')+'</b>\n'+self.get_change_string(self.pf.current_change)
            self.today_label.set_markup(text)
            text = '<b>'+_('Gain')+'</b>\n'+self.get_change_string(self.pf.overall_change)
            self.overall_label.set_markup(text)
            
            if isinstance(container, model.Portfolio):
                text = '<b>'+_('Investments')+'</b> :'+str(round(self.pf.cvalue,2))
                text += '\n<b>'+_('Cash')+'</b> :'+str(round(self.pf.cash,2))
                self.total_label.set_markup(text)
            else:
                text = '<b>'+_('Total')+'</b>\n'+str(round(self.pf.cvalue,2))
                self.total_label.set_markup(text)
            
            if isinstance(container, model.Portfolio) or isinstance(container, model.Watchlist):
                text = '<b>'+_('Last update')+'</b>\n'+datetime_format(self.pf.last_update)
                self.last_update_label.set_markup(text)
        
    def get_change_string(self, item):
        change, percent = item
        if change is None:
            return 'n/a'
        text = str(percent) + '%' + ' | ' + str(round(change,2))
        if change < 0.0:
            text = '<span foreground="red">'+ text + '</span>'
        else:
            text = '<span foreground="dark green">'+ text + '</span>'
        return text

    


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
        
        def float_to_red_green_string(column, cell, model, iter, user_data):
            num = round(model.get_value(iter, user_data), 2)
            if num < 0:
                markup =  '<span foreground="red">'+ str(num) + '</span>'
            elif num > 0:
                markup =  '<span foreground="dark green">'+ str(num) + '</span>'
            else:
                markup =  str(num)
            cell.set_property('markup', markup)
        
        self.set_model(gtk.TreeStore(object,str, str,float, float))
        
        self.create_column(_('Name'), self.cols['name'])
        self.create_column(_('Last price'), self.cols['last_price'])
        col, cell = self.create_column(_('Change'), self.cols['change'])
        col.set_cell_data_func(cell, float_to_red_green_string, self.cols['change'])
        col, cell = self.create_column(_('Change %'), self.cols['change_percent'])
        col.set_cell_data_func(cell, float_to_red_green_string, self.cols['change_percent'])
        
        
        def sort_current_price(model, iter1, iter2):
            item1 = model.get_value(iter1, self.cols['obj'])
            item2 = model.get_value(iter2, self.cols['obj'])
            if item1.current_price == item2.current_price: return 0
            elif item1.current_price < item2.current_price: return -1
            else: return 1

        self.get_model().set_sort_func(self.cols['last_price'], sort_current_price)

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
                PositionContextMenu(obj).show(event)
    
    def on_cursor_changed(self, widget):
        #FIXME
        return
        #Get the current selection in the gtk.TreeView
        selection = widget.get_selection()
        # Get the selection iter
        treestore, selection_iter = selection.get_selected()
        if (selection_iter and model):
            #Something is selected so get the object
            obj = treestore.get_value(selection_iter, 0)
            self.selected_item = obj, selection_iter
            if isinstance(obj, model.Position):
                pubsub.publish('positionstree.select', obj)
                return
        pubsub.publish('positionstree.unselect')

    def on_destroy(self, x):
        for topic, callback in self.subscriptions:
            pubsub.unsubscribe(topic, callback)

    def load_positions(self):
        for pos in self.container.positions:
            self.insert_position(pos)

    def on_stocks_updated(self, container):
        if container.name == self.container.name:
            for row in self.get_model():
                item = row[0]
                row[self.cols['last_price']] = self.get_price_string(item)
                row[self.cols['change']] = item.current_change[0]
                row[self.cols['change_percent']] = item.current_change[1]
                row[self.cols['gain']] = item.gain[0]
                row[self.cols['gain_percent']] = item.gain[1]
                row[self.cols['days_gain']] = item.days_gain
                row[self.cols['mkt_value']] = round(item.cvalue,2)

    def get_price_string(self, item):
        if item.price is None:
            return 'n/a'
        return str(round(item.price,2)) +'\n' +'<small>'+get_datetime_string(item.date)+'</small>'
        
    def insert_position(self, stock):
        self.get_model().append(None, [stock, 
                                       get_name_string(stock),  
                                       self.get_price_string(stock), 
                                       stock.change,
                                       stock.percent])
