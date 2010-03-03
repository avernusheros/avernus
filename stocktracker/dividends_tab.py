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
from stocktracker.dialogs import PosSelector
from datetime import datetime


class DividendsTab(gtk.VBox):
    def __init__(self, item):
        gtk.VBox.__init__(self)
        dividends_tree = DividendsTree(item)
        #self.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        #self.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        self.pack_start(DividendsToolbar(item), expand = False, fill = False)
        self.pack_start(dividends_tree)
        self.show_all()


class DividendsToolbar(gtk.Toolbar):
    def __init__(self, container):
        gtk.Toolbar.__init__(self)
        self.container = container
        self.conditioned = []
        
        button = gtk.ToolButton('gtk-add')
        button.connect('clicked', self.on_add_clicked)
        button.set_tooltip_text('Add dividend') 
        self.insert(button,-1)
        
        button = gtk.ToolButton('gtk-delete')
        #button.set_label('Remove tag'
        button.connect('clicked', self.on_remove_clicked)
        button.set_tooltip_text('Remove selected dividend') 
        self.conditioned.append(button)
        self.insert(button,-1)
        
        self.on_unselect()
        pubsub.subscribe('dividendstree.unselect', self.on_unselect)
        pubsub.subscribe('dividendstree.select', self.on_select)
        
    def on_unselect(self):
        for button in self.conditioned:
            button.set_sensitive(False)       
        
    def on_select(self, obj):
        for button in self.conditioned:
            button.set_sensitive(True)

    def on_add_clicked(self, *args):
        AddDividendDialog(self.container)
    
    def on_remove_clicked(self, *args):
        pubsub.publish("dividendstoolbar.remove")
       

class DividendsTree(Tree):
    def __init__(self, portfolio):
        self.portfolio = portfolio
        self.selected_item = None
        Tree.__init__(self)
        self.set_model(gtk.TreeStore(int, object,str, str, str,float))
        
        self.create_column(_('Name'), 2)
        self.create_column(_('Date'), 3)
        self.create_column(_('Value'), 4)
        self.create_column(_('Percentage'), 5)
        
        self.load_dividends()
        pubsub.subscribe('position.dividend.added', self.on_dividend_added)
        pubsub.subscribe('dividendstoolbar.remove', self.on_remove)
        self.connect('cursor_changed', self.on_cursor_changed)
        
    def on_cursor_changed(self, widget):
        #Get the current selection in the gtk.TreeView
        selection = widget.get_selection()
        # Get the selection iter
        model, selection_iter = selection.get_selected()
        if (selection_iter and model):
            #Something is selected so get the object
            obj = model.get_value(selection_iter, 1)
            self.selected_item = obj, selection_iter
            if isinstance(obj, objects.Dividend):
                pubsub.publish('dividendstree.select', obj)
                return
        pubsub.publish('dividendstree.unselect')
        
    def load_dividends(self):
        for pos in self.portfolio:
            for id, div in pos.dividends.items():
                self.insert_dividend(div, pos)
    
    def on_dividend_added(self, item, position):
        if position.container_id == self.portfolio.id:
            self.insert_dividend(item, position)    
    
    def insert_dividend(self, div, pos):
        stock = session['model'].stocks[pos.stock_id]
        self.get_model().append(None, [div.id, div, get_name_string(stock), get_datetime_string(div.date), div.value, 0.0])

    def on_remove(self):
        if self.selected_item is None:
            return
        obj, iter = self.selected_item
        if isinstance(obj, objects.Dividend):
            dlg = gtk.MessageDialog(None, 
                 gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION, 
                 gtk.BUTTONS_OK_CANCEL, 
                 _("Permanently delete dividend?"))
            response = dlg.run()
            dlg.destroy()
            if response == gtk.RESPONSE_OK:
                self.portfolio.positions[obj.pos_id].remove_dividend(obj)
                self.get_model().remove(iter) 



class AddDividendDialog(gtk.Dialog):
    def __init__(self, pf):
        gtk.Dialog.__init__(self, _("Add dividend"), session['main']
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      'Add', gtk.RESPONSE_ACCEPT))
        self.pf = pf
        vbox = self.get_content_area()
        table = gtk.Table()
        vbox.pack_start(table)
        
        table.attach(gtk.Label(_('Position: ')),0,1,0,1)
        self.pos_selector = PosSelector()
        self.pos_selector.on_pf_selection(pf)
        self.pos_selector.connect('changed', self.changed_pos)
        table.attach(self.pos_selector,1,2,0,1)
                
        self.selected_pos = None
        
        table.attach(gtk.Label(_('Value: ')),0,1,1,2)
        self.value_entry = gtk.SpinButton(gtk.Adjustment(lower=0, upper=100000,step_incr=0.1, value = 1.0), digits=2)
        table.attach(self.value_entry, 1,2,1,2)
        
        self.calendar = gtk.Calendar()
        table.attach(self.calendar, 0,2,2,3)
        
        
        self.set_response_sensitive(gtk.RESPONSE_ACCEPT, False)
        self.show_all()
        response = self.run()  
        self.process_result(response)
        
        self.destroy()
    
    def changed_pos(self, combobox):
        model = combobox.get_model()
        index = combobox.get_active()
        if index:
            self.selected_pos = self.pf.positions[model[index][0]]
        else:
            self.selected_pos = None
            
        if self.selected_pos is not None:
            self.set_response_sensitive(gtk.RESPONSE_ACCEPT, True)
        else:   
            self.set_response_sensitive(gtk.RESPONSE_ACCEPT, False)
        
    def process_result(self, response):
        if response == gtk.RESPONSE_ACCEPT:
            year, month, day = self.calendar.get_date()
            date = datetime(year, month+1, day)
            value = self.value_entry.get_text()
            self.selected_pos.add_dividend(value, date)
