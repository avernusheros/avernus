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
    import cPickle
    import items
    import pango


except ImportError, e:
    print "Import error stocktracker cannot start:", e
    sys.exit(1)



"""Column IDs"""
#watchlist performance tree
COL_OBJECT        = 0
COL_OBJECT_TYPE   = 1
COL_NAME          = 2
COL_CURRENTPRICE  = 3
COL_CURRENTCHANGE = 4
COL_CURRENTICON   = 5
COL_PRICE         = 6
COL_CHANGE        = 7
COL_ICON          = 8
COL_COMMENT       = 9

#portfolio performance tree
COL_QUANTITY      = 2
COL_PF_NAME       = 3
COL_BUYPRICE      = 4
COL_BUYSUM        = 5
COL_LASTTRADE     = 6
COL_PF_CHANGE     = 7
COL_PF_ICON       = 8
COL_PF_OVERALL    = 9
COL_PF_OALL_ICON  = 10
COL_PF_COMMENT    = 11

#left tree
COL_FOLDER        = 2
COL_TODAY         = 3
COL_OVERALL       = 4

#fundamentals tree
COL_MKTCAP        = 3
COL_AVG_VOL       = 4
COL_52WEEK_HIGH   = 5
COL_52WEEK_LOW    = 6
COL_EPS           = 7
COL_PE            = 8



        

class Column(object):
    """This is a class that represents a column in the tree.
    It is simply a helper class that makes it easier to inialize thet tree."""
    
    def __init__(self, ID, type, name, pos, visible=False, cellrenderer = None
                , markup = False,  share_column = False, multiline = False
                , wrap_width = 20, icon = False):
        """
        @param ID - int - The Columns ID
        @param type - int  - A gobject.TYPE_ for the gtk.TreeStore
        @param name - string - The name of the column
        @param pos - int - The index of the column.
        @param visible - boolean - Is the column visible or not?
        @param cellrenderer - gtk.CellRenderer - a constructor function for the column
        @param markup - boolean - should we use markup or not?
        @param share_column - boolean - Should this column be packed
        in with the previous column?  i.e. two data types in one gtk.TreeViewColumn?
        """
        self.ID = ID
        self.type = type
        self.name = name
        self.pos = pos
        self.visible = visible
        self.cellrenderer = cellrenderer
        self.color = 0
        self.markup = markup
        self.share_column = share_column
        self.icon = icon
        if multiline:
            #make the current column multiline
            self.cellrenderer.props.wrap_mode = pango.WRAP_WORD
            self.cellrenderer.props.wrap_width = wrap_width

    def create_column(self, column = None, widget = None):
        """Create the column in the tree.
        @param column - gtk.TreeViewColumn - If this is none the
        column will be created, if it is not none, then the cell renderer will be appended.
        @returns gtk.TreeViewColumn - The column that was created or passsed in.
        """
        if (column == None):
            if (self.visible):
                #first if never used
                if (self.icon):
                    column = gtk.TreeViewColumn(self.name
                            , self.cellrenderer
                            , pixbuf = self.pos)
                if (not self.markup):
                    column = gtk.TreeViewColumn(self.name
                            , self.cellrenderer
                            , text = self.pos)
                else:
                    column = gtk.TreeViewColumn(self.name
                            , self.cellrenderer
                            , markup = self.pos)
        else:
            #We are packing two cells together
            #Create the cell rendered
            cell = self.cellrenderer
            #pack it
            column.pack_start(cell, True)
            #Set the attribute
            if (self.icon):
                column.add_attribute(cell, "pixbuf", self.pos)
            if (not self.markup):
                column.add_attribute(cell, "text", self.pos)
            else:
                column.add_attribute(cell, "markup", self.pos)
        #set custom widget as header
        if not widget == None:
            column.set_widget(widget)
            widget.show()
        return column
        

class Treeview(object):
    def __init__(self, treeview):
        #For easy access later on
        self.column_dict = {}
        #Get the treeView from the widget Tree
        self.tree = treeview
        #Enable the selection callback
        selection = self.tree.get_selection()
        #selection.connect('changed', self.on_tree_selection_changed)
        #Make it so that the colours of each row can alternate
        self.tree.set_rules_hint(True)
        self.init_colums()
        #Attache the model to the treeView
        self.tree.set_model(self.treestore)
        
    def init_colums(self):
        tree_type_list = [] #For creating the TreeStore
        #Save the previous column
        previous_column = None
        # Loop through the columns and initialize the Tree
        for item_column in self.tree_columns:
            #Add the column to the column dict
            self.column_dict[item_column.ID] = item_column
            #Save the type for gtk.TreeStore creation
            tree_type_list.append(item_column.type)
            #Do we need the previous column?
            if (not item_column.share_column):
                previous_column = None
            #is it visible?
            if (item_column.visible):
                #Create the Column
                column = item_column.create_column(previous_column, 
                        widget = self.get_custom_header_widget(item_column.ID))
                column.set_resizable(True)
                column.set_sort_column_id(item_column.pos)
                if (not previous_column):
                    self.tree.append_column(column)
                else:
                    column
                # Save the previous column
                previous_column = column
        #Create the gtk.TreeStore Model to use with the performanceTree
        self.treestore = gtk.TreeStore(*tree_type_list)
        
    def find_Column(self, column_ID):
        """This function is used to search the _columns
        list to find a specific Column.
        @param column_ID - The ID of the column that we are looking for.
        @returns watchlistColumn, int - The column found and
        the position in the list. If watchlistColumn is None then the column was not found.
        """
        count = 0
        columnReturn = None
        for item_column in self.tree_columns:
            if (item_column.ID == column_ID):
                columnReturn = item_column
                break
        if (columnReturn == None):
            #Something is really wrong we did not match
            helper.show_error_dlg(_("Error column data appears corrupted"))
        #Return the results
        return columnReturn, count 
        
    def get_selected_object(self):
        """Just a helper function that will give you the selected object
        @returns A 3-tuple containing a reference to the gtk.TreeModel and a gtk.TreeIter 
        pointing to the currently selected node. Just like
        gtk.TreeSelection.get_selected but with the watchlistItem
        being returned as well."""
        object = None
        wcolumn, pos = self.find_Column(COL_OBJECT)
        if (not wcolumn):
            return None,None,None
        #Get the current selection in the gtk.TreeView
        selection = self.tree.get_selection()
        # Get the selection iter
        model, selection_iter = selection.get_selected()
        if (selection_iter and model):
            #Something is selected so get the object
            object = model.get_value(selection_iter, wcolumn.pos)
        return model, selection_iter, object
        
    def find_Column(self, column_ID):
        """This function is used to search the __performanceTree_columns
        list to find a specific watchlistColumn.
        @param column_ID - The ID of the column that we are looking for.
        @returns watchlistColumn, int - The column found and
        the position in the list. If watchlistColumn is None then the column was not found.
        """
        count = 0
        columnReturn = None
        for item_column in self.tree_columns:
            if (item_column.ID == column_ID):
                columnReturn = item_column
                break
        if (columnReturn == None):
            #Something is really wrong we did not match
            helper.show_error_dlg(_("Error column data appears corrupted"))
        #Return the results
        return columnReturn, count 
        
    def get_custom_header_widget(self, ID):
        return None


class LeftTree(Treeview):
    def __init__(self, treeview):
        self.name = 'LeftTree'
        self.tree_columns = [
            Column(COL_OBJECT, gobject.TYPE_PYOBJECT, "object", COL_OBJECT)
            , Column(COL_OBJECT_TYPE, gobject.TYPE_INT, "object_type", COL_OBJECT_TYPE)
            , Column(COL_FOLDER, gobject.TYPE_STRING, _("Folder"), COL_FOLDER, True, gtk.CellRendererText(),True,True)
            , Column(COL_TODAY, gobject.TYPE_STRING, _("Today"), COL_TODAY, True, gtk.CellRendererText())
            , Column(COL_OVERALL, gobject.TYPE_STRING, _("Overall"), COL_OVERALL, True, gtk.CellRendererText())
            ]
        Treeview.__init__(self, treeview)
        
        
class PerformanceTree(Treeview):
    def __init__(self, treeview):
        self.name = 'PerformanceTree'
        self.tree_columns = [
            Column(COL_OBJECT, gobject.TYPE_PYOBJECT, "object", COL_OBJECT)
            , Column(COL_OBJECT_TYPE, gobject.TYPE_INT, "object_type", COL_OBJECT_TYPE)
            , Column(COL_NAME, gobject.TYPE_STRING, _("Name"), COL_NAME, True, gtk.CellRendererText(), markup=True)
            , Column(COL_CURRENTPRICE, gobject.TYPE_STRING, _("Price"), COL_CURRENTPRICE, True, gtk.CellRendererText(), markup=True)
            , Column(COL_CURRENTCHANGE, gobject.TYPE_STRING, _("Change"), COL_CURRENTCHANGE, True, gtk.CellRendererText(), markup=True)
            , Column(COL_CURRENTICON, gobject.TYPE_OBJECT, _("Change"), COL_CURRENTICON, True, gtk.CellRendererPixbuf(), share_column=True, icon =True)
            , Column(COL_PRICE, gobject.TYPE_STRING, _("Price"), COL_PRICE, True, gtk.CellRendererText(), markup=True)
            , Column(COL_CHANGE, gobject.TYPE_STRING, _("Change"), COL_CHANGE, True, gtk.CellRendererText(), markup=True)
            , Column(COL_ICON, gobject.TYPE_OBJECT, _("Change"), COL_ICON, True, gtk.CellRendererPixbuf(), share_column=True, icon =True)
            , Column(COL_COMMENT, gobject.TYPE_STRING, _("Comment"), COL_COMMENT, True, gtk.CellRendererText())
                ]
        Treeview.__init__(self, treeview)
    
    def get_custom_header_widget(self, ID):
        #create custom header widgets
        widget = None
        if ID == COL_CURRENTPRICE:
            widget = gtk.Label()
            widget.set_markup('<span size="medium"><b>Last Trade</b></span>\n<span size="small">Price</span>\n<span size="small">Trade Time</span>') 
        elif ID == COL_PRICE:                  
            widget = gtk.Label()
            widget.set_markup('<span size="medium"><b>Watch Start</b></span>\n<span size="small">Price</span>\n<span size="small">Trade Time</span>') 
        elif ID == COL_NAME:
            widget = gtk.Label()
            widget.set_markup('<span size="medium"><b>Quote</b></span>\n<span size="small">Name</span>\n<span size="small">Symbol</span>')             
        elif ID == COL_COMMENT:
            widget = gtk.Label()
            widget.set_markup('<span size="medium"><b>Comment</b></span>\n<span size="small"> </span>\n<span size="small"> </span>') 
        elif ((ID == COL_CURRENTCHANGE) or (ID == COL_CHANGE)):
            widget = gtk.Label()
            widget.set_markup('<span size="medium"><b>Change</b></span>\n<span size="small">$</span>\n<span size="small">%</span>') 
        return widget
        
class PortfolioPerformanceTree(Treeview):
    def __init__(self, treeview):
        self.name = 'PortfolioPerformanceTree'
        self.tree_columns = [
            Column(COL_OBJECT, gobject.TYPE_PYOBJECT, "object", COL_OBJECT)
            , Column(COL_OBJECT_TYPE, gobject.TYPE_INT, "object_type", COL_OBJECT_TYPE)
            , Column(COL_QUANTITY, gobject.TYPE_STRING, _("Quantity"), COL_QUANTITY, True, gtk.CellRendererText(), markup=True)
            , Column(COL_PF_NAME, gobject.TYPE_STRING, _("Name"), COL_PF_NAME, True, gtk.CellRendererText(), markup=True)
            , Column(COL_BUYPRICE, gobject.TYPE_STRING, _("Buy Price"), COL_BUYPRICE, True, gtk.CellRendererText(), markup=True)
            , Column(COL_BUYSUM, gobject.TYPE_STRING, _("Buy Sum"), COL_BUYSUM, True, gtk.CellRendererText(), markup=True)
            , Column(COL_LASTTRADE, gobject.TYPE_STRING, _("Last Trade"), COL_LASTTRADE, True, gtk.CellRendererText(), markup=True)
            , Column(COL_PF_CHANGE, gobject.TYPE_STRING, _("Change"), COL_PF_CHANGE, True, gtk.CellRendererText(), markup=True)
            , Column(COL_PF_ICON, gobject.TYPE_OBJECT, _("Change"), COL_PF_ICON, True, gtk.CellRendererPixbuf(), share_column=True, icon =True)
            , Column(COL_PF_OVERALL, gobject.TYPE_STRING, _("Overall Change"), COL_PF_OVERALL, True, gtk.CellRendererText(), markup=True)
            , Column(COL_PF_OALL_ICON, gobject.TYPE_OBJECT, _("Overall Change"), COL_PF_OALL_ICON, True, gtk.CellRendererPixbuf(), share_column=True, icon =True)
            , Column(COL_PF_COMMENT, gobject.TYPE_STRING, _("Comment"), COL_PF_COMMENT, True, gtk.CellRendererText())
                ]
        Treeview.__init__(self, treeview)
    
    def get_custom_header_widget(self, ID):
        #create custom header widgets
        widget = None
        if ID == COL_LASTTRADE:
            widget = gtk.Label()
            widget.set_markup('<span size="medium"><b>Last Trade</b></span>\n<span size="small">Price</span>\n<span size="small">Trade Time</span>') 
        elif ID == COL_BUYPRICE:                  
            widget = gtk.Label()
            widget.set_markup('<span size="medium"><b>Buy</b></span>\n<span size="small">Price</span>\n<span size="small">Trade Time</span>') 
        elif ID == COL_PF_NAME:
            widget = gtk.Label()
            widget.set_markup('<span size="medium"><b>Quote</b></span>\n<span size="small">Name</span>\n<span size="small">Symbol</span>')             
        elif ID == COL_PF_COMMENT:
            widget = gtk.Label()
            widget.set_markup('<span size="medium"><b>Comment</b></span>\n<span size="small"> </span>\n<span size="small"> </span>') 
        elif ID == COL_QUANTITY:
            widget = gtk.Label()
            widget.set_markup('<span size="medium"><b>Quantity</b></span>\n<span size="small"> </span>\n<span size="small"> </span>') 
        elif ID == COL_BUYSUM:
            widget = gtk.Label()
            widget.set_markup('<span size="medium"><b>Sum</b></span>\n<span size="small"> </span>\n<span size="small"> </span>') 
        elif ID == COL_PF_CHANGE:
            widget = gtk.Label()
            widget.set_markup('<span size="medium"><b>Change</b></span>\n<span size="small">$</span>\n<span size="small">%</span>') 
        elif ID == COL_PF_OVERALL:
            widget = gtk.Label()
            widget.set_markup('<span size="medium"><b>Overall</b></span>\n<span size="small">$</span>\n<span size="small">%</span>') 
        return widget


class FundamentalsTree(Treeview):
    def __init__(self, treeview):
        self.name = 'PerformanceTree'
        self.tree_columns = [
            Column(COL_OBJECT, gobject.TYPE_PYOBJECT, "object", COL_OBJECT)
            , Column(COL_OBJECT_TYPE, gobject.TYPE_INT, "object_type", COL_OBJECT_TYPE)
            , Column(COL_NAME, gobject.TYPE_STRING, _("Name"), COL_NAME, True, gtk.CellRendererText(), markup=True)
            , Column(COL_MKTCAP, gobject.TYPE_STRING, _("Mkt Cap"), COL_MKTCAP, True, gtk.CellRendererText(), markup=True)
            , Column(COL_AVG_VOL, gobject.TYPE_STRING, _("Avg. Vol."), COL_AVG_VOL, True, gtk.CellRendererText(), markup=True)
            , Column(COL_52WEEK_HIGH, gobject.TYPE_STRING, _("52 Week high"), COL_52WEEK_HIGH, True, gtk.CellRendererText(), markup=True)
            , Column(COL_52WEEK_LOW, gobject.TYPE_STRING, _("52 Week low"), COL_52WEEK_LOW, True, gtk.CellRendererText(), markup=True)
            , Column(COL_EPS, gobject.TYPE_STRING, _("EPS"), COL_EPS, True, gtk.CellRendererText())
            , Column(COL_PE, gobject.TYPE_STRING, _("P/E"), COL_PE, True, gtk.CellRendererText())
                ]
        Treeview.__init__(self, treeview)

    def get_custom_header_widget(self, ID):
        #create custom header widgets
        widget = None
        if ID == COL_52WEEK_HIGH:
            widget = gtk.Label()
            widget.set_markup('<span size="medium"><b>52week high</b></span>\n<span size="small">Price</span>\n<span size="small">Trade Time</span>') 
        elif ID == COL_52WEEK_LOW:                  
            widget = gtk.Label()
            widget.set_markup('<span size="medium"><b>52week low</b></span>\n<span size="small">Price</span>\n<span size="small">Trade Time</span>') 
        elif ID == COL_NAME:
            widget = gtk.Label()
            widget.set_markup('<span size="medium"><b>Quote</b></span>\n<span size="small">Name</span>\n<span size="small">Symbol</span>')             
        return widget
