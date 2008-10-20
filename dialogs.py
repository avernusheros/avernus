try:
    import sys, os
    import gtk
    import gtk.glade
    import items
    from data import *
except ImportError, e:
    print _T("Import error in watchlist:"), e
    sys.exit(1)


class Dialog(object):
    def __init__(self):
        pass
        
    def find_text_in_combo(self, combobox, text):
        """This is a helper function use to find text in a gtk.ComboBox.
        @param combobox gtk.ComboBox - This should contain text.
        @param text - string - the text that we are looking to find.
        @returns - gtk.TreeIter - The iter at the found position or None if nothing was found.
        """
        found_iter = None #The Iter where text is found
        #Get the gtk.TreeModel associated with the combo
        combo_model = combobox.get_model()
        if (combo_model):
            #Get the first iter in the model
            search_iter = combo_model.get_iter_first()
            """Now loop through the model checking for
            matches until one is found.  Or until
            we have ran out of iters."""
            while ((found_iter == None)
                and (search_iter)):
                if (text == combo_model[search_iter][0]):
                    #Found!
                    found_iter = search_iter
                else:
                    search_iter = combo_model.iter_next(search_iter)
        return found_iter
    
    def run(self):
        """Show the dialog"""
        break_out = False
        while (not break_out):
            result = self.dialog.run()
            if (result==gtk.RESPONSE_OK):
                #Save the date to the object becuase the use pressed ok.
                self.save_data_to_object()
                break_out = True
                #Validate here eventually
            else:
                break_out = True
        self.dialog.hide()
        return result;
    
    
class WatchlistDialog(Dialog):
    """Initialize the quote dialog.
    @param glade_file - string - the glade file for this dialog.
    @param item -  None to create a new 
                   watchlist object, or the object that you wish to edit.
    """
    def __init__(self, glade_file, item = None):
        self.glade_file = glade_file
        self.item = item
        #Get the widget tree
        self.wTree = gtk.glade.XML(self.glade_file, "watchlistDialog")
        #Connect with yourself
        self.wTree.signal_autoconnect(self)
        self.dialog = self.wTree.get_widget("watchlistDialog")
        #get the widgets from the dlg
        self.enterName = self.wTree.get_widget("enterName")
        self.enterDescription = self.wTree.get_widget("enterDescription")
        #update dialog
        self.update_dialog_from_object()
        
    def update_dialog_from_object(self):
        """Used to update the settings on the dialog"""
        if (self.item):
            #Name
            self.enterName.set_text(self.item.name)
            #Comment
            self.set_description(self.item.description)
    
    def save_data_to_object(self):
        """This function is used to read the data from the dialog
        and then store it in the watchlist.quote object.
        """
        if (self.item == None):
            self.item = items.Watchlist(self.enterName.get_text(), self.get_description())
        else:
            self.item.name = self.enterName.get_text()
            self.item.description = self.get_description()
        
    def get_description(self):
        """This function gets the details from the TextView
        @returns string - The text in the gtk.TextView
        """
        txtBuffer = self.enterDescription.get_buffer()
        return txtBuffer.get_text(*txtBuffer.get_bounds())

    def set_description(self, description):
        """This function sets the text in the defails gtk.TextView
        @param details - string - The text that will be
        put into the gtk.TextView.
        """
        txtBuffer = self.enterDescription.get_buffer()
        txtBuffer.set_text(description)
    
 
class QuoteDialog(Dialog):
    """This is a class that is used to show a quoteDialog.  It
    can be used to create or edit a watchlist.quote.  To create one
    simply initialize the class and do not pass a quote.  If you
    want to edit an object initialize with the object that
    you want to edit."""

    def __init__(self, glade_file, stock = None):
        """Initialize the quote dialog.
        @param glade_file - string - the glade file for this dialog.
        @param stock - watchlist.quote - None to create a new 
                       watchlist.quote object, or the object that you wish to edit.
        """
        self.glade_file = glade_file
        self.stock = stock
        #Get the widget tree
        self.wTree = gtk.glade.XML(self.glade_file, "quoteDialog")
        #Connect with yourself
        self.wTree.signal_autoconnect(self)
        self.dialog = self.wTree.get_widget("quoteDialog")
        #get the widgets from the dlg
        self.enterSymbol = self.wTree.get_widget("enterSymbol")
        self.enterComment = self.wTree.get_widget("enterComment")
        self.stock_id = None
        self.autocomplete()
        #update dialog
        self.update_dialog_from_object()
        
    def autocomplete(self):
        #get db
        self.db = database.get_db()
        self.db.connect()

        completion = gtk.EntryCompletion()
        self.liststore = gtk.ListStore(str, str, str, str)
        cell0 = gtk.CellRendererText()
        cell0.set_property('size', 0)
        cell1 = gtk.CellRendererText()
        cell1.set_property('foreground', 'gray')
        cell2 = gtk.CellRendererText()
        cell3 = gtk.CellRendererText()
        cell3.set_property('foreground', 'gray')
        completion.pack_start(cell0, expand = False)
        completion.add_attribute(cell0, 'text', 0)
        completion.pack_start(cell1, expand = True)
        completion.add_attribute(cell1, 'text', 1)
        completion.pack_start(cell2, expand = True)
        completion.add_attribute(cell2, 'text', 2)
        completion.pack_start(cell3, expand = True)
        completion.add_attribute(cell3, 'text', 3)
        completion.set_property('text_column', 3)
        list = self.db.get_stock_list()
        for item in list:
            self.liststore.append(item)
        completion.set_model(self.liststore)
        self.enterSymbol.set_completion(completion)
        completion.set_text_column(2)
        completion.connect('match-selected', self.match_cb)      
        
    def match_cb(self, completion, model, iter):
        self.stock_id = model[iter][0]
        print self.stock_id, 'was selected'
        return

    def update_dialog_from_object(self):
        """Used to update the settings on the dialog"""
        if self.stock:
            #Symbol
            #self.enterSymbol.set_text(self.quote.symbol)
            #Comment
            self.set_comment(self.stock.stock.comment)

    def save_data_to_object(self):
        """This function is used to read the data from the dialog
        and then store it in the watchlist.quote object.
        """
        if not self.stock:
            self.stock = items.WatchlistItem(self.stock_id, self.get_comment())
        else:
            self.stock.comment = self.get_comment()

    def get_comment(self):
        """This function gets the details from the TextView
        @returns string - The text in the gtk.TextView
        """
        txtBuffer = self.enterComment.get_buffer()
        return txtBuffer.get_text(*txtBuffer.get_bounds())

    def set_comment(self, comment):
        """This function sets the text in the defails gtk.TextView
        @param details - string - The text that will be
        put into the gtk.TextView.
        """
        txtBuffer = self.enterComment.get_buffer()
        txtBuffer.set_text(comment)
        

class PortfolioDialog(WatchlistDialog):
    """Initialize the portfolio dialog.
    @param glade_file - string - the glade file for this dialog.
    @param item - None to create a new 
                   porfolio object, or the object that you wish to edit.
    """
    def __init__(self, glade_file, item = None):
        self.glade_file = glade_file
        self.item = item
        #Get the widget tree
        self.wTree = gtk.glade.XML(self.glade_file, "portfolioDialog")
        #Connect with yourself
        self.wTree.signal_autoconnect(self)
        self.dialog = self.wTree.get_widget("portfolioDialog")
        #get the widgets from the dlg
        self.enterName = self.wTree.get_widget("enterPortfolioName")
        self.enterDescription = self.wTree.get_widget("enterPortfolioDescription")
        #update dialog
        self.update_dialog_from_object()
    
    def save_data_to_object(self):
        """This function is used to read the data from the dialog
        and then store it in the watchlist.quote object.
        """
        if (self.item == None):
            self.item = items.Portfolio(self.enterName.get_text(), self.get_description())
        else:
            self.item.name = self.enterName.get_text()
            self.item.description = self.get_description()
     
        
class BuyDialog(QuoteDialog):
    """
    stock buying dialog
    """
    def __init__(self, glade_file, position = None):
        """Initialize the buy dialog.
        @param glade_file - string - the glade file for this dialog.
        @param quote - watchlist.quote - None to create a new 
                       watchlist.quote object, or the object that you wish to edit.
        """
        self.glade_file = glade_file
        self.position = position
        #Get the widget tree
        self.wTree = gtk.glade.XML(self.glade_file, "buyDialog")
        #Connect with yourself
        self.wTree.signal_autoconnect(self)
        self.dialog = self.wTree.get_widget("buyDialog")
        #get the widgets from the dlg
        self.enterSymbol = self.wTree.get_widget("enterBuySymbol")
        self.enterComment = self.wTree.get_widget("enterBuyComment")
        self.numShares = self.wTree.get_widget("enterBuyNumShares")
        self.enterBuyPrice = self.wTree.get_widget("enterBuyPrice")
        self.buyDate = self.wTree.get_widget("buyDate")
        self.transactioncosts = self.wTree.get_widget("buyTransactionCosts")
        self.buy_position_name = self.wTree.get_widget("buy_position_name")
        #update dialog
        self.update_dialog_from_object()
        self.autocomplete()
    
    def match_cb(self, completion, model, iter):
        self.stock_id = model[iter][0]
        self.update_stock_info()
        return
        
    def update_stock_info(self):
        #if a stock is selected
        if self.stock_id:
            print "setting stock info.. "
            info = self.db.get_stock_name(self.stock_id) #name, isin, exchange
            color = '#606060'
            text = info[0] +"\n \
                <span foreground=\""+ color +"\"><small>" +info[1]+ "</small></span>\n \
                 <span foreground=\""+ color +"\"><small>" +info[2]+ "</small></span>"
            self.buy_position_name.set_markup(text)
    
    def update_dialog_from_object(self):
        """Used to update the settings on the dialog"""
        if (self.position):
            #Symbol
            #self.enterSymbol.set_text(self.quote.symbol)
            #Comment
            self.set_comment(self.position.stock.comment)

    def save_data_to_object(self):
        """This function is used to read the data from the dialog
        and then store it in the watchlist.quote object.
        """
        #get data from widgets
        stock_id           = self.stock_id
        comment          = self.get_comment()
        quantity         = self.numShares.get_text()
        price            = self.enterBuyPrice.get_text()
        date             = self.buyDate.get_date()
        transactionCosts = self.transactioncosts.get_text()
        #create new position    
        if (self.position == None):
            self.position = items.PortfolioItem(stock_id,quantity,price,date,transactionCosts,comment)
        #or edit existing position
        else:
            self.position.symbol   = stock_id
            self.position.comment  = comment
            self.position.quantity = quantity
            self.position.buyPrice = price
            self.position.buyDate  = date
            self.position.transactionCosts = transactionCosts
        self.position.update()





