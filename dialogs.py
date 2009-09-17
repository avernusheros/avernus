import gtk
import objects, updater
from datetime import datetime

#TODO dialogen immer parent window mitgeben


class EditWatchlist(gtk.Dialog):
    def __init__(self, wl):
        gtk.Dialog.__init__(self, "Edit...", None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        
        self.wl = wl
        vbox = self.get_content_area()
        
        #name entry
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        label = gtk.Label('Name:')
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
    def __init__(self, pf):
        EditWatchlist.__init__(self, pf)

class NewContainerDialog(gtk.Dialog):
    def __init__(self, model):
        gtk.Dialog.__init__(self, "Create...", None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        
        self.model = model
        vbox = self.get_content_area()
        
        
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        self.radiobutton = button = gtk.RadioButton(None, "Portfolio")
        hbox.pack_start(button, True, True, 0)
        
        button = gtk.RadioButton(button, "Watchlist")
        hbox.pack_start(button, True, True, 0)
               
        #name entry
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        label = gtk.Label('Name:')
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


class BuyDialog(gtk.Dialog):
    def __init__(self, pf, model):
        gtk.Dialog.__init__(self, "Buy a stock", None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self.pf = pf
        self.model = model
        
        vbox = self.get_content_area()
        #symbol entry
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        hbox.pack_start(gtk.Label('Symbol:'))
        self.symbol_entry = gtk.Entry()
        hbox.pack_start(self.symbol_entry)

        #shares entry
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        hbox.pack_start(gtk.Label('Shares:'))
        self.shares_entry = gtk.Entry()
        hbox.pack_start(self.shares_entry)
        
        #price entry
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        hbox.pack_start(gtk.Label('Price:'))
        self.price_entry = gtk.Entry()
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
            symbol = self.symbol_entry.get_text()
            shares = float(self.shares_entry.get_text())
            price = float(self.price_entry.get_text())
            stock = self.model.get_stock(symbol, update = True)
            year, month, day = self.calendar.get_date()
            date = datetime(year, month, day)
            position = self.pf.add_position(symbol, price, date, shares)

class NewWatchlistPositionDialog(gtk.Dialog):
    def __init__(self, wl, model):
        gtk.Dialog.__init__(self, "Create...", None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        
        self.wl = wl
        self.model = model
        vbox = self.get_content_area()
        
        #symbol entry
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        label = gtk.Label('Symbol:')
        hbox.pack_start(label)
        self.symbol_entry = gtk.Entry()
        hbox.pack_start(self.symbol_entry)

        self.show_all()
        response = self.run()  
        self.process_result(response)
        
        self.destroy()

    def process_result(self, response):
        if response == gtk.RESPONSE_ACCEPT:
            symbol = self.symbol_entry.get_text()
            stock = self.model.get_stock(symbol, update = True)
            position = self.wl.add_position(symbol,stock.price, stock.date, 1)
            
        
if __name__ == "__main__":
    import objects, persistent_store
    store = persistent_store.Store('test.db')
    model = objects.Model(store)
    d = NewWatchlistDialog(model)
    gtk.main() 
