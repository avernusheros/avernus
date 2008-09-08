try:
    import sys
    import gtk
    import gtk.glade
    import items
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
    @param quote - watchlist.quote - None to create a new 
                   watchlist.quote object, or the object that you wish to edit.
    """
    def __init__(self, glade_file, watchlist = None):
        self.glade_file = glade_file
        self.watchlist = watchlist
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
        if (self.watchlist):
            #Name
            self.enterName.set_text(self.watchlist.name)
            #Comment
            self.set_description(self.watchlist.description)
    
    def save_data_to_object(self):
        """This function is used to read the data from the dialog
        and then store it in the watchlist.quote object.
        """
        if (self.watchlist == None):
            self.watchlist = items.Watchlist(self.enterName.get_text(), self.get_description())
        else:
            self.watchlist.name = self.enterName.get_text()
            self.watchlist.description = self.get_description()
        
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

    def __init__(self, glade_file, quote = None):
        """Initialize the quote dialog.
        @param glade_file - string - the glade file for this dialog.
        @param quote - watchlist.quote - None to create a new 
                       watchlist.quote object, or the object that you wish to edit.
        """
        self.glade_file = glade_file
        self.quote = quote
        #Get the widget tree
        self.wTree = gtk.glade.XML(self.glade_file, "quoteDialog")
        #Connect with yourself
        self.wTree.signal_autoconnect(self)
        self.dialog = self.wTree.get_widget("quoteDialog")
        #get the widgets from the dlg
        self.enterName = self.wTree.get_widget("enterQuoteName")
        self.enterSymbol = self.wTree.get_widget("enterSymbol")
        self.enterComment = self.wTree.get_widget("enterComment")
        #update dialog
        self.update_dialog_from_object()
        
    def update_dialog_from_object(self):
        """Used to update the settings on the dialog"""
        if (self.quote):
            #Name
            self.enterName.set_text(self.quote.name)
            #Symbol
            self.enterSymbol.set_text(self.quote.symbol)
            #Comment
            self.set_comment(self.quote.comment)

    def save_data_to_object(self):
        """This function is used to read the data from the dialog
        and then store it in the watchlist.quote object.
        """
        if (self.quote == None):
            self.quote = items.Quote(self.enterSymbol.get_text(), self.enterName.get_text(), self.get_comment())
        else:
            self.quote.name = self.enterName.get_text()
            self.quote.symbol = self.enterSymbol.get_text()
            self.quote.comment = self.get_comment()
        self.quote.update()

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
        
