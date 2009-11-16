#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/stocktracker
#    treeviews.py: Copyright 2009 Wolfgang Steitz <wsteitz(at)gmail.com>
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

import gtk, string,  logging, pytz
import objects, dialogs, config, pubsub

logger = logging.getLogger(__name__)


def to_local_time(date):
    if date is not None:
        date = date.replace(tzinfo = pytz.utc)
        date = date.astimezone(pytz.timezone(config.timezone))
        return date.replace(tzinfo = None)

def get_datetime_string(date):
    if date is not None:
        if date.hour == 0 and date.minute == 0 and date.second == 0:
            return str(to_local_time(date).date())
        else:
            return str(to_local_time(date))
    return ''
    
def get_name_string(stock):
    return '<b>'+stock.name+'</b>' + '\n' + '<small>'+stock.symbol+'</small>' + '\n' + '<small>'+stock.exchange+'</small>'
 

def get_green_red_string(num):
    if num < 0.0:
        text = '<span foreground="red">'+ str(num) + '</span>'
    else:
        text = '<span foreground="dark green">'+ str(num) + '</span>'
    return text


class Category(object):
    def __init__(self, name):
        self.name = name

class Tree(gtk.TreeView):
    def __init__(self):
        self.selected_item = None
        gtk.TreeView.__init__(self)

    
    def create_column(self, name, attribute):
        column = gtk.TreeViewColumn(name)
        self.append_column(column)
        cell = gtk.CellRendererText()
        column.pack_start(cell, expand = True)
        column.add_attribute(cell, "markup", attribute)
        column.set_sort_column_id(attribute)
        return column, cell

    
    def find_item(self, id):
        def search(rows):
            if not rows: return None
            for row in rows:
                if row[0] == id:
                    return row 
                result = search(row.iterchildren())
                if result: return result
            return None
        return search(self.get_model())



class MainTree(Tree):
    def __init__(self, model):
        self.model = model
        
        Tree.__init__(self)
        #id, object, icon, name
        self.set_model(gtk.TreeStore(int, object,gtk.gdk.Pixbuf, str))
        
        self.set_headers_visible(False)
             
        column = gtk.TreeViewColumn()
        # Icon Renderer
        renderer = gtk.CellRendererPixbuf()
        column.pack_start(renderer, expand = False)
        column.add_attribute(renderer, "pixbuf", 2)
        # Text Renderer
        renderer = gtk.CellRendererText()
        column.pack_start(renderer, expand = True)
        column.add_attribute(renderer, "markup", 3)
        self.append_column(column)
        
        self.insert_categories()
       

        self.connect('cursor_changed', self.on_cursor_changed)
        pubsub.subscribe("watchlist.created", self.insert_watchlist)
        pubsub.subscribe("portfolio.created", self.insert_portfolio)
        pubsub.subscribe("tag.created", self.insert_tag)
        pubsub.subscribe( "maintoolbar.remove", self.on_remove)
        pubsub.subscribe("maintoolbar.edit", self.on_edit)
        pubsub.subscribe( "container.updated", self.on_updated)
        pubsub.subscribe("model.database.loaded", self.on_database_loaded)
        
        self.selected_item = None


    def insert_categories(self):
        self.pf_iter = self.get_model().append(None, [-1, Category('Portfolios'),None,_("<b>Portfolios</b>")])
        self.wl_iter = self.get_model().append(None, [-1, Category('Watchlists'),None,_("<b>Watchlists</b>")])
        self.tag_iter = self.get_model().append(None, [-1, Category('Tags'),None,_("<b>Tags</b>")])

    def insert_watchlist(self, item):
        self.get_model().append(self.wl_iter, [item.id, item, None, item.name])
    
    def insert_portfolio(self, item):
        self.get_model().append(self.pf_iter, [item.id, item, None, item.name])
         
    def insert_tag(self, item):
        self.get_model().append(self.tag_iter, [item.id, item, None, item.name])
         
    def on_remove(self):
        if self.selected_item is None:
            return
        obj, iter = self.selected_item
        if isinstance(obj, objects.Watchlist) or isinstance(obj, objects.Portfolio) or isinstance(obj, objects.Tag):
            dlg = gtk.MessageDialog(None, 
                 gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION, 
                    gtk.BUTTONS_OK_CANCEL, _("Are you sure?"))
            response = dlg.run()
            dlg.destroy()
            if response == gtk.RESPONSE_OK:
                self.model.remove(obj)
                self.get_model().remove(iter)  
    
    def on_updated(self, item):
        row = self.find_item(item.id)
        if row: 
            row[1] = item
            row[3] = item.name
    
    def on_cursor_changed(self, widget):
        #Get the current selection in the gtk.TreeView
        selection = widget.get_selection()
        # Get the selection iter
        model, selection_iter = selection.get_selected()
        if (selection_iter and model):
            #Something is selected so get the object
            obj = model.get_value(selection_iter, 1)
            self.selected_item = obj, selection_iter
            pubsub.publish('maintree.selection', obj)        
        
    def on_edit(self):
        if self.selected_item is None:
            return
        obj, iter = self.selected_item
        if isinstance(obj, objects.Watchlist):
            dialogs.EditWatchlist(obj)
        elif isinstance(obj, objects.Portfolio):
            dialogs.EditPortfolio(obj)

    def on_database_loaded(self):
        self.expand_all()
    
class PositionsTree(Tree):
    def __init__(self, container, model, type):
        #type 0=wl 1=pf
        self.model = model
        self.container = container
        self.type = type
        Tree.__init__(self)
        self.cols = {'id':0,
                     'obj':1,
                     'name':2, 
                     'start':3, 
                     'last_price':4, 
                     'change':5, 
                     'gain':6,
                     'shares':7, 
                     'buy_value':8,
                     'mkt_value':9,
                     'tags':10,
                     'days_gain':11,
                     'gain_percent':12,
                     'change_percent':13,
                     'type': 14
                      }
        
        #id, object, name, price, change
        self.set_model(gtk.TreeStore(int, object,str, str, str,str, str, int, str, str, str, str, str, str, str))
        
        if type == 1 or type == 2:
            self.create_column(_('Shares'), 7)
        self.create_column(_('Name'), 2)
        self.create_column(_('Type'), self.cols['type'])
        self.create_column(_('Start'), 3)
        if type == 1 or type == 2:
            self.create_column(_('Buy value'), 8)
        self.create_column(_('Last price'), 4)
        self.create_column(_('Change'), 5)
        self.create_column(_('Change %'), 13)
        if type == 1 or type == 2:
            self.create_column(_('Mkt value'), 9)
        
        self.create_column(_('Gain'), 6)
        self.create_column(_('Gain %'), 12)
        self.create_column(_('Day\'s gain'), 11)
        col, cell = self.create_column(_('Tags'), 10)
        cell.set_property('editable', True)
        cell.connect('edited', self.on_tag_edited)
        
        def sort_string_float(model, iter1, iter2, col):
            item1 = float(model.get_value(iter1, col))
            item2 = float(model.get_value(iter2, col))
            if item1 == item2: return 0
            elif item1 < item2: return -1
            else: return 1
        
        def sort_start_price(model, iter1, iter2):
            item1 = model.get_value(iter1, self.cols['obj'])
            item2 = model.get_value(iter2, self.cols['obj'])
            if item1.price == item2.price: return 0
            elif item1.price < item2.price: return -1
            else: return 1
        
        def sort_current_price(model, iter1, iter2):
            item1 = model.get_value(iter1, self.cols['obj'])
            item2 = model.get_value(iter2, self.cols['obj'])
            if item1.current_price == item2.current_price: return 0
            elif item1.current_price < item2.current_price: return -1
            else: return 1
        
        def sort_days_gain(model, iter1, iter2):
            item1 = model.get_value(iter1, self.cols['obj'])
            item2 = model.get_value(iter2, self.cols['obj'])
            if item1.days_gain == item2.days_gain: return 0
            elif item1.days_gain < item2.days_gain: return -1
            else: return 1

        def sort_gain(model, iter1, iter2, i):
            item1 = model.get_value(iter1, self.cols['obj'])
            item2 = model.get_value(iter2, self.cols['obj'])
            if item1.gain[i] == item2.gain[i]: return 0
            elif item1.gain[i] < item2.gain[i]: return -1
            else: return 1
        
        def sort_change(model, iter1, iter2, i):
            item1 = model.get_value(iter1, self.cols['obj'])
            item2 = model.get_value(iter2, self.cols['obj'])
            if item1.current_change[i] == item2.current_change[i]: return 0
            elif item1.current_change[i] < item2.current_change[i]: return -1
            else: return 1
                
        self.get_model().set_sort_func(self.cols['buy_value'], sort_string_float, self.cols['buy_value'])
        self.get_model().set_sort_func(self.cols['mkt_value'], sort_string_float, self.cols['mkt_value'])
        self.get_model().set_sort_func(self.cols['days_gain'], sort_days_gain)
        self.get_model().set_sort_func(self.cols['gain'], sort_gain, 0)
        self.get_model().set_sort_func(self.cols['gain_percent'], sort_gain, 1)
        self.get_model().set_sort_func(self.cols['change'], sort_change, 0)
        self.get_model().set_sort_func(self.cols['change_percent'], sort_change, 1)
        self.get_model().set_sort_func(self.cols['start'], sort_start_price)
        self.get_model().set_sort_func(self.cols['last_price'], sort_current_price)

        self.load_positions()
        
        self.connect('cursor_changed', self.on_cursor_changed)
        self.connect("destroy", self.on_destroy)
        
        self.subscriptions = (
            ('position.updated', self.on_position_updated),
            ('stock.updated', self.on_stock_updated),
            ('positionstoolbar.remove', self.on_remove_position),
            ('positionstoolbar.add', self.on_add_position),
            ('positionstoolbar.tag', self.on_tag),
            ('position.created', self.on_position_created),
            ('position.tags.changed', self.on_positon_tags_changed),
            ('container.position.removed', self.on_position_deleted)
        )
        for topic, callback in self.subscriptions:
            pubsub.subscribe(topic, callback)
            
        self.selected_item = None

    def on_destroy(self, x):
        for topic, callback in self.subscriptions:
            pubsub.unsubscribe(topic, callback)

    def load_positions(self):
        for pos in self.container:
            self.insert_position(pos)
    
    def on_tag_edited(self, cellrenderertext, path, new_text):
        if self.selected_item is None:
            return
        obj, iter = self.selected_item
        obj.tag(new_text.split())
    
    def on_position_updated(self, item):
        row = self.find_position(item.id)
        if row:
            if item.quantity == 0:
                self.get_model().remove(row.iter)
            else:
                row[self.cols['quantity']] = item.quantity
    
    def on_positon_tags_changed(self, tags, item):
        row = self.find_position(item.id)
        if row:
            row[self.cols['tags']] = item.tags_string
    
    def on_stock_updated(self, item):
        row = self.find_position_from_stock(item.id)
        if row:
            row[self.cols['last_price']] = self.get_price_string(item)
            row[self.cols['change']] = get_green_red_string(row[1].current_change[0])
            row[self.cols['change_percent']] = get_green_red_string(row[1].current_change[1])
            row[self.cols['gain']] = get_green_red_string(row[1].gain[0])
            row[self.cols['gain']] = get_green_red_string(row[1].gain[1])
            row[self.cols['days_gain']] = get_green_red_string(row[1].days_gain)
            row[self.cols['mkt_value']] = str(round(row[1].cvalue,2))
                
    def on_position_created(self, item):
        if item.container_id == self.container.id:
            self.insert_position(item)
     
    def on_remove_position(self):
        if self.selected_item is None:
            return
        obj, iter = self.selected_item
        if self.type == 0:
            dlg = gtk.MessageDialog(None, 
                 gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION, 
                    gtk.BUTTONS_OK_CANCEL, _("Are you sure?"))
            response = dlg.run()
            dlg.destroy()
            if response == gtk.RESPONSE_OK:
                self.container.remove_position(obj)
        elif self.type == 1:
            dialogs.SellDialog(self.container, obj)    
    
    def on_position_deleted(self, pos, pf):
        if pf.id == self.container.id:
            row = self.find_position(pos.id)
            if row is not None:
                self.get_model().remove(row.iter)   
       
    def on_add_position(self):
        if self.type == 0:
            dialogs.NewWatchlistPositionDialog(self.container, self.model)  
        elif self.type == 1:
            dialogs.BuyDialog(self.container, self.model)
    
    def on_tag(self):
        if self.selected_item is None:
            return
        path, col = self.get_cursor()
        obj, iter = self.selected_item
        cell = self.get_column(8).get_cell_renderers()[0]
        self.set_cursor(path, focus_column = self.get_column(8), start_editing=True)
        #self.grab_focus()
        
    def on_cursor_changed(self, widget):
        #Get the current selection in the gtk.TreeView
        selection = widget.get_selection()
        # Get the selection iter
        model, selection_iter = selection.get_selected()
        if (selection_iter and model):
            #Something is selected so get the object
            obj = model.get_value(selection_iter, 1)
            self.selected_item = obj, selection_iter
            pubsub.publish('watchlistpositionstree.selection', obj)   
            
    def get_price_string(self, item):
        if item.price is None:
            return 'n/a'
        return str(item.price) +'\n' +'<small>'+get_datetime_string(item.date)+'</small>'
        
    def insert_position(self, position):
        if position.quantity != 0:
            stock = self.model.stocks[position.stock_id]
            gain = position.gain
            c_change = position.current_change
            self.get_model().append(None, [position.id, 
                                           position, 
                                           get_name_string(stock), 
                                           self.get_price_string(position), 
                                           self.get_price_string(stock), 
                                           get_green_red_string(c_change[0]),
                                           get_green_red_string(gain[0]),
                                           position.quantity,
                                           str(round(position.bvalue,2)),
                                           str(round(position.cvalue,2)),
                                           position.tags_string,
                                           get_green_red_string(position.days_gain),
                                           get_green_red_string(gain[1]),
                                           get_green_red_string(c_change[1]),
                                           position.type_string])

    def find_position_from_stock(self, sid):
        def search(rows):
            if not rows: return None
            for row in rows:
                if row[1].stock_id == sid:
                    return row 
                result = search(row.iterchildren())
                if result: return result
            return None
        return search(self.get_model())
        
    def find_position(self, pid):
        def search(rows):
            if not rows: return None
            for row in rows:
                if row[0] == pid:
                    return row 
                result = search(row.iterchildren())
                if result: return result
            return None
        return search(self.get_model())
        
    def __del__(self):
        pass


class TransactionsTree(Tree):
    def __init__(self, portfolio, model):
        self.model = model
        self.portfolio = portfolio
        Tree.__init__(self)
        #id, object, name, price, change
        self.set_model(gtk.TreeStore(int, object,str, str, str,str, str, str))
        
        self.create_column(_('Action'), 2)
        self.create_column(_('Name'), 3)
        self.create_column(_('Date'), 4)
        self.create_column(_('Shares'), 5)
        self.create_column(_('Price'), 6)
        self.create_column(_('Transaction Costs'), 7)
        
        self.load_transactions()
        pubsub.subscribe('position.transaction.added', self.on_transaction_created)
        
        
    def load_transactions(self):
        for pos in self.portfolio:
            for ta in pos:
                self.insert_transaction(ta, pos)
    
    def on_transaction_created(self, item, position):
        if position.container_id == self.portfolio.id:
            self.insert_transaction(item, position)    
    
    def get_action_string(self, type):
        if type == 1:
            return 'BUY'
        elif type == 0:
            return 'SELL'
        else:
            return ''
        
    def insert_transaction(self, ta, pos):
        stock = self.model.stocks[pos.stock_id]
        self.get_model().append(None, [ta.id, ta, self.get_action_string(ta.type), get_name_string(stock), get_datetime_string(ta.date), ta.quantity, ta.price, ta.ta_costs])
