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
from stocktracker import objects, dialogs, config, pubsub

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
