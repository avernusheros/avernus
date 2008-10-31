try:
    import sys, os
    import gtk
    import gtk.glade
    import config, helper
    from db import *
except ImportError, e:
    print "Import error in dialogs:", e
    sys.exit(1)

db = database.get_db()

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
                self.save_data_to_db()
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
    def __init__(self, glade_file):
        self.glade_file = glade_file
        self.item = {}
        #Get the widget tree
        self.wTree = gtk.glade.XML(self.glade_file, "watchlistDialog")
        #Connect with yourself
        self.wTree.signal_autoconnect(self)
        self.dialog = self.wTree.get_widget("watchlistDialog")
        #get the widgets from the dlg
        self.enterName = self.wTree.get_widget("enterName")
        self.enterDescription = self.wTree.get_widget("enterDescription")
    
    def save_data_to_db(self):
        """This function is used to read the data from the dialog
        and then store it in the db.
        """
        self.item['name'] = self.enterName.get_text()
        self.item['type'] = config.WATCHLIST
        txtBuffer = self.enterDescription.get_buffer()
        self.item['comment'] = txtBuffer.get_text(*txtBuffer.get_bounds())
        self.item['id'] = db.add_portfolio(self.item['name'], self.item['comment'], 0.0,self.item['type'] )
    
 
class QuoteDialog(Dialog):
    """This is a class that is used to show a quoteDialog.  It
    can be used to create or edit a watchlist.quote.  To create one
    simply initialize the class and do not pass a quote.  If you
    want to edit an object initialize with the object that
    you want to edit."""

    def __init__(self, glade_file, watchlist_id):
        """Initialize the quote dialog.
        @param glade_file - string - the glade file for this dialog.
        """
        self.glade_file = glade_file
        #Get the widget tree
        self.wTree = gtk.glade.XML(self.glade_file, "quoteDialog")
        #Connect with yourself
        self.wTree.signal_autoconnect(self)
        self.dialog = self.wTree.get_widget("quoteDialog")
        #get the widgets from the dlg
        self.enterSymbol = self.wTree.get_widget("enterSymbol")
        self.enterComment = self.wTree.get_widget("enterComment")
        self.header_name = self.wTree.get_widget("add_position_name")
        self.header_performance = self.wTree.get_widget("add_position_performance")
        self.header_icon = self.wTree.get_widget("add_postion_icon")
        self.stock_id = None
        self.autocomplete()
        self.item = {}
        self.item['portfolio_id'] = watchlist_id
        
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
        self.update_stock_info()
        return
    
    def update_stock_info(self):
        #if a stock is selected
        if self.stock_id:
            item = self.db.get_stock_name(self.stock_id) #name, isin, exchange
            data = helper.update_stock(self.stock_id)
            color = '#606060'
            text = '<span size="medium"><b>' + item['name'] + '</b></span>\n\
                    <span size="small">' + item['isin'] + '</span>\n\
                    <span size="small">' + item['exchange'] + '</span>\n\
                    <span size="small">Volume: ' + data['volume'] + '</span>'
            self.header_name.set_markup(text)
            text = '<span size="medium"><b>' + data['price'] + '</b></span>\n<span size="small">' + data['change'] + '</span>\n<span size="small">' + str(data['percent']) + '%</span>'
            self.header_performance.set_markup(text)
            self.header_icon.set_from_file(helper.get_arrow_type(float(data['percent'])))
            self.header_icon.show()
        else:
            self.header_icon.hide()
        #save data to item which is returned 
        for k, v in data.iteritems():
            self.item[k] = v   
        for k, v in item.iteritems():
            self.item[k] = v

    def save_data_to_db(self):
        """This function is used to read the data from the dialog
        and then store it in the watchlist.quote object.
        """
        #get data from widget
        self.item['stock_id']         = self.stock_id
        self.item['comment']          = self.get_comment()
        self.item['quantity']         = 1
        self.item['transactioncosts'] = 0.0
        self.item['type']             = config.WATCHLISTITEM
        self.item['buy_sum']          = float(self.item['price'])
                                        
        #insert into positions table
        self.item['id'] = db.add_position(self.item['portfolio_id']
                , self.item['stock_id'], self.item['comment']
                , self.item['date'], self.item['quantity']
                , self.item['price'], self.item['type'], self.item['buy_sum'])

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
        

class PortfolioDialog(Dialog):
    """Initialize the portfolio dialog.
    @param glade_file - string - the glade file for this dialog.
    """
    def __init__(self, glade_file):
        self.glade_file = glade_file
        #Get the widget tree
        self.wTree = gtk.glade.XML(self.glade_file, "portfolioDialog")
        #Connect with yourself
        self.wTree.signal_autoconnect(self)
        self.dialog = self.wTree.get_widget("portfolioDialog")
        #get the widgets from the dlg
        self.enterName = self.wTree.get_widget("enterPortfolioName")
        self.enterDescription = self.wTree.get_widget("enterPortfolioDescription")
        self.item = {}
    
    def save_data_to_db(self):
        """This function is used to read the data from the dialog
        and then store it in the db.
        """
        self.item['name'] = self.enterName.get_text()
        self.item['type'] = config.PORTFOLIO
        txtBuffer = self.enterDescription.get_buffer()
        self.item['comment'] = txtBuffer.get_text(*txtBuffer.get_bounds())
        self.item['id'] = db.add_portfolio(self.item['name'], self.item['comment'], 0.0,self.item['type'] )
  
        
class BuyDialog(QuoteDialog):
    """
    stock buying dialog
    """
    def __init__(self, glade_file, portfolio_id):
        """Initialize the buy dialog.
        @param glade_file - string - the glade file for this dialog.
        @param quote - watchlist.quote - None to create a new 
                       watchlist.quote object, or the object that you wish to edit.
        """
        self.glade_file = glade_file
        self.item = {}
        self.item['portfolio_id'] = portfolio_id
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
        self.header_name = self.wTree.get_widget("buy_position_name")
        self.header_performance = self.wTree.get_widget("buy_position_performance")
        self.header_icon = self.wTree.get_widget("buy_postion_icon")
        self.transactioncosts = self.wTree.get_widget("buyTransactionCosts")
        self.autocomplete()
    
    def save_data_to_db(self):
        """This function is used to read the data from the dialog
        and then store it in the db.
        """
        #get data from widgets
        self.item['stock_id']         = self.stock_id
        self.item['comment']          = self.get_comment()
        self.item['quantity']         = self.numShares.get_text()
        self.item['price']            = self.enterBuyPrice.get_text()
        self.item['date']             = str(self.buyDate.get_date())
        self.item['transactioncosts'] = self.transactioncosts.get_text()
        self.item['type']             = config.PORTFOLIOITEM
        self.item['buy_sum']          = (float(self.item['price'])  
                                        * float(self.item['quantity'])
                                        + float(self.item['transactioncosts']))
        #insert into positions table
        self.item['id'] = db.add_position(self.item['portfolio_id']
                , self.item['stock_id'], self.item['comment']
                , self.item['date'], self.item['quantity']
                , self.item['price'], self.item['type'], self.item['buy_sum'])
        #insert transaction into db
        self.item['id'] = db.add_transaction(self.item['portfolio_id']
                        , self.item['id'], config.TRANSACTION_BUY
                        , self.item['date'], self.item['quantity']
                        , self.item['transactioncosts'])
                        
