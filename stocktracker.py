__author__ = "Wolfgang Steitz <wsteitz@gmail.com>"
__version__ = "0.1"
__date__ = "Date: 2008/09/08"
__copyright__ = "Copyright (c) 2008 Wolfgang Steitz"
__license__ = "GPL v3"


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
    import os
    import locale
    import gettext
    import config
    import file
    import items
    import helper
    import pango
    import dialogs
    import treeviews
    from data import *


except ImportError, e:
    print "Import error stocktracker cannot start:", e
    sys.exit(1)




'''A simple python based portfolio manager'''
class StockTracker(object):

    def __init__(self):
        #Get the local path
        self.local_path = os.path.realpath(os.path.dirname(sys.argv[0]))
        #Translation stuff
        #self.initialize_translation()
        #Set the Glade file
        self.gladefile = os.path.join(self.local_path, "glade/stocktracker.glade")
        #Get the Main Widget Tree
        self.mainWindow = gtk.glade.XML(self.gladefile, "mainWindow")
        #Connect with main window
        self.mainWindow.signal_autoconnect(self)
        #Initialize trees
        self.performance_tree           = treeviews.PerformanceTree(self.mainWindow.get_widget('performanceTree'))
        self.fundamentals_tree          = treeviews.FundamentalsTree(self.mainWindow.get_widget('fundamentalsTree'))
        self.portfolio_performance_tree = treeviews.PortfolioPerformanceTree(self.mainWindow.get_widget('portfolioPerformanceTree'))
        self.left_tree                  = treeviews.LeftTree(self.mainWindow.get_widget('leftTree'))
        self.transactions_tree          = treeviews.TransactionsTree(self.mainWindow.get_widget('transactionsTree'))
        #init file
        self.file = file.File()        
        #init widgets
        self.initialize_widgets()

        self.watchlists = items.Category('Watchlists', self.left_tree)
        self.portfolios = items.Category('Portfolios', self.left_tree)
        self.currentList = None
        
        #current selected item
        self.selected_item = None
        
        #init database
        self.initialize_db()


    #************************************************************
    #* Initialize
    #************************************************************

    def initialize_widgets(self):
        """Initialize any widgets that we want.  Basically
        grab widgets that you want to have access to later on in the program.
        """
        #Get the Main Window
        self.main_window = self.mainWindow.get_widget("mainWindow")
        self.set_window_title_from_file(self.file.filename)
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
        #path = os.path.expanduser("~")
        #path = os.path.join(path, '.stocktracker/')
        #if not os.path.exists(path):
        #        os.mkdir(path)
        #path = os.path.join(path, 'data.db')
        #if not os.path.exists(path):
        #    self.db_conn = sqlite3.connect(path)
        #    # Create tables
        #    self.db_conn.execute('''create table stocks (id text, name text, exchange text)''')
        #    self.db_conn.execute('''create table transactions (id text
        #    , type integer, datetime timestamp, quantity integer, price real, charge real)''')
        #    #commit
        #    self.db_conn.commit()
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
        
    def show_watchlist(self, item):
        self.reload_watchlist(item)
        self.currentList = item
        self.addButton.set_sensitive(True)
        self.updateButton.set_sensitive(True)
        self.removeButton.set_sensitive(True)
        self.editButton.set_sensitive(True)
        self.reload_header()
        self.header.show()
        for tab in self.watchlist_tabs:
            tab.show()
        
    def hide_watchlist(self):
        for tab in self.watchlist_tabs:
            tab.hide()
            
    def show_portfolio(self, item):
        self.reload_portfolio(item)  
        self.currentList = item
        self.addButton.set_sensitive(True)
        self.updateButton.set_sensitive(True)
        self.removeButton.set_sensitive(True)
        self.editButton.set_sensitive(True)
        self.reload_header()
        self.header.show()
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
                        
    def reload_watchlist(self, watchlist):
        watchlist.show(self.performance_tree, self.fundamentals_tree)

    def reload_portfolio(self, portfolio):
        portfolio.show(self.portfolio_performance_tree
                     , self.fundamentals_tree
                     , self.transactions_tree)

    def reload_header(self):
        name            = self.mainWindow.get_widget("header_name")
        performance     = self.mainWindow.get_widget("header_performance")
        overall         = self.mainWindow.get_widget("header_overall")
        performance_img = self.mainWindow.get_widget("header_performance_img")
        overall_img     = self.mainWindow.get_widget("header_overall_img")
        name.set_label('<span size="medium"><b>' + self.currentList.name+ ' </b></span>\n')
        #get performance information from current list
        perf = self.currentList.get_performance()
        oall = self.currentList.get_overall_performance()
        #setting labels
        performance.set_label(perf[0])
        overall.set_label(oall[0])
        #setting icons
        performance_img.set_from_file(perf[1])
        overall_img .set_from_file(oall[1])

    def add_quote(self, watchlist):
        dialog = dialogs.QuoteDialog(self.gladefile)
        if (dialog.run() == gtk.RESPONSE_OK):
                dialog.stock.update()
                #Append to the tree
                dialog.stock.add_to_tree(self.performance_tree, self.fundamentals_tree)
                #Add to the Watchlist
                watchlist.add_child(dialog.stock)
        self.reload_header()
    
    def buy_position(self, portfolio):
        dialog = dialogs.BuyDialog(self.gladefile)
        if (dialog.run() == gtk.RESPONSE_OK):
                dialog.position.update()
                #Append to the tree
                dialog.position.add_to_tree(self.portfolio_performance_tree, self.fundamentals_tree, self.transactions_tree)
                #Add to the portfolio
                portfolio.add_child(dialog.position)
        self.reload_header()
    
    def add_watchlist(self, selection_iter):
        dialog = dialogs.WatchlistDialog(self.gladefile)
        if (dialog.run() == gtk.RESPONSE_OK):
                #Append to the tree
                dialog.item.add_to_tree(self.left_tree.treestore
                    , selection_iter
                    , self.left_tree.tree_columns)
                self.watchlists.add_child(dialog.item)
                
    def add_portfolio(self, selection_iter):
        dialog = dialogs.PortfolioDialog(self.gladefile)
        if (dialog.run() == gtk.RESPONSE_OK):
                #Append to the tree
                dialog.item.add_to_tree(self.left_tree.treestore
                    , selection_iter
                    , self.left_tree.tree_columns)
                self.portfolios.add_child(dialog.item)
                
    def reload_from_data(self):
        """Called when we want to reset everything based
        on internal data.  Probably called when a file has been loaded."""
        self.performance_tree.treestore.clear()
        self.left_tree.treestore.clear()
        self.fundamentals_tree.treestore.clear()
        self.transactions_tree.treestore.clear()
        self.portfolio_performance_tree.treestore.clear()
        self.watchlists.add_to_tree(self.left_tree)
        self.portfolios.add_to_tree(self.left_tree)


    #************************************************************
    #* Signal Handlers
    #************************************************************

    def on_mainWindow_destroy(self, widget):
        """Called when the application is going to quit"""
        gtk.main_quit()
        
    def on_add_quote(self, widget):
        pass
    
    def on_add_watchlist(self, widget):
        pass
        
    def on_about(self, widget):
        #load the dialog from the glade file
        mainWindow = gtk.glade.XML(self.gladefile, "aboutDialog")
        #Get the actual dialog widget
        dlg = mainWindow.get_widget("aboutDialog")
        dlg.run()

    def on_add_button(self, widget):
        item, model, selection_iter = self.selected_item
        if item:
            if (item.type == items.CATEGORY):
                if (item.name == "Watchlists"):
                    self.add_watchlist(selection_iter)
                elif (item.name == "Portfolios"):
                    self.add_portfolio(selection_iter)
            elif (item.type == items.WATCHLIST):
                self.add_quote(item)
            elif (item.type == items.PORTFOLIO):
                self.buy_position(item)
            elif (item.type == items.PORTFOLIOITEM or item.type == items.WATCHLISTITEM):
                self.add_quote(self.currentList)
    
    def on_treeview_cursor_changed(self, widget):
        self.selected_item = None
        #Get the current selection in the gtk.TreeView
        selection = widget.get_selection()
        # Get the selection iter
        model, selection_iter = selection.get_selected()
        if (selection_iter and model):
            #Something is selected so get the object
            item = model.get_value(selection_iter, 0)
        self.selected_item = [item, model, selection_iter]
    
    def on_leftTree_cursor_changed(self, widget):
        self.on_treeview_cursor_changed(widget)
        model, selection_iter, item = self.left_tree.get_selected_object()
        self.performance_tree.treestore.clear()
        self.fundamentals_tree.treestore.clear()
        self.transactions_tree.treestore.clear()
        self.portfolio_performance_tree.treestore.clear()
        if not (item == None):
            #category selected
            if (item.type == items.CATEGORY):
                self.currentList = None
                self.addButton.set_sensitive(True)
                self.updateButton.set_sensitive(True)
                self.removeButton.set_sensitive(False)
                self.editButton.set_sensitive(False)
                self.header.hide()
                self.hide_portfolio()
                self.hide_watchlist()
            elif (item.type == items.WATCHLIST):
                self.hide_portfolio()
                self.show_watchlist(item)
            elif (item.type == items.PORTFOLIO):
                self.hide_watchlist()
                self.show_portfolio(item)
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
        item , model, selection_iter = self.selected_item
        if item:
            if (item.type == items.CATEGORY):
                #categories should not be removed
                pass
            elif item.type == items.WATCHLIST:
                self.watchlists.remove_child(item)
            elif item.type == items.PORTFOLIO:
                self.portfolios.remove_child(item)
            elif (item.type == items.WATCHLISTITEM or item.type == items.PORTFOLIOITEM):
                self.currentList.remove_child(item)
                self.reload_header()
            model.remove(selection_iter)
                    
    def on_file_new(self, widget):
        """File | New - Start a new project file, blank out
        the currnet project and start from scratch"""
        self.watchlists.clear()
        self.portfolios.clear()
        self.file.filename = None
        self.set_window_title_from_file(self.file.filename)
        self.reload_from_data()

    def on_file_open(self, widget):
        """Function called to open a file"""
        self.file.filename = helper.file_browse(gtk.FILE_CHOOSER_ACTION_OPEN
            , self.file.get_browse_filter_list()
            , file.FILE_EXT)
        data = self.file.load_from_file()
        if data:
            self.watchlists = data[0]
            self.portfolios = data[1]
            self.set_window_title_from_file(self.file.filename)
            self.reload_from_data()

    def on_file_save(self, widget):
        """Save the file"""
        data = [self.watchlists, self.portfolios]
        # Let the user browse for the save location and name
        if (self.file.filename == None):
            self.file.filename = helper.file_browse(gtk.FILE_CHOOSER_ACTION_SAVE
            , self.file.get_browse_filter_list()
            , file.FILE_EXT)
        #If we have a file
        if (self.file.filename):
            if (self.file.save_to_file(data)):
                #Allright it all worked! Set the Title
                self.set_window_title_from_file(self.file.filename)

    def on_file_save_as(self, widget):
        """ Save As function"""
        data = [self.watchlists, self.portfolios]
        f = _("Untitled")
        if (self.file.filename != None):
            f = os.path.basename(self.file.filename)
        f = helper.file_browse(gtk.FILE_CHOOSER_ACTION_SAVE
            , self.file.get_browse_filter_list()
            , file.FILE_EXT)
        #If we have a xml_file
        if (f):
            self.file.filename = file
            if (self.file.save_to_file(data)):
                #set title
                self.set_window_title_from_file(self.file.filename)
        
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
        

if __name__ == '__main__':
    StockTracker()
    gtk.main()

