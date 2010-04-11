#!/usr/bin/env python

import gtk
from stocktracker import model, pubsub
from datetime import datetime
from stocktracker import updater


class StockSelector(gtk.Entry):
    def __init__(self, stocks):
        self.stocks = stocks
        gtk.Entry.__init__(self)
        self.completion = completion = gtk.EntryCompletion()
        self.set_completion(completion)
        self.model = liststore = gtk.ListStore(int, str)
        completion.set_model(liststore)
        completion.set_text_column(1)
        i = 0
        for stock in stocks:
            liststore.append([i, str(stock)])       
            i += 1
        #completion.insert_action_text(4,'test')
        #completion.insert_action_markup(4,'test')
    
        completion.set_match_func(self.match_func)
        completion.connect("match-selected", self.on_completion_match)

    def match_func(self, completion, key, iter):
        stock = self.stocks[self.model[iter][0]]
        key = key.lower()
        if stock.name.lower().startswith(key)  \
                or stock.yahoo_symbol.lower().startswith(key) \
                or stock.isin.lower().startswith(key):
            return True
        return False

    def on_completion_match(self, completion, model, iter):
        self.selected_stock = self.stocks[model[iter][0]]
        

class AddStockDialog(gtk.Dialog):
    def __init__(self):
        gtk.Dialog.__init__(self, _("Add a new stock"), None
                    , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                       (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        vbox = self.get_content_area()
        table = gtk.Table()
        vbox.add(table)
        
        table.attach(gtk.Label('Symbol'), 0,1,0,1)
        
        self.symbol_entry = gtk.Entry()
        self.symbol_entry.set_icon_from_stock(1, gtk.STOCK_NO)
        table.attach(self.symbol_entry, 1,2,0,1)
        self.symbol_entry.connect("activate", self.on_symbol_entry)
        self.symbol_entry.connect("focus-out-event", self.on_symbol_entry)
        self.symbol_entry.connect("changed", self.on_symbol_change)

        #type
        table.attach(gtk.Label('Type'), 0,1,1,2)
        self.type_cb = type_cb = gtk.combo_box_new_text()
        type_cb.append_text('stock')
        type_cb.append_text('fund')
        type_cb.set_active(0)
        table.attach(type_cb, 1,2,1,2)
        
        #name
        table.attach(gtk.Label('Name'), 0,1,2,3)
        self.name_entry = gtk.Entry()
        table.attach(self.name_entry, 1,2,2,3)
        
        table.attach(gtk.Label('Exchange'), 0,1,3,4)
        self.exchange_label = gtk.Entry()
        self.exchange_label.set_editable(False)
        table.attach(self.exchange_label, 1,2,3,4)
        
        table.attach(gtk.Label('Currency'), 0,1,4,5)
        self.currency_label = gtk.Entry()
        self.currency_label.set_editable(False)
        table.attach(self.currency_label, 1,2,4,5)

        #table.attach(gtk.Label('Country'), 0,1,5,6)
        #self.country_entry = gtk.Entry()
        #self.country_entry.set_editable(False)
        #table.attach(self.country_entry, 1,2,5,6)

        self.show_all()
        self.process_result(self.run())
        
        self.destroy()

    def on_symbol_change(self, widget):
        self.symbol_entry.set_icon_from_stock(1, gtk.STOCK_DIALOG_QUESTION)
        self.set_response_sensitive(gtk.RESPONSE_ACCEPT, False)  
        
    def on_symbol_entry(self, widget, event = None):
        symbol = self.symbol_entry.get_text()
        stock_info = updater.get_info(symbol)
        if stock_info is not None:
            name, isin, exchange, currency = stock_info
            self.symbol_entry.set_icon_from_stock(1, gtk.STOCK_YES)
            self.set_response_sensitive(gtk.RESPONSE_ACCEPT, True)
            self.name_entry.set_text(name)
            self.exchange_label.set_text(exchange)
            self.currency_label.set_text(currency)
        else:
            self.symbol_entry.set_icon_from_stock(1, gtk.STOCK_NO)
            self.set_response_sensitive(gtk.RESPONSE_ACCEPT, False)
            self.name_entry.set_text('')
            self.exchange_label.set_text('')
            self.currency_label.set_text('')
        
    def process_result(self, response):
        if response == gtk.RESPONSE_ACCEPT:
            name = self.name_entry.get_text()
            symbol = self.symbol_entry.get_text()
            type = self.type_cb.get_active()
            exchange = self.exchange_label.get_text()
            currency = self.currency_label.get_text()
            isin = 'n/a'
            #FIXME
            
            model.Stock(yahoo_symbol = symbol, name = name, type = type, exchange = exchange, currency = currency, isin = isin)


        
class SellDialog(gtk.Dialog):
    def __init__(self, pf, pos):
        gtk.Dialog.__init__(self, _("Sell a position"), None
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
        self.response = self.run()  
        self.process_result()
        
        self.destroy()
        
    def process_result(self):
        if self.response == gtk.RESPONSE_ACCEPT:
            shares = self.shares_entry.get_value()
            if shares == 0.0:
                return
            price = float(self.price_entry.get_text())
            year, month, day = self.calendar.get_date()
            date = datetime(year, month+1, day)
            ta_costs = 0.0

            self.pos.quantity -= shares
            ta = model.Transaction(position=self.pos, type=0, date=date, quantity=shares, price=price, ta_costs=ta_costs)              
            pubsub.publish('position.transaction.added', self.pos, ta)
            self.pf.cash += shares*price - ta_costs


class BuyDialog(gtk.Dialog):
    def __init__(self, pf):
        gtk.Dialog.__init__(self, _("Buy a position"), None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self.pf = pf
        
        vbox = self.get_content_area()
        #stock entry
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        label = gtk.Label(_('Stock:'))
        hbox.pack_start(label)

        self.stock_selector = StockSelector(model.Stock.query.all())
        hbox.pack_start(self.stock_selector)
        self.stock_selector.completion.connect('match-selected', self.on_stock_selection)


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

    def on_stock_selection(self, *args):
        self.set_response_sensitive(gtk.RESPONSE_ACCEPT, True)  
        
    def process_result(self, response):
        if response == gtk.RESPONSE_ACCEPT:
            stock = self.stock_selector.selected_stock
            shares = self.shares_entry.get_value()
            if shares == 0.0:
                return
            price = self.price_entry.get_value()
            year, month, day = self.calendar.get_date()
            date = datetime(year, month+1, day)
            ta_costs = self.tacosts_entry.get_value()
            pos = model.PortfolioPosition(price=price, date=date, quantity=shares, portfolio=self.pf, stock = stock)
            ta = model.Transaction(type=1, date=date,quantity=shares,price=price,ta_costs=ta_costs, position=pos)
            pubsub.publish('container.position.added', self.pf, pos)
            pubsub.publish('position.transaction.added', pos, ta)


class NewWatchlistPositionDialog(gtk.Dialog):
    def __init__(self, wl):
        gtk.Dialog.__init__(self, _("Add watchlist position"), None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self.wl = wl
        
        vbox = self.get_content_area()
        #stock entry
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        label = gtk.Label(_('Stock:'))
        hbox.pack_start(label)

        self.stock_selector = StockSelector(model.Stock.query.all())
        hbox.pack_start(self.stock_selector)
        self.stock_selector.completion.connect('match-selected', self.on_stock_selection)

        self.set_response_sensitive(gtk.RESPONSE_ACCEPT, False)
        self.show_all()
        response = self.run()  
        self.process_result(response)
        self.destroy()

    def on_stock_selection(self, *args):
        self.set_response_sensitive(gtk.RESPONSE_ACCEPT, True)  
        
    def process_result(self, response):
        if response == gtk.RESPONSE_ACCEPT:
            stock = self.stock_selector.selected_stock
            stock.update()
            pos = model.WatchlistPosition(stock=stock, price = stock.price, date=stock.date, watchlist=self.wl)
            pubsub.publish('container.position.added', self.wl, pos)


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
            

class SplitDialog(gtk.Dialog):
    def __init__(self, pos):
        gtk.Dialog.__init__(self, _("Split a position"), None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      _('Split'), gtk.RESPONSE_ACCEPT))
        self.pos = pos
        
        vbox = self.get_content_area()
        
        vbox.pack_start(gtk.Label(str(pos)))

        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        self.val1 = gtk.SpinButton(gtk.Adjustment(lower=1, upper= 1000,step_incr=1, value = 0), digits=0)
        hbox.pack_start(self.val1)
        hbox.pack_start(gtk.Label(' - '))
        self.val2 = gtk.SpinButton(gtk.Adjustment(lower=1, upper=1000,step_incr=1, value = 0), digits=0)
        hbox.pack_start(self.val2)     
        
        #date 
        self.calendar = gtk.Calendar()
        vbox.pack_start(self.calendar)   

        self.show_all()
        response = self.run()  
        self.process_result(response)
        
        self.destroy()
        
    def process_result(self, response):
        if response == gtk.RESPONSE_ACCEPT:
            val1 = self.val1.get_value()
            val2 = self.val2.get_value()
            year, month, day = self.calendar.get_date()
            self.pos.split(val1, val2, datetime(year, month+1, day))
 
            
class MergeDialog(gtk.Dialog):
    def __init__(self):
        gtk.Dialog.__init__(self, _("Merge two positions"), None
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
            #FIXME
            self.selected_pf = session['model'].portfolios[model[index][0]]
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
        


