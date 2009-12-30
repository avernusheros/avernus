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
from stocktracker import objects, config, pubsub
from stocktracker.session import session

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
 

def get_green_red_string(num, string = None):
    if string is None:
        string = str(num)
    if num < 0.0:
        text = '<span foreground="red">'+ string + '</span>'
    else:
        text = '<span foreground="dark green">'+ string + '</span>'
    return text


class Tree(gtk.TreeView):
    def __init__(self):
        self.selected_item = None
        gtk.TreeView.__init__(self)
        pubsub.subscribe('clear!', self.clear)
    
    def create_column(self, name, attribute):
        column = gtk.TreeViewColumn(name)
        self.append_column(column)
        cell = gtk.CellRendererText()
        column.pack_start(cell, expand = True)
        column.add_attribute(cell, "markup", attribute)
        column.set_sort_column_id(attribute)
        return column, cell

    
    def find_item(self, id, type = None):
        print "find item", id
        def search(rows):
            if not rows: return None
            for row in rows:
                if row[0] == id and (type is None or type == row[1].type):
                    return row 
                result = search(row.iterchildren())
                if result: return result
            return None
        return search(self.get_model())

    def clear(self):
        print self
        self.get_model().clear()
    

class TransactionsTree(Tree):
    def __init__(self, portfolio):
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
        elif type == 2:
            return 'SPLIT'
        else:
            return ''
        
    def insert_transaction(self, ta, pos):
        stock = session['model'].stocks[pos.stock_id]
        self.get_model().append(None, [ta.id, ta, self.get_action_string(ta.type), get_name_string(stock), get_datetime_string(ta.date), ta.quantity, ta.price, ta.ta_costs])
