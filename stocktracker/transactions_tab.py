#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/stocktracker
#    objects.py: Copyright 2009 Wolfgang Steitz <wsteitz(at)gmail.com>
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


from stocktracker.treeviews import Tree, get_name_string, datetime_format, get_datetime_string
import gtk
from stocktracker.session import session
from stocktracker import pubsub, config, objects



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
        pubsub.subscribe('portfolio.transaction.added', self.on_pf_transaction_created)
        
    def load_transactions(self):
        for pos in self.portfolio:
            for ta in pos:
                self.insert_transaction(ta, pos)
        if self.portfolio.type == 'portfolio':
            for id, ta in self.portfolio.transactions.iteritems():
                self.insert_pf_transaction(ta)
    
    def on_pf_transaction_created(self, ta, portfolio):
        if portfolio.id == self.portfolio.id:
            self.insert_pf_transaction(ta)
    
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
        elif type == 3:
            return 'DEPOSIT'
        elif type == 4:
            return 'WITHDRAW'
        else:
            return ''
        
    def insert_transaction(self, ta, pos):
        stock = session['model'].stocks[pos.stock_id]
        self.get_model().append(None, [ta.id, ta, self.get_action_string(ta.type), get_name_string(stock), get_datetime_string(ta.date), ta.quantity, ta.price, ta.ta_costs])

    def insert_pf_transaction(self, ta):
        self.get_model().append(None, [ta.id, ta, self.get_action_string(ta.type), '', get_datetime_string(ta.date), ta.quantity, ta.price, ta.ta_costs]) 

