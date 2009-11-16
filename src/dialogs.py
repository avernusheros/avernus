#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/stocktracker
#    dialogs.py: Copyright 2009 Wolfgang Steitz <wsteitz(at)gmail.com>
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


import gtk
import objects, updater
from datetime import datetime


class EditWatchlist(gtk.Dialog):
    def __init__(self, wl, parent = None):
        gtk.Dialog.__init__(self, _("Edit..."), parent
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        
        self.wl = wl
        vbox = self.get_content_area()
        
        #name entry
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        label = gtk.Label(_('Name:'))
        hbox.pack_start(label)
        self.name_entry = gtk.Entry()
        hbox.pack_start(self.name_entry)

        self.show_all()
        response = self.run()  
        self.process_result(response)
        
        self.destroy()

    def process_result(self, response):
        if response == gtk.RESPONSE_ACCEPT:
            self.wl.name = self.name_entry.get_text()    

class EditPortfolio(EditWatchlist):
    def __init__(self, pf, parent = None):
        EditWatchlist.__init__(self, pf, parent)

class NewContainerDialog(gtk.Dialog):
    def __init__(self, model, parent = None):
        gtk.Dialog.__init__(self, _("Create..."), parent
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        
        self.model = model
        vbox = self.get_content_area()
        
        
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        self.radiobutton = button = gtk.RadioButton(None, _("Portfolio"))
        hbox.pack_start(button, True, True, 0)
        
        button = gtk.RadioButton(button, _("Watchlist"))
        hbox.pack_start(button, True, True, 0)
               
        #name entry
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        label = gtk.Label(_('Name:'))
        hbox.pack_start(label)
        self.name_entry = gtk.Entry()
        hbox.pack_start(self.name_entry)

        self.show_all()
        response = self.run()  
        self.process_result(response)
        
        self.destroy()

    def process_result(self, response):
        if response == gtk.RESPONSE_ACCEPT:
            #grab the name
            name = self.name_entry.get_text()
            if self.radiobutton.get_active():
                self.model.create_portfolio(name)
            else:
                #create wathclist
                self.model.create_watchlist(name)


class SellDialog(gtk.Dialog):
    def __init__(self, pf, pos, parent = None):
        gtk.Dialog.__init__(self, _("Sell a position"), parent
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self.pf = pf              
        self.pos = pos
        
        vbox = self.get_content_area()

        #shares entry
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        hbox.pack_start(gtk.Label(_('Shares:')))
        self.shares_entry = gtk.SpinButton(gtk.Adjustment(lower=0, upper=pos.quantity,step_incr=1, value = 0), digits=2)
        hbox.pack_start(self.shares_entry)
        
        #price entry
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        hbox.pack_start(gtk.Label(_('Price:')))
        self.price_entry = gtk.SpinButton(gtk.Adjustment(lower=0, upper=100000,step_incr=0.1, value = 1.0), digits=2)
        hbox.pack_start(self.price_entry)
        
        #date 
        self.calendar = gtk.Calendar()
        vbox.pack_start(self.calendar)
        
        self.show_all()
        response = self.run()  
        self.process_result(response)
        
        self.destroy()
        
    def process_result(self, response):
        if response == gtk.RESPONSE_ACCEPT:
            shares = self.shares_entry.get_value()
            if shares == 0.0:
                return
            price = self.price_entry.get_text()
            year, month, day = self.calendar.get_date()
            date = datetime(year, month, day)
            ta_costs = 0.0

            self.pos.quantity -= shares    
            
            self.pos.add_transaction(0, date, shares, price, ta_costs)


class BuyDialog(gtk.Dialog):
    def __init__(self, pf, model, parent = None):
        gtk.Dialog.__init__(self, _("Buy a position"), parent
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self.pf = pf
        self.model = model
        
        vbox = self.get_content_area()
        #symbol entry
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        label = gtk.Label(_('Symbol:'))
        label.set_tooltip_text('Symbol as used on yahoo finance') 
        hbox.pack_start(label)


        self.symbol_entry = gtk.Entry()
        self.symbol_entry.set_icon_from_stock(1, gtk.STOCK_NO)
        hbox.pack_start(self.symbol_entry)
        self.symbol_entry.connect("activate", self.on_symbol_entry)
        self.symbol_entry.connect("focus-out-event", self.on_symbol_entry)
        self.symbol_entry.connect("changed", self.on_symbol_change)

        #type
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        self.radiobutton = button = gtk.RadioButton(None, _("Stock"))
        hbox.pack_start(button, True, True, 0)
        
        button = gtk.RadioButton(button, _("Fond"))
        hbox.pack_start(button, True, True, 0)

        #shares entry
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        hbox.pack_start(gtk.Label(_('Shares:')))
        self.shares_entry = gtk.SpinButton(gtk.Adjustment(lower=0, upper=100000,step_incr=1.0, value = 0), digits=2)
        self.shares_entry.connect("changed", self.on_change)
        hbox.pack_start(self.shares_entry)
        
        #price entry
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        hbox.pack_start(gtk.Label(_('Price:')))
        self.price_entry = gtk.SpinButton(gtk.Adjustment(lower=0, upper=100000,step_incr=0.1, value = 1.0), digits=2)
        self.price_entry.connect("changed", self.on_change)
        hbox.pack_start(self.price_entry)
        
        
        #ta_costs entry
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        hbox.pack_start(gtk.Label(_('Transaction Costs:')))
        self.tacosts_entry = gtk.SpinButton(gtk.Adjustment(lower=0, upper=100000,step_incr=0.1, value = 0.0), digits=2)
        self.tacosts_entry.connect("changed", self.on_change)
        hbox.pack_start(self.tacosts_entry)
        
        #total
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        hbox.pack_start(gtk.Label(_('Total:')))
        self.total = gtk.Label('0.0')
        hbox.pack_start(self.total)
        
        #date 
        self.calendar = gtk.Calendar()
        vbox.pack_start(self.calendar)
        
        self.set_response_sensitive(gtk.RESPONSE_ACCEPT, False)
        self.show_all()
        response = self.run()  
        self.process_result(response)
        
        self.destroy()

    def on_change(self, widget):
        total = self.shares_entry.get_value() * self.price_entry.get_value() + self.tacosts_entry.get_value()
        self.total.set_text(str(total))

    def on_symbol_change(self, widget):
        self.symbol_entry.set_icon_from_stock(1, gtk.STOCK_DIALOG_QUESTION)
        self.set_response_sensitive(gtk.RESPONSE_ACCEPT, False)  
        
    def on_symbol_entry(self, widget, event = None):
        symbol = self.symbol_entry.get_text()
        if updater.check_symbol(symbol):
            self.symbol_entry.set_icon_from_stock(1, gtk.STOCK_YES)
            self.set_response_sensitive(gtk.RESPONSE_ACCEPT, True)
        else:
            self.symbol_entry.set_icon_from_stock(1, gtk.STOCK_NO)
            self.set_response_sensitive(gtk.RESPONSE_ACCEPT, False)
        
    def process_result(self, response):
        if response == gtk.RESPONSE_ACCEPT:
            symbol = self.symbol_entry.get_text()
            shares = self.shares_entry.get_value()
            if shares == 0.0:
                return
            if self.radiobutton.get_active():
                type = 0
            else:
                type = 1
            price = self.price_entry.get_value()
            stock = self.model.get_stock(symbol, type, update = True)
            year, month, day = self.calendar.get_date()
            date = datetime(year, month, day)
            ta_costs = self.tacosts_entry.get_value()
            position = self.pf.add_position(symbol, price, date, shares)
            position.add_transaction(1, date, shares, price, ta_costs)


class NewWatchlistPositionDialog(gtk.Dialog):
    def __init__(self, wl, model, parent = None):
        gtk.Dialog.__init__(self, _("Create..."), parent
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        
        self.wl = wl
        self.model = model
        vbox = self.get_content_area()
        
        #symbol entry
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        hbox.pack_start(gtk.Label(_('Symbol:')))
        self.symbol_entry = gtk.Entry()
        self.symbol_entry.set_icon_from_stock(1, gtk.STOCK_NO)
        hbox.pack_start(self.symbol_entry)
        self.symbol_entry.connect("activate", self.on_entry)
        self.symbol_entry.connect("focus-out-event", self.on_entry)
        self.symbol_entry.connect("changed", self.on_change)
        self.set_response_sensitive(gtk.RESPONSE_ACCEPT, False)
        
        #type
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        self.radiobutton = button = gtk.RadioButton(None, _("Stock"))
        hbox.pack_start(button, True, True, 0)
        
        button = gtk.RadioButton(button, _("Fond"))
        hbox.pack_start(button, True, True, 0)

        
        self.show_all()
        response = self.run()  
        self.process_result(response)
        
        self.destroy()
    
    def on_change(self, widget):
        self.symbol_entry.set_icon_from_stock(1, gtk.STOCK_DIALOG_QUESTION)
        self.set_response_sensitive(gtk.RESPONSE_ACCEPT, False)
   
    def on_entry(self, widget, event = None):
        symbol = self.symbol_entry.get_text()
        if updater.check_symbol(symbol):
            self.symbol_entry.set_icon_from_stock(1, gtk.STOCK_YES)
            self.set_response_sensitive(gtk.RESPONSE_ACCEPT, True)
        else:
            self.symbol_entry.set_icon_from_stock(1, gtk.STOCK_NO)
            self.set_response_sensitive(gtk.RESPONSE_ACCEPT, False)

    def process_result(self, response):
        if response == gtk.RESPONSE_ACCEPT:
            symbol = self.symbol_entry.get_text()
            if self.radiobutton.get_active():
                type = 0
            else:
                type = 1
            stock = self.model.get_stock(symbol, type, update = True)
            position = self.wl.add_position(symbol,stock.price, stock.date, 1)            



class PfSelector(gtk.ComboBox):
    def __init__(self, model):
        liststore = gtk.ListStore(int, str)
        liststore.append([-1, 'Select a portfolio'])
        for id, pf in model.portfolios.items():
            liststore.append([id, pf.name])
        gtk.ComboBox.__init__(self, liststore)
        cell = gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, 'text', 1)  
        self.set_active(0)

class PosSelector(gtk.ComboBox):
    def __init__(self):
        gtk.ComboBox.__init__(self)
        cell = gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, 'text', 1)  
        self.set_active(0)
        self.set_button_sensitivity(gtk.SENSITIVITY_AUTO)
        
    def on_pf_selection(self, pf):
        if pf is None:
            self.set_model()
            return
        liststore = gtk.ListStore(int, str)
        liststore.append([-1, 'Select a position'])
        for pos in pf:
            liststore.append([pos.id, str(pos.quantity) +' ' +pos.name])
        self.set_model(liststore)
            
        
            
class MergeDialog(gtk.Dialog):
    def __init__(self,  model, parent = None):
        self.model = model
        
        gtk.Dialog.__init__(self, _("Merge two positions"), parent
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      'Merge', gtk.RESPONSE_ACCEPT))
        vbox = self.get_content_area()
        table = gtk.Table(rows = 4, columns = 2)
        vbox.pack_start(table)
        
        table.attach(gtk.Label(_('Portfolio')),0,1,0,1)
        self.pf = PfSelector(model)
        table.attach(self.pf,1,2,0,1)
        self.pf.connect('changed', self.changed_pf)
        
        table.attach(gtk.Label(_('First Position')),0,1,1,2)
        self.pos1 = PosSelector()
        self.pos1.connect('changed', self.changed_pos, 0)
        table.attach(self.pos1,1,2,1,2)
        
        table.attach(gtk.Label(_('Second Position')),0,1,2,3)
        self.pos2 = PosSelector()
        self.pos2.connect('changed', self.changed_pos, 1)
        table.attach(self.pos2,1,2,2,3)
        
        table.attach(gtk.Label(_('Only positions with identical stocks can be merged. This action can not be undone!')),0,2,3,4)
        
        self.selected_pf = None
        self.selected_pos = [None,None]
        
        self.set_response_sensitive(gtk.RESPONSE_ACCEPT, False)
        self.show_all()
        response = self.run()  
        self.process_result(response)
        
        self.destroy()
    
    def changed_pf(self, combobox):
        model = combobox.get_model()
        index = combobox.get_active()
        if index:
            self.selected_pf = self.model.portfolios[model[index][0]]
        else:
            self.selected_pf = None
        self.pos1.on_pf_selection(self.selected_pf)
        self.pos2.on_pf_selection(self.selected_pf)
    
    def changed_pos(self, combobox, pos_num):
        model = combobox.get_model()
        index = combobox.get_active()
        if index:
            self.selected_pos[pos_num] = self.selected_pf.positions[model[index][0]]
        else:
            self.selected_pos[pos_num] = None
            
        if self.selected_pos[1] is not None \
                and self.selected_pos[0].stock_id == self.selected_pos[1].stock_id \
                and self.selected_pos[0].id != self.selected_pos[1].id:
            self.set_response_sensitive(gtk.RESPONSE_ACCEPT, True)
        else:   
            self.set_response_sensitive(gtk.RESPONSE_ACCEPT, False)
        
    def process_result(self, response):
        if response == gtk.RESPONSE_ACCEPT:
            self.selected_pf.merge_positions(self.selected_pos[0], self.selected_pos[1])
        
if __name__ == "__main__":
    import objects, persistent_store
    store = persistent_store.Store('test.db')
    model = objects.Model(store)
    d = MergeDialog(model)
    gtk.main() 
