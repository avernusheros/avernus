_ = lambda x : x

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass
try:
    import sys
    import gtk
    import gtk.glade
    import gobject
    import logging
    import os
    import locale
    import gettext
    import pango
    from stocktracker import helper, config
    from stocktracker.ui import dialogs, treeviews
    from stocktracker.database import database

except ImportError, e:
    print "Import error in stocktracker_gui.py, cannot start:", e
    sys.exit(1)


'''A simple python based portfolio manager'''
class StockTracker(object):
    logger = logging.getLogger('stocktracker')
    
    def __init__(self):
        #Get the local path
        self.local_path = os.path.realpath(os.path.dirname(sys.argv[0]))
        #Set the Glade file
        self.gladefile = os.path.join("share/glade/stocktracker.glade")
        #Get the Main Widget Tree
        self.mainWindow = gtk.glade.XML(self.gladefile, "mainWindow")
        #Connect with main window
        self.mainWindow.signal_autoconnect(self)
        #Initialize trees
        self.wl_performance_tree = treeviews.PerformanceTreeWatchlist(self.mainWindow.get_widget('performanceTree'))
        self.po_performance_tree = treeviews.PerformanceTreePortfolio(self.mainWindow.get_widget('portfolioPerformanceTree'))
        self.left_tree = treeviews.LeftTree(self.mainWindow.get_widget('leftTree'))
        self.fundamentals_tree = treeviews.FundamentalsTree(self.mainWindow.get_widget('fundamentalsTree'))
        self.transactions_tree = treeviews.TransactionsTree(self.mainWindow.get_widget('transactionsTree'))

        #init widgets
        self.initialize_widgets()

        #self.watchlists = items.Category('Watchlists', self.left_tree)
        #self.portfolios = items.Category('Portfolios', self.left_tree)

        self.currentList = None

        #current selected item
        self.selected_item = None

        #init database
        self.initialize_db()
        #reload
        self.reload_from_data()


    #************************************************************
    #* Initialize
    #************************************************************

    def initialize_widgets(self):
        """Initialize any widgets that we want.  Basically
        grab widgets that you want to have access to later on in the program.
        """
        self.logger.debug('Initialize widgets')
        #Get the Main Window
        self.main_window = self.mainWindow.get_widget("mainWindow")
        #self.set_window_title_from_file(self.file.filename)
        #Get the button widgets
        self.editButton = self.mainWindow.get_widget("editButton")
        self.removeButton = self.mainWindow.get_widget("removeButton")
        self.addButton = self.mainWindow.get_widget("addButton")
        self.updateButton = self.mainWindow.get_widget("updateButton")
        self.header = self.mainWindow.get_widget("header")
        #get watchlist tabs
        self.watchlist_tabs = []
        self.watchlist_tabs.append(self.mainWindow.get_widget("tab_fundamentals"))
        self.watchlist_tabs.append(self.mainWindow.get_widget("tab_performance"))
        self.hide_watchlist()
        #get portfolio tabs
        self.portfolio_tabs = []
        self.portfolio_tabs.append(self.mainWindow.get_widget("tab_fundamentals"))
        self.portfolio_tabs.append(self.mainWindow.get_widget("tab_portfolio_performance"))
        self.portfolio_tabs.append(self.mainWindow.get_widget("tab_transactions"))
        self.hide_portfolio()

    def initialize_db(self):
        self.db = database.get_db()
        self.db.connect()

    #********************************************************
    #* Simple Helpers
    #********************************************************

    def set_window_title_from_file(self, file):
        """Set the windows title, take it from file.
        @param file - string - The file name that we will
        base the window title off of
        """
        if (file):
            self.main_window.set_title("StockTracker - %s"
                % (os.path.basename(file)))
        else:
            self.main_window.set_title(_("StockTracker - Untitled"))

    def show_watchlist(self, id):
        self.currentList = id
        self.reload_watchlist(id)
        self.addButton.set_sensitive(True)
        self.updateButton.set_sensitive(True)
        self.removeButton.set_sensitive(True)
        self.editButton.set_sensitive(True)
        #self.reload_header()
        #self.header.show()
        for tab in self.watchlist_tabs:
            tab.show()

    def hide_watchlist(self):
        for tab in self.watchlist_tabs:
            tab.hide()

    def show_portfolio(self, id):
        self.currentList = id
        self.reload_portfolio(id)
        self.addButton.set_sensitive(True)
        self.updateButton.set_sensitive(True)
        self.removeButton.set_sensitive(True)
        self.editButton.set_sensitive(True)
        for tab in self.portfolio_tabs:
            tab.show()

    def hide_portfolio(self):
        for tab in self.portfolio_tabs:
            tab.hide()

    def edit_object(self, object, model, object_iter):
        """Helper function used to edit an object in the tree.
        @param object - itemBase- The object that we are editing.
        @param model - gtk.TreeModel - The model for the tree.
        @param object_iter - gtk.TreeIter representing the object's position in the tree.
        """
        #Just make sure that they are all correct
        if (object and model and object_iter):
            if (object.type == items.WATCHLIST):
                #Edit watchlist
                dialog = dialogs.WatchlistDialog(self.gladefile, object)
                if (dialog.run() == gtk.RESPONSE_OK):
                    object.set_tree_values(model
                        , object_iter
                        , self.left_tree.tree_columns)
            if (object.type == items.PORTFOLIO):
                #Edit portfolio
                dialog = dialogs.PortfolioDialog(self.gladefile, object)
                if (dialog.run() == gtk.RESPONSE_OK):
                    object.set_tree_values(model
                        , object_iter
                        , self.left_tree.tree_columns)
            if (object.type == items.WATCHLISTITEM):
                #Edit watchlist item
                dialog = dialogs.QuoteDialog(self.gladefile, object)
                if (dialog.run() == gtk.RESPONSE_OK):
                    object.set_tree_values(model
                        , object_iter
                        , self.performance_tree.tree_columns)
            if (object.type == items.PORTFOLIOITEM):
                #Edit portfolio item
                dialog = dialogs.BuyDialog(self.gladefile, object)
                if (dialog.run() == gtk.RESPONSE_OK):
                    object.set_tree_values(model
                        , object_iter
                        , self.portfolio_performance_tree.tree_columns)

    def reload_watchlist(self, id):
        items = self.db.get_portfolio_positions(id)
        self.fundamentals_tree.clear()
        self.wl_performance_tree.clear()
        for item in items:
            self.fundamentals_tree.insert(item)
            self.wl_performance_tree.insert(item)
        #reload and show the header
        self.reload_header()
        self.header.show()

    def reload_portfolio(self, id):
        """ reload a portfolio
        @params id - integer - portfolio id
        """
        items = self.db.get_portfolio_positions(id)
        #print items
        self.fundamentals_tree.clear()
        self.po_performance_tree.clear()
        self.transactions_tree.clear()
        for item in items:
            self.fundamentals_tree.insert(item)
            self.po_performance_tree.insert(item)
        transactions = self.db.get_transactions(id)
        for trans in transactions:
            self.transactions_tree.insert(trans)
        #reload and show the header
        self.reload_header()
        self.header.show()

    def reload_header(self):
        #get performance information from current list
        data = self.db.get_portfolio_info(self.currentList)
        #get widgets
        name            = self.mainWindow.get_widget("header_name")
        info            = self.mainWindow.get_widget("header_info")
        performance     = self.mainWindow.get_widget("header_performance")
        overall         = self.mainWindow.get_widget("header_overall")
        performance_img = self.mainWindow.get_widget("header_performance_img")
        overall_img     = self.mainWindow.get_widget("header_overall_img")
        #setting labels
        name.set_label('<span size="medium"><b>' + data['name']+ '</b></span>\n')
        if data['count']>0:
            info.set_label('# '+str(data['count'])+'\nValue: '+str(data['value'])
                        +'\nCash: '+str(data['cash'])+'\nOverall: '
                        +str(data['value']+data['cash']))
            performance.set_label('Today\n$ '+str(data['change'])+'\n% '
                                +str(data['percent']))
            overall.set_label('Overall\n$ '+str(data['overall_change'])+'\n% '
                                +str(data['overall_percent']))
            #setting icons
            performance_img.set_from_file(helper.get_arrow_type(data['change'], True))
            overall_img.set_from_file(helper.get_arrow_type(data['overall_change'], True))

    def add_watchlistitem(self, watchlist_id):
        dialog = dialogs.QuoteDialog(self.gladefile, watchlist_id)
        if (dialog.run() == gtk.RESPONSE_OK):
            self.wl_performance_tree.insert(dialog.item)
            self.fundamentals_tree.insert(dialog.item)
            #self.reload_header()

    def buy_position(self, portfolio_id):
        dialog = dialogs.BuyDialog(self.gladefile, portfolio_id)
        if (dialog.run() == gtk.RESPONSE_OK):
            pass
                #dialog.position.update()
                #Append to the tree
                #dialog.position.add_to_tree(self.portfolio_performance_tree, self.fundamentals_tree, self.transactions_tree)
                #Add to the portfolio
                #portfolio.add_child(dialog.position)
        #self.reload_header()

    def add_watchlist(self):
        dialog = dialogs.WatchlistDialog(self.gladefile)
        if (dialog.run() == gtk.RESPONSE_OK):
                #Append to the tree
                self.left_tree.insert_after(None, dialog.item)

    def add_portfolio(self):
        dialog = dialogs.PortfolioDialog(self.gladefile)
        if (dialog.run() == gtk.RESPONSE_OK):
                #Append to the tree
                self.left_tree.insert_after(None, dialog.item)

    def reload_from_data(self):
        """Called when we want to reset everything based
        on internal data.  Probably called when a file has been loaded."""
        #self.performance_tree.treestore.clear()
        #self.left_tree.treestore.clear()
        #self.fundamentals_tree.treestore.clear()
        #self.transactions_tree.treestore.clear()
        #self.portfolio_performance_tree.treestore.clear()
        #self.watchlists.add_to_tree(self.left_tree)
        #self.portfolios.add_to_tree(self.left_tree)
        items = self.db.get_portfolios()
        for item in items:
            self.left_tree.insert_after(None, item)


    #************************************************************
    #* Signal Handlers
    #************************************************************

    def on_mainWindow_destroy(self, widget):
        """Called when the application is going to quit"""
        gtk.main_quit()

    def on_about(self, widget):
        #load the dialog from the glade file
        mainWindow = gtk.glade.XML(self.gladefile, "aboutDialog")
        #Get the actual dialog widget
        dlg = mainWindow.get_widget("aboutDialog")
        dlg.run()

    def on_add_button(self, widget):
        if self.selected_item:
            type, id, model, selection_iter = self.selected_item
            if type == config.CATEGORY_W:
                self.add_watchlist()
            elif type == config.CATEGORY_P:
                self.add_portfolio()
            elif type == config.WATCHLIST:
                self.add_watchlistitem(id)
            elif type == config.PORTFOLIO:
                self.buy_position(id)
            elif type == config.PORTFOLIOITEM:
                self.buy_position(self.currentList)
            elif type == config.WATCHLISTITEM:
                 self.add_watchlistitem(self.currentList)
        else:
            print "nothing selected"

    def on_treeview_cursor_changed(self, widget):
        self.selected_item = None
        #Get the current selection in the gtk.TreeView
        selection = widget.get_selection()
        # Get the selection iter
        model, selection_iter = selection.get_selected()
        if (selection_iter and model):
            #Something is selected so get the object
            type = model.get_value(selection_iter, 0)
            id = model.get_value(selection_iter, 1)
            self.selected_item = [type, id, model, selection_iter]

    def on_leftTree_cursor_changed(self, widget):
        self.on_treeview_cursor_changed(widget)
        #self.performance_tree.treestore.clear()
        #self.fundamentals_tree.treestore.clear()
        #self.transactions_tree.treestore.clear()
        #self.portfolio_performance_tree.treestore.clear()
        if not (self.selected_item == None):
            type, id, model, selection_iter = self.selected_item
            #category selected
            if type == config.CATEGORY_W or type == config.CATEGORY_P:
                self.currentList = None
                self.addButton.set_sensitive(True)
                self.updateButton.set_sensitive(True)
                self.removeButton.set_sensitive(False)
                self.editButton.set_sensitive(False)
                self.header.hide()
                self.hide_portfolio()
                self.hide_watchlist()
            elif type == config.WATCHLIST:
                self.hide_portfolio()
                self.show_watchlist(id)
            elif type == config.PORTFOLIO:
                self.hide_watchlist()
                self.show_portfolio(id)
            else :
                self.currentList = None
                self.addButton.set_sensitive(False)
                self.updateButton.set_sensitive(False)
                self.removeButton.set_sensitive(False)
                self.editButton.set_sensitive(False)
                self.header.hide()
                self.hide_portfolio()
                self.hide_watchlist()

    def on_tree_button_press_event(self, widget, event):
        """There has been a button press on a Tree
        for now we use this as a quick hack to remove
        the selection.  Perhaps there is a better way?
        @param widget - gtk.TreeView - The Tree View
        @param event - gtk.gdk.event - Event information
        """
        #Get the path at the specific mouse position
        path = widget.get_path_at_pos(int(event.x), int(event.y))
        if (path == None):
            """If we didn't get apath then we don't want anything to be selected."""
            selection = widget.get_selection()
            selection.unselect_all()

    def on_remove_item(self, widget):
        """called then the remove button is clicked.
        Can also be generally used to remove a items."""
        if self.selected_item:
            type, id, model, selection_iter = self.selected_item
            if type == config.WATCHLIST or type == config.PORTFOLIO:
                self.db.remove_portfolio(id)
                self.left_tree.remove(selection_iter)
            elif type == config.WATCHLISTITEM:
                self.db.remove_position(id)
                self.fundamentals_tree.remove_id(id)
                self.wl_performance_tree.remove_id(id)
            elif type == config.PORTFOLIOITEM:
                self.db.remove_position(id)
                self.fundamentals_tree.remove_id(id)
                self.pf_performance_tree.remove_id(id)
                self.transactions_tree.remove_id(id)
                #self.reload_header()

    def on_edit_object(self, widget):
        """Called when we want to edit the selected item"""
        # Get the selected object
        object, model, selection_iter  = self.selected_item
        if (selection_iter and model and object):
            """All right something and we have all the needed data"""
            self.edit_object(object, model, selection_iter)

    def on_row_activated(self, tree_view, path, tree_column):
        """This is called when a row is "activated" in the tree
        view.  It happens when the user double clicks on an item
        in the tree.  We will use it to edit the items.
        @param tree_view gtk.TreeView - The Tree
        @param path - string - The path string
        @param tree_column - gtk.TreeViewColumn - The column that was clicked on.
        """
        #Get the column of the object
        wcolumn, pos = self.performance_tree.find_Column(treeviews.COL_OBJECT)
        model = tree_view.get_model()
        if ((wcolumn) and (model)):
            #Now get the selection iter from the path
            selection_iter = model.get_iter(path)
            if (selection_iter):
                #Now that we have the selection let's get the object
                object = model.get_value(selection_iter, wcolumn.pos)
                #Now lets edit the object
                self.edit_object(object, model, selection_iter)

    def on_leftTree_row_activated(self, tree_view, path, tree_column):
        """This is called when a row is "activated" in the tree
        view.  It happens when the user double clicks on an item
        in the tree.  We will use it to edit the items.
        @param tree_view gtk.TreeView - The Tree
        @param path - string - The path string
        @param tree_column - gtk.TreeViewColumn - The column that was clicked on.
        """
        #Get the column of the object
        wcolumn, pos = self.left_tree.find_Column(treeviews.COL_OBJECT)
        model = tree_view.get_model()
        if (wcolumn and model):
            #Now get the selection iter from the path
            selection_iter = model.get_iter(path)
            if (selection_iter):
                #Now that we have the selection let's get the object
                item = model.get_value(selection_iter, wcolumn.pos)
                #Now lets edit the object
                self.edit_object(item, model, selection_iter)

    def on_update(self, widget):
        """called when update button is clicked"""
        self.watchlists.update()
        self.portfolios.update()
        self.reload_from_data()


