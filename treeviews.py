# -*- coding: iso-8859-15 -*-

import gtk, string,  logging, pytz
from pubsub import pub
import objects, dialogs, config




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


def fix(item):
    if len(item) == 2:
        a, b = item
        return a,b, None
    else:
        return item


def get_change_string(item):
    change, percent, absolute = fix(item)
    if change is None:
        return 'n/a'
    text = str(percent) + '%' + '\n' + str(change) + config.currency
    if absolute is not None:
        text += '\n' + str(absolute) + config.currency
    return text


class Category(object):
    def __init__(self, name):
        self.name = name

class Tree(gtk.TreeView):
    def __init__(self):
        self.selected_item = None
        gtk.TreeView.__init__(self)

    
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
        pub.subscribe(self.insert_watchlist, "watchlist.created")
        pub.subscribe(self.insert_portfolio, "portfolio.created")
        pub.subscribe(self.on_remove, "maintoolbar.remove")
        pub.subscribe(self.on_edit, "maintoolbar.edit")
        pub.subscribe(self.on_updated, "container.updated")
        
        self.selected_item = None


    def insert_categories(self):
        self.pf_iter = self.get_model().append(None, [-1, Category('Portfolios'),None,"<b>Portfolios</b>"])
        self.wl_iter = self.get_model().append(None, [-1, Category('Watchlists'),None,"<b>Watchlists</b>"])

    def insert_watchlist(self, item):
        self.get_model().append(self.wl_iter, [item.id, item, None, item.name])
    
    def insert_portfolio(self, item):
        self.get_model().append(self.pf_iter, [item.id, item, None, item.name])
         
    def on_remove(self):
        if self.selected_item is None:
            return
        obj, iter = self.selected_item
        if isinstance(obj, objects.Watchlist) or isinstance(obj, objects.Portfolio):
            dlg = gtk.MessageDialog(None, 
                 gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION, 
                    gtk.BUTTONS_OK_CANCEL, "Are you sure?")
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
            pub.sendMessage('maintree.selection', item = obj)        
        
    def on_edit(self):
        if self.selected_item is None:
            return
        obj, iter = self.selected_item
        if isinstance(obj, objects.Watchlist):
            dialogs.EditWatchlist(obj)
        elif isinstance(obj, objects.Portfolio):
            dialogs.EditPortfolio(obj)

    
class PositionsTree(Tree):
    def __init__(self, container, model, type):
        #type 0=wl 1=pf
        self.model = model
        self.container = container
        self.type = type
        Tree.__init__(self)
        #id, object, name, price, change
        self.set_model(gtk.TreeStore(int, object,str, str, str,str, str, str))
        
        column = gtk.TreeViewColumn('Shares')
        self.append_column(column)
        cell = gtk.CellRendererText()
        column.pack_start(cell, expand = True)
        column.add_attribute(cell, "markup", 7)
        column.set_sort_column_id(7)
        if type == 0:
            column.set_visible(False)
        
        column = gtk.TreeViewColumn('Name')
        self.append_column(column)
        cell = gtk.CellRendererText()
        column.pack_start(cell, expand = True)
        column.add_attribute(cell, "markup", 2)
        column.set_sort_column_id(2)
        
        column = gtk.TreeViewColumn('Start')
        self.append_column(column)
        cell = gtk.CellRendererText()
        column.pack_start(cell, expand = True)
        column.add_attribute(cell, "markup", 3)
        column.set_sort_column_id(3)
        
        column = gtk.TreeViewColumn('Current Price')
        self.append_column(column)
        cell = gtk.CellRendererText()
        column.pack_start(cell, expand = True)
        column.add_attribute(cell, "markup", 4)
        column.set_sort_column_id(4)
        
        column = gtk.TreeViewColumn('Current Change')
        self.append_column(column)
        cell = gtk.CellRendererText()
        column.pack_start(cell, expand = True)
        column.add_attribute(cell, "markup", 5)
        column.set_sort_column_id(5)
        
        column = gtk.TreeViewColumn('Overall Change')
        self.append_column(column)
        cell = gtk.CellRendererText()
        column.pack_start(cell, expand = True)
        column.add_attribute(cell, "markup", 6)
        column.set_sort_column_id(6)
          
        self.load_positions()
        
        self.connect('cursor_changed', self.on_cursor_changed)
        pub.subscribe(self.on_add_position, 'positionstoolbar.add')
        
        pub.subscribe(self.on_position_created, 'position.created')
        pub.subscribe(self.on_remove_position, 'positionstoolbar.remove')
        pub.subscribe(self.on_stock_updated, 'stock.updated')
        pub.subscribe(self.on_position_updated, 'position.updated')
        
        self.selected_item = None

    def load_positions(self):
        for pos in self.container:
            self.insert_position(pos)
    
    def on_position_updated(self, item):
        row = self.find_position(item.id)
        if row:
            if item.quantity == 0:
                self.get_model().remove(row.iter)
            else:
                row[7] = item.quantity
    
    def on_stock_updated(self, item):
        row = self.find_position_from_stock(item.id)
        if row:
            row[4] = self.get_price_string(item)
            row[5] = get_change_string(row[1].current_change)
            row[6] = get_change_string(row[1].overall_change)
                
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
                    gtk.BUTTONS_OK_CANCEL, "Are you sure?")
            response = dlg.run()
            dlg.destroy()
            if response == gtk.RESPONSE_OK:
                self.container.remove_position(obj)
                self.get_model().remove(iter)  
        elif self.type == 1:
            dialogs.SellDialog(self.container, obj)    
       
    def on_add_position(self):
        if self.type == 0:
            dialogs.NewWatchlistPositionDialog(self.container, self.model)  
        elif self.type == 1:
            dialogs.BuyDialog(self.container, self.model)
        
    def on_cursor_changed(self, widget):
        #Get the current selection in the gtk.TreeView
        selection = widget.get_selection()
        # Get the selection iter
        model, selection_iter = selection.get_selected()
        if (selection_iter and model):
            #Something is selected so get the object
            obj = model.get_value(selection_iter, 1)
            self.selected_item = obj, selection_iter
            pub.sendMessage('watchlistpositionstree.selection', item = obj)   
            
    def get_price_string(self, item):
        if item.price is None:
            return 'n/a'
        return str(item.price) + item.currency +'\n' +'<small>'+get_datetime_string(item.date)+'</small>'
        
    def insert_position(self, position):
        if position.quantity != 0:
            stock = self.model.stocks[position.stock_id]
            self.get_model().append(None, [position.id, position, get_name_string(stock), self.get_price_string(position), self.get_price_string(stock), get_change_string(position.current_change),get_change_string(position.overall_change),position.quantity])

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


class TransactionsTree(Tree):
    def __init__(self, portfolio, model):
        self.model = model
        self.portfolio = portfolio
        Tree.__init__(self)
        #id, object, name, price, change
        self.set_model(gtk.TreeStore(int, object,str, str, str,str, str, str))
        
        column = gtk.TreeViewColumn('Action')
        self.append_column(column)
        cell = gtk.CellRendererText()
        column.pack_start(cell, expand = True)
        column.add_attribute(cell, "markup", 2)
        column.set_sort_column_id(2)
        
        column = gtk.TreeViewColumn('Name')
        self.append_column(column)
        cell = gtk.CellRendererText()
        column.pack_start(cell, expand = True)
        column.add_attribute(cell, "markup", 3)
        column.set_sort_column_id(3)
        
        column = gtk.TreeViewColumn('Date')
        self.append_column(column)
        cell = gtk.CellRendererText()
        column.pack_start(cell, expand = True)
        column.add_attribute(cell, "markup", 4)
        column.set_sort_column_id(4)
        
        column = gtk.TreeViewColumn('Shares')
        self.append_column(column)
        cell = gtk.CellRendererText()
        column.pack_start(cell, expand = True)
        column.add_attribute(cell, "markup", 5)
        column.set_sort_column_id(5)
        
        column = gtk.TreeViewColumn('Price')
        self.append_column(column)
        cell = gtk.CellRendererText()
        column.pack_start(cell, expand = True)
        column.add_attribute(cell, "markup", 6)
        column.set_sort_column_id(6)
        
        column = gtk.TreeViewColumn('Transaction Costs')
        self.append_column(column)
        cell = gtk.CellRendererText()
        column.pack_start(cell, expand = True)
        column.add_attribute(cell, "markup", 7)
        column.set_sort_column_id(7)
        
        
        self.load_transactions()
        pub.subscribe(self.on_transaction_created, 'position.transaction.added')
        
        
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


