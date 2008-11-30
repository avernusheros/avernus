try:
    import sys, os
    import gtk
    import gtk.glade
    from stocktracker import config, helper
    from stocktracker.database import *
except ImportError, e:
    print "Import error in dialogs:", e
    sys.exit(1)

db = database.get_db()
main_application_window = None

class Dialog(object):
    def __init__(self):
        pass

    def run(self):
        """Show the dialog"""
        break_out = False
        while (not break_out):
            result = self.dialog.run()
            if (result==gtk.RESPONSE_OK):
                #Save the date to the object because the user pressed ok.
                self.save_data_to_db()
                break_out = True
                #Validate here eventually
            else:
                break_out = True
        self.dialog.destroy()
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
        self.item['cash'] = 0.0
        self.item['id'] = db.add_portfolio(self.item)


class QuoteDialog(Dialog):
    """This is a class that is used to show a quoteDialog.  It
    can be used to create a watchlist.quote."""

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
            text1 = '<span size="medium"><b>' + item['name'] + '</b></span>\n\
                    <span size="small">' + item['isin'] + '</span>\n\
                    <span size="small">' + item['exchange'] + '</span>'
            text2 = ''
            if data: #data available
                text1 += '\n<span size="small">Volume: ' + data['volume'] + '</span>'
                text2 += '<span size="medium"><b>' + data['price'] \
                   + '</b></span>\n<span size="small">' + data['change'] \
                   + '</span>\n<span size="small">' + str(data['percent']) \
                   + '%</span>'
                self.header_icon.set_from_file(helper.get_arrow_type(float(data['percent'])))
                self.header_icon.show()
            self.header_name.set_markup(text1)
            self.header_performance.set_markup(text2)
        else:
            self.header_icon.hide()
        #save data to item which is returned
        if data:
            for k, v in data.iteritems():
                self.item[k] = v
        for k, v in item.iteritems():
            self.item[k] = v

    def save_data_to_db(self):
        """This function is used to read the data from the dialog
        and then store it in the watchlist.quote object.
        """
        #get data from widget
        self.item['stock_id']          = self.stock_id
        self.item['comment']           = self.get_comment()
        self.item['quantity']          = 1
        self.item['transaction_costs'] = 0.0
        self.item['type']              = config.WATCHLISTITEM
        self.item['buyprice']          = float(self.item['price'])
        self.item['buysum']            = float(self.item['price'])
        import datetime
        self.item['buydate']           = datetime.date.today()
        self.item['transaction_type']  = config.TRANSACTION_BUY
        #insert into positions table
        self.item['id'] = db.add_position(self.item)

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
    """
    def __init__(self, glade_file):
        """
        @param glade_file: the glade file for this dialog.
        @type glade_file: text
        """
        self.glade_file = glade_file
        #Get the widget tree
        self.wTree = gtk.glade.XML(self.glade_file, "portfolioDialog")
        #Connect with yourself
        self.wTree.signal_autoconnect(self)
        self.dialog = self.wTree.get_widget("portfolioDialog")
        #get the widgets from the dlg
        self.enterName = self.wTree.get_widget("enterPortfolioName")
        self.enterCash = self.wTree.get_widget("enterPortfolioCash")
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
        self.item['cash'] = self.enterCash.get_text()
        self.item['id'] = db.add_portfolio(self.item)


class SellDialog(Dialog):
    """
    dialog to sell a portfolio position
    """
    def __init__(self,glade_file, position_id):
        """
        Initialize the sell dialog
        @param glade_file - string - the glade file for this dialog.
        @param position_id: position to sell
        @type position_id: integer
        """
        self.glade_file = glade_file
        #Get the widget tree
        self.wTree = gtk.glade.XML(self.glade_file, "sellDialog")
        #Connect with yourself
        self.wTree.signal_autoconnect(self)
        self.dialog = self.wTree.get_widget("sellDialog")
        #get the widgets from the dialog
        self.enterComment = self.wTree.get_widget("enterSellComment")
        self.numShares = self.wTree.get_widget("enterSellNumShares")
        self.enterBuyPrice = self.wTree.get_widget("enterSellPrice")
        self.buyDate = self.wTree.get_widget("sellDate")
        self.header_name = self.wTree.get_widget("sell_position_name")
        self.header_performance = self.wTree.get_widget("sell_position_performance")
        self.header_icon = self.wTree.get_widget("sell_postion_icon")
        self.transactioncosts = self.wTree.get_widget("sellTransactionCosts")
        self.item = {}
        self.item['position_id'] = position_id
    
    def save_data_to_db(self):
        """
        This function is used to read the data from the dialog
        and then store it in the db.
        """
        pass

class RemovePortfolio(Dialog):
    def __init__(self, portfolio_id):
        self.portfolio_id = portfolio_id
        info = db.get_portfolio_name(portfolio_id)
        text1 = 'Do you wish to permanently delete the following portfolio and all contained positions?'
        text2 = info['name']+' - '+info['comment']
        self.dialog = gtk.MessageDialog(main_application_window,
                                  gtk.DIALOG_DESTROY_WITH_PARENT,
                                  gtk.MESSAGE_QUESTION,
                                  gtk.BUTTONS_OK_CANCEL,
                                  text1
                                  )
        self.dialog.format_secondary_text(text2)
        
    def save_data_to_db(self):
        db.remove_portfolio(self.portfolio_id)


class BuyDialog(QuoteDialog):
    """
    stock buying dialog
    """
    def __init__(self, glade_file, portfolio_id):
        """Initialize the buy dialog.
        @param glade_file - string - the glade file for this dialog.
        @param portfolio_id
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
        """
        This function is used to read the data from the dialog
        and then store it in the db.
        """
        #get data from widgets
        self.item['stock_id']          = self.stock_id
        self.item['comment']           = self.get_comment()
        self.item['quantity']          = self.numShares.get_text()
        self.item['buyprice']          = self.enterBuyPrice.get_text()
        self.item['price']             = self.item['buyprice']
        self.item['buydate']           = str(helper.makeTimeFromGTK(self.buyDate.get_date()))
        self.item['datetime']          = self.item['buydate']
        self.item['transaction_costs'] = self.transactioncosts.get_text()
        self.item['type']              = config.PORTFOLIOITEM
        self.item['transaction_type']  = config.TRANSACTION_BUY
        self.item['buysum']            = (float(self.item['buyprice'])
                                        * float(self.item['quantity'])
                                        + float(self.item['transaction_costs']))
        #insert into positions table
        self.item['id']                = db.add_position(self.item)
        self.item['position_id']       = self.item['id']
        #insert transaction into db
        db.add_transaction(self.item)
        #update cash of portfolio
        db.update_cash(self.item['portfolio_id'], self.item['buysum'])


