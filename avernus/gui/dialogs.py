#!/usr/bin/env python

import gtk, pango
from avernus import pubsub, config
from datetime import datetime
from avernus.objects import controller, stock
from avernus.gui import gui_utils


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
        
        self.attach(gtk.Label(_('Name')),0,1,0,1, yoptions=gtk.FILL)
        self.name_entry = gtk.Entry()
        self.name_entry.set_text(stock.name)
        self.attach(self.name_entry,1,2,0,1,yoptions=gtk.FILL)

        self.attach(gtk.Label(_('ISIN')),0,1,1,2, yoptions=gtk.FILL)
        self.isin_entry = gtk.Entry()
        self.isin_entry.set_text(stock.isin)
        self.attach(self.isin_entry,1,2,1,2,yoptions=gtk.FILL)

        self.attach(gtk.Label(_('Type')),0,1,2,3, yoptions=gtk.FILL)
        liststore = gtk.ListStore(str, int)
        for key, val in [('fund',0), ('stock',1), ('etf',2)]:
            liststore.append([key, val])
        self.type_cb = cb = gtk.ComboBox(liststore)
        cell = gtk.CellRendererText()
        cb.pack_start(cell, True)
        cb.add_attribute(cell, 'text', 0)  
        cb.set_active(self.stock.type)
        self.attach(cb, 1,2,2,3,  yoptions=gtk.FILL)

        self.attach(gtk.Label(_('Sector')),0,1,3,4, yoptions=gtk.FILL)
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
        self.attach(self.sector_cb, 1,2,3,4,  yoptions=gtk.FILL)

    def process_result(self, widget=None, response = gtk.RESPONSE_ACCEPT):
        if response == gtk.RESPONSE_ACCEPT:
            self.stock.name = self.name_entry.get_text()
            self.stock.isin = self.isin_entry.get_text()
            active_iter = self.type_cb.get_active_iter()
            self.stock.type = self.type_cb.get_model()[active_iter][1]
            if self.sector_cb.get_active() != 0:   
                self.stock.sector = self.sectors[self.sector_cb.get_active()]
            else:
                self.stock.sector = None
            pubsub.publish("stock.edited", self.stock) 


class EditPositionTable(gtk.Table):

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
        self.comment_entry.set_size_request(50, 80)
        self.comment_entry.set_wrap_mode(pango.WRAP_WORD)
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


SPINNER_SIZE = 40

class StockSelector(gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self)
        self.search_field = gtk.Entry()
        self.search_field.set_icon_from_stock(1, gtk.STOCK_FIND)
        self.search_field.connect('activate', self.on_search)
        self.search_field.connect('icon-press', self.on_search)
        self.pack_start(self.search_field, expand=False, fill=False)
        
        sw = gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        self.result_tree = gui_utils.Tree()
        self.result_tree.model = gtk.TreeStore(object, str, str,str,str,str)
        self.result_tree.set_model(self.result_tree.model)
        self.result_tree.create_icon_column(None, 1)
        col, cell = self.result_tree.create_column(_('Name'), 2)
        self.result_tree.create_column('ISIN', 3)
        self.result_tree.create_column(_('Currency'), 4)
        self.result_tree.create_icon_column(_('Type'), 5,size= gtk.ICON_SIZE_DND)
        self.result_tree.set_size_request(600,300)
        sw.connect_after('size-allocate', 
                         gui_utils.resize_wrap, 
                         self.result_tree, 
                         col, 
                         cell)
        
        sw.add(self.result_tree)
        self.pack_end(sw)
        self.spinner = None

    def get_stock(self):
        path, col = self.result_tree.get_cursor()
        return self.result_tree.get_model()[path][0]

    def _show_spinner(self):
        self.spinner = gtk.Spinner()
        self.pack_start(self.spinner, fill=True, expand=False)
        self.spinner.show()
        self.spinner.set_size_request(SPINNER_SIZE, SPINNER_SIZE);
        self.spinner.start()
    
    def _hide_spinner(self):
        if self.spinner:
            self.remove(self.spinner)

    def on_search(self, *args):
        self.stop_search()
        self.result_tree.clear()
        searchstring = self.search_field.get_text()
        self._show_spinner()
        for item in controller.getStockForSearchstring(searchstring):
            self.insert_item(item)
        self.search_source_count = controller.datasource_manager.get_source_count()
        controller.datasource_manager.search(searchstring, self.insert_item, self.search_complete_callback)
    
    def search_complete_callback(self):
        self.search_source_count -= 1
        if self.search_source_count == 0:
            self._hide_spinner()
    
    def stop_search(self):
        self._hide_spinner()
        controller.datasource_manager.stop_search()
        
    def insert_item(self, stock, icon='gtk-harddisk'):
        icons = ['fund', 'stock', 'etf']
        self.result_tree.get_model().append(None, [
                                       stock, 
                                       icon,
                                       stock.name,
                                       stock.isin,
                                       stock.currency,
                                       icons[stock.type]
                                       ])

class SellDialog(gtk.Dialog):
    def __init__(self, pos, transaction = None):
        if transaction is None:
            title = _('Sell position')
            max_quantity = pos.quantity
        else:
            title = _('Edit position')
            max_quantity = pos.quantity + transaction.quantity
        gtk.Dialog.__init__(self, title, None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self.pos = pos
        self.transaction = transaction
        
        vbox = self.get_content_area()
        table = gtk.Table()
        table.set_row_spacings(4)
        table.set_col_spacings(4)
        vbox.pack_end(table)
        
        #name
        label = gtk.Label()
        label.set_markup(gui_utils.get_name_string(pos.stock))
        label.set_alignment(xalign=0.0, yalign=0.5)
        table.attach(label, 0,2,0,1,xoptions=gtk.FILL, yoptions=0)
        
        #shares entry
        
        table.attach(gtk.Label(_('Shares')),1,2,1,2)
        self.shares_entry = gtk.SpinButton(gtk.Adjustment(lower=0, upper=max_quantity,step_incr=1, value = 0), digits=2)
        self.shares_entry.connect("value-changed", self.on_change)
        table.attach(self.shares_entry, 2,3,1,2,xoptions=gtk.SHRINK,yoptions=gtk.SHRINK)
        
        #price entry
        table.attach(gtk.Label(_('Price:')),1,2,2,3)
        self.price_entry = gtk.SpinButton(gtk.Adjustment(lower=0, upper=100000,step_incr=0.1, value = 1.0), digits=2)
        self.price_entry.connect("value-changed", self.on_change)
        table.attach(self.price_entry, 2,3,2,3,xoptions=gtk.SHRINK,yoptions=gtk.SHRINK)
        
        #ta_costs entry
        table.attach(gtk.Label(_('Transaction Costs')),1,2,3,4,xoptions=gtk.SHRINK,yoptions=gtk.SHRINK)
        self.tacosts_entry = gtk.SpinButton(gtk.Adjustment(lower=0, upper=100000,step_incr=0.1, value = 0.0), digits=2)
        self.tacosts_entry.connect("value-changed", self.on_change)
        table.attach(self.tacosts_entry,2,3,3,4,xoptions=gtk.SHRINK,yoptions=gtk.SHRINK)
        
        #total
        table.attach(gtk.Label(_('Total')),1,2,4,5,xoptions=gtk.SHRINK,yoptions=gtk.SHRINK)
        self.total = gtk.Label()
        self.total.set_markup('<b>'+gui_utils.get_string_from_float(0.0)+'</b>')
        table.attach(self.total,2,3,4,5,xoptions=gtk.SHRINK,yoptions=gtk.SHRINK)
        
        #date 
        self.calendar = gtk.Calendar()
        table.attach(self.calendar, 0,1,1,5)
        
        if self.transaction is not None:
            self.shares_entry.set_value(self.transaction.quantity)
            self.price_entry.set_value(self.transaction.price)
            self.tacosts_entry.set_value(self.transaction.costs)
            self.calendar.select_month(self.transaction.date.month-1, self.transaction.date.year)
            self.calendar.select_day(self.transaction.date.day)
            self.on_change()
        
        self.show_all()
        self.response = self.run()  
        self.process_result()
        
        self.destroy()
        
    def process_result(self):
        if self.response == gtk.RESPONSE_ACCEPT:
            shares = self.shares_entry.get_value()
            price = self.price_entry.get_value()
            year, month, day = self.calendar.get_date()
            date = datetime(year, month+1, day)
            ta_costs = self.tacosts_entry.get_value()

            if self.transaction is None:
                if shares == 0.0:
                    return
                self.pos.quantity -= shares
                self.pos.portfolio.cash += shares*price - ta_costs    
                ta = controller.newTransaction(portfolio=self.pos.portfolio, position=self.pos, type=0, date=date, quantity=shares, price=price, costs=ta_costs) 
                pubsub.publish('transaction.added', ta)             
            else:
                diff = self.transaction.quantity - shares
                self.pos.quantity += diff
                self.pos.portfolio.cash -= self.transaction.quantity*self.transaction.price - self.transaction.costs
                self.pos.portfolio.cash += shares*price - ta_costs 
                self.transaction.price=price
                self.transaction.date = date
                self.transaction.costs = ta_costs
                self.transaction.quantity = shares
            
    def on_change(self, widget=None):
        total = self.shares_entry.get_value() * self.price_entry.get_value() + self.tacosts_entry.get_value()
        self.total.set_markup('<b>'+gui_utils.get_string_from_float(total)+'</b>')

class CashDialog(gtk.Dialog):
    def __init__(self, pf, type = 0, transaction=None):  #0 deposit, 1 withdraw
        self.action_type = type
        self.transaction = transaction
        if type == 0:
            text = _("Deposit cash")
        else: text = _("Withdraw cash")
        gtk.Dialog.__init__(self, text, None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        self.pf = pf
        vbox = self.get_content_area()

        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        hbox.pack_start(gtk.Label(_('Amount:')))
        self.amount_entry = gtk.SpinButton(gtk.Adjustment(lower=0, upper=100000,step_incr=0.1, value = 1.0), digits=2)
        hbox.pack_start(self.amount_entry)

        self.calendar = gtk.Calendar()
        vbox.pack_start(self.calendar)

        if self.transaction is not None:
            self.amount_entry.set_value(self.transaction.price)
            self.calendar.select_month(self.transaction.date.month-1, self.transaction.date.year)
            self.calendar.select_day(self.transaction.date.day)
        
        self.show_all()
        response = self.run()
        self.process_result(response = response)
        self.destroy()

    def process_result(self, widget=None, response = gtk.RESPONSE_ACCEPT):
        if response == gtk.RESPONSE_ACCEPT:
            amount = self.amount_entry.get_value()
            year, month, day = self.calendar.get_date()
            date = datetime(year, month+1, day)
            if self.transaction is None:
                if self.action_type == 0:
                    ta = controller.newTransaction(date=date, portfolio=self.pf, type=3, price=amount, quantity=1, costs=0.0)
                else:
                    ta = controller.newTransaction(date=date, portfolio=self.pf, type=4, price=amount, quantity=1, costs=0.0)
                pubsub.publish('transaction.added', ta)
            else:
                self.transaction.date = date
                self.transaction.price = amount
            if self.action_type == 0:
                self.pf.cash += amount
            else:
                self.pf.cash -= amount
 
 
class BuyDialog(gtk.Dialog):

    def __init__(self, pf, transaction=None):
        gtk.Dialog.__init__(self, _("Buy a position"), None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self.pf = pf
        self.transaction = transaction
        if transaction is None:
            self.b_new = True
        else:
            self.b_new = False
        
        
        vbox = self.get_content_area()
        table = gtk.Table()
        table.set_row_spacings(4)
        table.set_col_spacings(4)
        vbox.pack_end(table)
        if self.b_new:
            #stock entry
            self.stock_selector = StockSelector()
            table.attach(self.stock_selector,0,3,0,1)
            self.stock_selector.result_tree.connect('cursor-changed', self.on_stock_selection)
            self.stock_selector.result_tree.get_model().connect('row-deleted', self.on_stock_deselection)
            self.stock_ok = False
        else:
            label = gtk.Label()
            label.set_markup(gui_utils.get_name_string(self.transaction.position.stock))
            label.set_alignment(xalign=0.0, yalign=0.5)
            table.attach(label, 0,3,0,1,xoptions=gtk.FILL, yoptions=0)

        #shares entry
        table.attach(gtk.Label(_('Shares')),1,2,1,2,xoptions=gtk.SHRINK,yoptions=gtk.SHRINK)
        self.shares_entry = gtk.SpinButton(gtk.Adjustment(lower=0, upper=100000,step_incr=1.0, value = 0), digits=2)
        self.shares_entry.connect("value-changed", self.on_change)
        table.attach(self.shares_entry,2,3,1,2,xoptions=gtk.SHRINK,yoptions=gtk.SHRINK)
        
        #price entry
        table.attach(gtk.Label(_('Price')),1,2,2,3,xoptions=gtk.SHRINK,yoptions=gtk.SHRINK)
        self.price_entry = gtk.SpinButton(gtk.Adjustment(lower=0, upper=100000,step_incr=0.1, value = 1.0), digits=2)
        self.price_entry.connect("value-changed", self.on_change)
        table.attach(self.price_entry,2,3,2,3,xoptions=gtk.SHRINK,yoptions=gtk.SHRINK)
        
        #ta_costs entry
        table.attach(gtk.Label(_('Transaction Costs')),1,2,3,4,xoptions=gtk.SHRINK,yoptions=gtk.SHRINK)
        self.tacosts_entry = gtk.SpinButton(gtk.Adjustment(lower=0, upper=100000,step_incr=0.1, value = 0.0), digits=2)
        self.tacosts_entry.connect("value-changed", self.on_change)
        table.attach(self.tacosts_entry,2,3,3,4,xoptions=gtk.SHRINK,yoptions=gtk.SHRINK)
        
        #total
        table.attach(gtk.Label(_('Total')),1,2,4,5,xoptions=gtk.SHRINK,yoptions=gtk.SHRINK)
        self.total = gtk.Label()
        self.total.set_markup('<b>'+gui_utils.get_string_from_float(0.0)+'</b>')
        table.attach(self.total,2,3,4,5,xoptions=gtk.SHRINK,yoptions=gtk.SHRINK)
        
        #date 
        self.calendar = gtk.Calendar()
        self.calendar.connect('day-selected', self.on_calendar_day_selected)
        table.attach(self.calendar,0,1,1,5,yoptions=gtk.SHRINK)
        self.date_ok = True
        
        self.infobar = gtk.InfoBar()
        self.infobar.set_message_type(gtk.MESSAGE_WARNING)
        
        if not self.b_new:
            self.stock_ok = True
            self.shares_entry.set_value(self.transaction.quantity)
            self.price_entry.set_value(self.transaction.price)
            self.tacosts_entry.set_value(self.transaction.costs)
            self.calendar.select_month(self.transaction.date.month-1, self.transaction.date.year)
            self.calendar.select_day(self.transaction.date.day)
            self.on_change()
        
        content = self.infobar.get_content_area()
        label = gtk.Label('Date cannot be in the future!')
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_DIALOG)
        content.pack_start(image)
        content.pack_start(label)
        vbox.pack_start(self.infobar)
        
        if self.b_new:
            self.set_response_sensitive(gtk.RESPONSE_ACCEPT, False)
        table.show_all()
        response = self.run()  
        self.process_result(response)
        self.destroy()
    
    def on_calendar_day_selected(self, calendar):
        year, month, day = self.calendar.get_date()
        date = datetime(year, month+1, day)
        if date > datetime.today():
            self.infobar.show_all()
            self.date_ok = False
        else:
            self.infobar.hide_all()
            self.date_ok = True
        self.set_response_sensitivity()

    def on_change(self, widget=None):
        total = self.shares_entry.get_value() * self.price_entry.get_value() + self.tacosts_entry.get_value()
        self.total.set_markup('<b>'+gui_utils.get_string_from_float(total)+'</b>')

    def on_stock_selection(self, *args):
        self.stock_ok = True
        self.set_response_sensitivity()
    
    def on_stock_deselection(self, *args):
        self.stock_ok = False
        self.set_response_sensitivity()
        
    def set_response_sensitivity(self):
        if self.stock_ok and self.date_ok:
            self.set_response_sensitive(gtk.RESPONSE_ACCEPT, True)
        else:
            self.set_response_sensitive(gtk.RESPONSE_ACCEPT, False)  

    def process_result(self, response):
        if self.b_new:
            self.stock_selector.stop_search()
        if response == gtk.RESPONSE_ACCEPT:
            price = self.price_entry.get_value()
            year, month, day = self.calendar.get_date()
            date = datetime(year, month+1, day)
            ta_costs = self.tacosts_entry.get_value()
            shares = self.shares_entry.get_value()
            
            if self.b_new:
                stock = self.stock_selector.get_stock()
                stock.update_price()
                if shares == 0.0:
                    return
                pos = controller.newPortfolioPosition(price=price, date=date, quantity=shares, portfolio=self.pf, stock = stock)
                self.pf.cash -= shares*price - ta_costs 
                ta = controller.newTransaction(type=1, date=date,quantity=shares,price=price,costs=ta_costs, position=pos, portfolio=self.pf)
                #FIXME trigger publish in container.py and transaction.py
                pubsub.publish('container.position.added', self.pf, pos)
                pubsub.publish('transaction.added', ta)
            else:
                diff = self.transaction.quantity - shares
                self.transaction.position.quantity -= diff
                self.pf.cash += self.transaction.quantity*self.transaction.price - self.transaction.costs
                self.pf.cash -= shares*price - ta_costs 
                self.transaction.price = price
                self.transaction.date = date
                self.transaction.costs = ta_costs
                self.transaction.quantity = shares
                


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
        self.stock_selector.stop_search()
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
        liststore = gtk.ListStore(object, str)
        liststore.append([-1, 'Select a position'])
        for pos in pf:
            liststore.append([pos, str(pos.quantity) +' ' +pos.name])
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


if __name__ == "__main__":
    #import objects, persistent_store
    #store = persistent_store.Store('test.db')
    #model = objects.Model(store)
    #d = MergeDialog(model)
    #gtk.main()
    PrefDialog() 