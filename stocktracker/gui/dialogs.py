#!/usr/bin/env python

import gtk
from stocktracker import pubsub, config, logger
from datetime import datetime
from stocktracker.objects import controller
from stocktracker.objects.exchange import Exchange
from stocktracker.gui import gui_utils

class EditPositionDialog(gtk.Dialog):
    def __init__(self, position):
        gtk.Dialog.__init__(self, _("Edit position"), None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        vbox = self.get_content_area()
        notebook = gtk.Notebook()
        vbox.pack_start(notebook)
        self.position_table = EditPositionTable(position)
        self.stock_table = EditStockTable(position.stock)
        notebook.append_page(self.position_table, gtk.Label(_('Position')))
        notebook.append_page(self.stock_table, gtk.Label(_('Stock')))
        
        self.show_all()
        response = self.run()  
        self.process_result(response = response)

    def process_result(self, widget=None, response = gtk.RESPONSE_ACCEPT):
        if response == gtk.RESPONSE_ACCEPT:
            self.position_table.process_result(response)
            self.stock_table.process_result(response)
        self.destroy()              
              

class EditStockDialog(gtk.Dialog):
    def __init__(self, stock):
        gtk.Dialog.__init__(self, _("Edit stock"), None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        
        vbox = self.get_content_area()
        self.table = EditStockTable(stock)
        vbox.pack_start(self.table)
        
        self.show_all()
        response = self.run()  
        self.process_result(response = response)

    def process_result(self, widget=None, response = gtk.RESPONSE_ACCEPT):
        if response == gtk.RESPONSE_ACCEPT:
            self.table.process_result(response)
        self.destroy()


class EditStockTable(gtk.Table):
    def __init__(self, stock):
        gtk.Table.__init__(self)
        
        self.stock = stock
        
        self.attach(gtk.Label(_('Name')),0,1,0,1)
        self.name_entry = gtk.Entry()
        self.name_entry.set_text(stock.name)
        self.attach(self.name_entry,1,2,0,1)

        self.attach(gtk.Label(_('ISIN')),0,1,1,2)
        self.isin_entry = gtk.Entry()
        self.isin_entry.set_text(stock.isin)
        self.attach(self.isin_entry,1,2,1,2)
        
        self.attach(gtk.Label(_('Type')),0,1,2,3)
        self.types = {'fund':0, 'stock':1}
        self.type_cb = gtk.combo_box_new_text()
        for key, val in self.types.items():
            self.type_cb.append_text(key)
        self.type_cb.set_active(self.stock.type)
        self.attach(self.type_cb, 1,2,2,3)

        self.attach(gtk.Label(_('yahoo symbol')),0,1,3,4)
        self.yahoo_entry = gtk.Entry()
        self.yahoo_entry.set_text(stock.yahoo_symbol)
        self.attach(self.yahoo_entry,1,2,3,4)

        self.attach(gtk.Label(_('Sector')),0,1,4,5)
        self.sector_cb = gtk.combo_box_new_text()
        self.sectors = {}
        current = 0
        count = 1
        self.sector_cb.append_text('None')
        for s in controller.getAllSector():
            self.sector_cb.append_text(s.name)
            self.sectors[count] = s
            if self.stock.sector == s:
                current = count
            count+=1
        self.sector_cb.set_active(current)
        self.attach(self.sector_cb, 1,2,4,5)

    def process_result(self, widget=None, response = gtk.RESPONSE_ACCEPT):
        if response == gtk.RESPONSE_ACCEPT:
            self.stock.name = self.name_entry.get_text()
            self.stock.isin = self.isin_entry.get_text()
            self.stock.type = self.types[self.type_cb.get_active_text()]
            self.stock.yahoo_symbol = self.yahoo_entry.get_text()
            if self.sector_cb.get_active() != 0:   
                self.stock.sector = self.sectors[self.sector_cb.get_active()]
            else:
                self.stock.sector = None
            pubsub.publish("stock.edited", self.stock) 


class EditPositionTable(gtk.Table):
    #FIXME tags
    def __init__(self, pos):
        gtk.Table.__init__(self)
        self.pos = pos

        self.attach(gtk.Label(_('Shares')),0,1,0,1)
        self.shares_entry = gtk.SpinButton(gtk.Adjustment(lower=0, upper=100000,step_incr=1.0, value = 0), digits=2)
        self.shares_entry.set_value(self.pos.quantity)
        self.attach(self.shares_entry,1,2,0,1)
        
        self.attach(gtk.Label(_('Buy price')),0,1,1,2)
        self.price_entry = gtk.SpinButton(gtk.Adjustment(lower=0, upper=100000,step_incr=0.1, value = 1.0), digits=2)
        self.price_entry.set_value(self.pos.price)
        self.attach(self.price_entry,1,2,1,2)  

        self.attach(gtk.Label(_('Buy date')),0,1,2,3)
        self.calendar = gtk.Calendar()
        self.calendar.select_month(self.pos.date.month-1, self.pos.date.year)
        self.calendar.select_day(self.pos.date.day)
        self.attach(self.calendar,1,2,2,3)

        self.attach(gtk.Label(_('Comment')),0,1,3,4)
        self.comment_entry = gtk.TextView()
        buffer = self.comment_entry.get_buffer()
        buffer.set_text(self.pos.comment)
        self.attach(self.comment_entry, 1,2,3,4)

    def process_result(self, widget=None, response = gtk.RESPONSE_ACCEPT):
        if response == gtk.RESPONSE_ACCEPT:
            ta = controller.getBuyTransaction(self.pos)
            
            ta.quantity = self.pos.quantity = self.shares_entry.get_value() 
            ta.price = self.pos.price = self.price_entry.get_value()
            year, month, day = self.calendar.get_date()
            ta.date = self.pos.date = datetime(year, month+1, day)
            buffer = self.comment_entry.get_buffer()
            self.pos.comment = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter())            


class StockSelector(gtk.Table):
    def __init__(self):
        gtk.Table.__init__(self)
        
        self.search_field = gtk.Entry()
        self.search_field.connect('activate', self.on_search)
        self.search_field.set_icon_from_stock(1, gtk.STOCK_FIND)
        self.attach(self.search_field,0,1,0,1,xoptions=gtk.FILL, yoptions=gtk.FILL)
        
        button = gtk.Button(label='search', stock='gtk-find')
        self.attach(button,1,2,0,1,xoptions=gtk.FILL, yoptions=gtk.FILL)
        button.connect('clicked', self.on_search)
        
        sw = gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', gtk.POLICY_NEVER)
        sw.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        self.result_tree = gui_utils.Tree()
        self.result_tree.set_model(gtk.TreeStore(object,str, str, str,str,str))
        self.result_tree.create_icon_column(None, 1)
        self.result_tree.create_column(_('Name'), 2)
        self.result_tree.create_column('ISIN', 3)
        self.result_tree.create_column(_('Exchange'), 4)
        self.result_tree.create_icon_column(_('Type'), 5)
        sw.add(self.result_tree)
        self.attach(sw, 0,2,1,2)

    def get_stock(self):
        path, col = self.result_tree.get_cursor()
        return self.result_tree.get_model()[path][0]

    def on_search(self, *args):
        self.result_tree.clear()
        searchstring = self.search_field.get_text()
        controller.datasource_manager.search(searchstring, self.insert_item)
        for item in controller.getStockForSearchstring(searchstring):
            self.insert_item(item)    
        
    def insert_item(self, stock, icon='gtk-harddisk'):
        icons = ['F', 'A']
        self.result_tree.get_model().append(None, [
                                       stock, 
                                       icon,
                                       stock.name,
                                       stock.isin,
                                       stock.exchange.name,
                                       icons[stock.type]
                                       ])


class StockSelectorOld(gtk.Entry):
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
        type_cb.append_text('fund')
        type_cb.append_text('stock')
        type_cb.set_active(1)
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

        table.attach(gtk.Label(_('Sector')),0,1,5,6)
        self.sector_cb = gtk.combo_box_new_text()
        self.sectors = {}
        count = 1
        self.sector_cb.append_text('None')
        self.sectors[0] = None
        for s in controller.getAllSector():
            self.sector_cb.append_text(s.name)
            self.sectors[count] = s
            count+=1
        self.sector_cb.set_active(0)
        table.attach(self.sector_cb, 1,2,5,6)

        self.show_all()
        self.process_result(self.run())
        
        self.destroy()

    def on_symbol_change(self, widget):
        self.symbol_entry.set_icon_from_stock(1, gtk.STOCK_DIALOG_QUESTION)
        self.set_response_sensitive(gtk.RESPONSE_ACCEPT, False)  
        
    def on_symbol_entry(self, widget, event = None):
        symbol = self.symbol_entry.get_text()
        stock_info = controller.datasource_manager.get_info(symbol)
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
        #FIXME should check existing stocks first
        if response == gtk.RESPONSE_ACCEPT:
            name = self.name_entry.get_text()
            symbol = self.symbol_entry.get_text()
            type = self.type_cb.get_active()
            exchange_name = self.exchange_label.get_text()
            currency = self.currency_label.get_text()
            sector = self.sectors[self.sector_cb.get_active()]
            #FIXME get isin from yahoo????
            isin = ''
            ex = controller.detectDuplicate(Exchange, name=exchange_name)
            controller.newStock(yahoo_symbol = symbol, name = name, type = type, exchange = ex, currency = currency, isin = isin, sector=sector)


        
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
            ta = controller.newTransaction(portfolio=self.pf, position=self.pos, type=0, date=date, quantity=shares, price=price, costs=ta_costs)              
            pubsub.publish('transaction.added', ta)
            self.pf.cash += shares*price - ta_costs
            
class PrefDialog(gtk.Dialog):
    
    def __init__(self):
        gtk.Dialog.__init__(self, "Preferences", None,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                             gtk.STOCK_OK, gtk.RESPONSE_ACCEPT),
                            )
        logger.logger.debug("PrefDialog started")
        self.conf = config.StocktrackerConfig()
        self.newName = None
        vbox = self.get_content_area()
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        label = gtk.Label("Database Location: ")
        hbox.pack_start(label)
        dialogButton = gtk.ToolButton(gtk.STOCK_OPEN)
        hbox.pack_start(dialogButton)
        dialogButton.connect('clicked',self.launchDiag)
        self.currLabel = gtk.Label(self.conf.get_option('database file'))
        vbox.pack_start(self.currLabel)
        self.show_all()
        response = self.run()  
        self.process_result(response)
        self.destroy()
        logger.logger.debug("PrefDialog destroyed")
        
    def launchDiag(self, widget):
        dialog = gtk.FileChooserDialog("Select a Database Location",
                               None,
                               gtk.FILE_CHOOSER_ACTION_SAVE,
                               (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            self.newName = dialog.get_filename()
            self.currLabel.set_text(self.newName)
        dialog.destroy()

    def process_result(self, response):
        #print "Processing the response"
        if response == gtk.RESPONSE_ACCEPT:
            if self.newName:
                self.conf.set_option('database file', self.newName)
                self.conf.write()
                logging.logger.info("Wrote new database file: " + self.newName)


class BuyDialog(gtk.Dialog):
    #FIXME user should not be able to select a date in the future
    def __init__(self, pf):
        gtk.Dialog.__init__(self, _("Buy a position"), None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self.pf = pf
        
        vbox = self.get_content_area()
        table = gtk.Table()
        vbox.pack_start(table)
        #stock entry
        self.stock_selector = StockSelector()
        table.attach(self.stock_selector,0,2,0,1)
        self.stock_selector.result_tree.connect('cursor-changed', self.on_stock_selection)
        self.stock_selector.result_tree.get_model().connect('row-deleted', self.on_stock_deselection)

        #shares entry
        table.attach(gtk.Label(_('Shares')),0,1,1,2)
        self.shares_entry = gtk.SpinButton(gtk.Adjustment(lower=0, upper=100000,step_incr=1.0, value = 0), digits=2)
        self.shares_entry.connect("value-changed", self.on_change)
        table.attach(self.shares_entry,1,2,1,2)
        
        #price entry
        table.attach(gtk.Label(_('Price')),0,1,2,3)
        self.price_entry = gtk.SpinButton(gtk.Adjustment(lower=0, upper=100000,step_incr=0.1, value = 1.0), digits=2)
        self.price_entry.connect("value-changed", self.on_change)
        table.attach(self.price_entry,1,2,2,3)
        
        #ta_costs entry
        table.attach(gtk.Label(_('Transaction Costs')),0,1,3,4)
        self.tacosts_entry = gtk.SpinButton(gtk.Adjustment(lower=0, upper=100000,step_incr=0.1, value = 0.0), digits=2)
        self.tacosts_entry.connect("value-changed", self.on_change)
        table.attach(self.tacosts_entry,1,2,3,4)
        
        #total
        table.attach(gtk.Label(_('Total')),0,1,4,5)
        self.total = gtk.Label('0.0')
        table.attach(self.total,1,2,4,5)
        
        #date 
        self.calendar = gtk.Calendar()
        table.attach(self.calendar,0,2,5,6)
        
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
    
    def on_stock_deselection(self, *args):
        self.set_response_sensitive(gtk.RESPONSE_ACCEPT, False)   
        
    def process_result(self, response):
        if response == gtk.RESPONSE_ACCEPT:
            stock = self.stock_selector.get_stock()
            shares = self.shares_entry.get_value()
            if shares == 0.0:
                return
            price = self.price_entry.get_value()
            year, month, day = self.calendar.get_date()
            date = datetime(year, month+1, day)
            ta_costs = self.tacosts_entry.get_value()
            pos = controller.newPortfolioPosition(price=price, date=date, quantity=shares, portfolio=self.pf, stock = stock)
            ta = controller.newTransaction(type=1, date=date,quantity=shares,price=price,costs=ta_costs, position=pos, portfolio=self.pf)
            pubsub.publish('container.position.added', self.pf, pos)
            pubsub.publish('transaction.added', ta)


class NewWatchlistPositionDialog(gtk.Dialog):
    def __init__(self, wl):
        gtk.Dialog.__init__(self, _("Add watchlist position"), None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self.wl = wl
        
        vbox = self.get_content_area()
        self.stock_selector = StockSelector()
        vbox.pack_start(self.stock_selector)
        self.stock_selector.result_tree.connect('cursor-changed', self.on_stock_selection)
        self.stock_selector.result_tree.get_model().connect('row-deleted', self.on_stock_deselection)

        self.set_response_sensitive(gtk.RESPONSE_ACCEPT, False)
        self.show_all()
        response = self.run()  
        self.process_result(response)
        self.destroy()

    def on_stock_selection(self, *args):
        self.set_response_sensitive(gtk.RESPONSE_ACCEPT, True)
    
    def on_stock_deselection(self, *args):
        self.set_response_sensitive(gtk.RESPONSE_ACCEPT, False)   
        
    def process_result(self, response):
        if response == gtk.RESPONSE_ACCEPT:
            stock = self.stock_selector.get_stock()
            stock.update_price()
            pos = controller.newWatchlistPosition(price=stock.price, date=stock.date, watchlist=self.wl, stock = stock)
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
        
        vbox.pack_start(gtk.Label(str(pos.stock)))

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
            pass
            #self.selected_pf = session['model'].portfolios[model[index][0]]
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
    #import objects, persistent_store
    #store = persistent_store.Store('test.db')
    #model = objects.Model(store)
    #d = MergeDialog(model)
    #gtk.main()
    PrefDialog() 
