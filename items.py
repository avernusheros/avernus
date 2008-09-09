#!/usr/bin/env python

import stock_tracker
import datetime
import time
import config
import treeviews
import stock

try:
    import sys
    import gtk
    import gtk.glade
    import treeviews
except ImportError, e:
    print _T("Import error in watchlist:"), e
    sys.exit(1)

CATEGORY      = 0
WATCHLIST     = 1
PORTFOLIO     = 2
WATCHLISTITEM = 3
PORTFOLIOITEM = 4

class ItemBase(object):
    """This is the base class for watchlist and quote """
    def __init__(self, type):
        """The only way to set the type is through the
        initialization"""
        self.type = type

    def get_column_list(self, columnList):
        """This function is used to get the display list
        for the Tree. The COlumnList controls the
        order that the list will be returned in. Used as the
        second param in the gtk.TreeStore.append function.
        @param watchlistColumnList - list - A list of watchlistColumn items.
        Their type member should use used to determine the order
        of the returned list.
        @returns list - A list for the watchlistTree.
        """
        pass

    def add_to_tree(self, tree, parent):
        """This function is used to add an item to a
        gtk.TreeStore, usually when loading.  All
        children will be added as well
        @param tree - gtk.TreeStore - The tree store that
        we wil be adding to.
        @param parent gtk.TreeIter - The parent of this
        item.
        @param watchlistColumnList - list - A list of watchlistColumn items.
        Their type member should use used to determine the order
        of the returned list.
        """
        tree.append(parent, self.get_column_list(tree.tree_columns))
        
    def set_tree_values(self, tree_model, iter, columnList):
        """This is used to set the values in a tree.
        For whatever reason you cannot use the same list that you
        use to append items into the tree?  I don't know why.
        @param tree - gtk.TreeStore - The tree store that we will be setting the values in
        @param iter - gtk.TreeIter - The item in the tree
        @param watchlistColumnList - list - A list of watchlistColumn items.
        Their type member should use used to determine the order
        of the returned list."""
        lst_values = self.get_column_list(columnList)
        count = 0
        for value in lst_values:
            tree_model.set_value(iter, count, value)
            count += 1

class Category(ItemBase):
    def __init__(self, name, tree):
        #init base
        ItemBase.__init__(self, CATEGORY)
        #init variables
        self.__m_name = ""
        self.name = name
        #children
        self.__m_children = []
        self.add_to_tree(tree)

    def __str__(self):
        return _("<watchlist object: name = %s num_children = %d>") % (self.name, len(self.__m_children))

    def add_child(self, item):
        """Add a child to the watchlist.
        @param item - Either a watchlist or a quote. This will be a child of the watchlist.
        """
        self.__m_children.append(item)
        
    def remove_child(self, item):
        """Removes a child from the watchlist.
        @param item - Either a watchlist or a quote. This will be a removed.
        """
        try:
            self.__m_children.remove(item)
        except ValueError, e:
            helper.show_error_dlg(_("Error removing child %s = %s") % (item, e))
        
    def get_column_list(self, watchlistColumnList):
        """This function is used to get the display list
        for the watchlistTree. The watchlistColumnList controls the
        order that the list will be returned in.
        @param watchlistColumnList - list - A list of watchlistColumn items.
        Their type member should use used to determine the order
        of the returned list.
        @returns list - A list for the watchlistTree.
        """
        lst_return = []
        # Loop through the columns and create the return list
        for item_column in watchlistColumnList:
            if (item_column.ID == treeviews.COL_OBJECT):
                lst_return.append(self)
            elif (item_column.ID == treeviews.COL_OBJECT_TYPE):
                lst_return.append(self.type)
            elif (item_column.ID == treeviews.COL_FOLDER):
                lst_return.append("<b>%s</b>" % self.name)
            else:
                lst_return.append("")
        return lst_return
    
    def add_to_tree(self, tree):
        """This function is used to add an item to a
        gtk.TreeStore, usually when loading.  All
        children will be added as well
        @param tree - gtk.TreeStore - The tree store that
        we will be adding to.
        @param parent gtk.TreeIter - The parent of this
        item.
        @param watchlistColumnList - list - A list of watchlistColumn items.
        Their type member should use used to determine the order of the returned list.
        """
        insert_iter = tree.treestore.append(None, self.get_column_list(tree.tree_columns))
        if (insert_iter):
            for child in self.__m_children:
                child.add_to_tree(tree.treestore, insert_iter, tree.tree_columns)
        else:
            helper.show_error_dlg(_("Error appending category: %s" % self))
    
    def clear(self):
        self.__m_children = []
        
    def get_child_quotes(self):
        ret = []
        for child in self.__m_children:
            ret.extend(child.get_child_quotes())
        return ret


class Watchlist(ItemBase):
    def __init__(self, name, description = ""):
        #init base
        ItemBase.__init__(self, WATCHLIST)
        #init variables
        self.name = name
        self.description = description
        #children
        self.__m_children = []

    def add_child(self, item):
        """Add a child to the watchlist.
        @param item - Either a watchlist or a quote. This will be a child of the watchlist.
        """
        self.__m_children.append(item)
        
    def get_child_quotes(self):
        """ returns all quotes in this watchlist, including those in children watchlists"""
        returnlist = []
        for child in self.__m_children:
            if child.type == QUOTE:
                returnlist.append(child)
            elif child.type == WATCHLIST:
                returnlist.extend(child.get_child_quotes())
            else:
                print "unknown type!!!"
        return returnlist

    def remove_child(self, item):
        """Removes a child from the watchlist.
        @param item - Either a watchlist or a quote. This will be a removed.
        """
        try:
            self.__m_children.remove(item)
        except ValueError, e:
            helper.show_error_dlg(_("Error removing child %s = %s") % (item, e))

    def get_column_list(self, watchlistColumnList):
        """This function is used to get the display list
        for the watchlistTree. The watchlistColumnList controls the
        order that the list will be returned in.
        @param watchlistColumnList - list - A list of watchlistColumn items.
        Their type member should use used to determine the order
        of the returned list.
        @returns list - A list for the watchlistTree.
        """
        lst_return = []
        # Loop through the columns and create the return list
        for item_column in watchlistColumnList:
            if (item_column.ID == treeviews.COL_OBJECT):
                lst_return.append(self)
            elif (item_column.ID == treeviews.COL_OBJECT_TYPE):
                lst_return.append(self.type)
            elif (item_column.ID == treeviews.COL_FOLDER):
                lst_return.append(self.name)
            else:
                lst_return.append("")
        return lst_return
    
    def add_to_tree(self, tree, parent, columnList):
        """This function is used to add an item to a gtk.TreeStore, usually when loading.  All children will be added as well
        @param tree - gtk.TreeStore - The tree store that we will be adding to.
        @param parent gtk.TreeIter - The parent of this item.
        @param watchlistColumnList - list - A list of watchlistColumn items.
        Their type member should use used to determine the order of the returned list.
        """
        tree.append(parent, self.get_column_list(columnList))
        
    def add_stocks_to_tree(self, performance_tree, fundamentals_tree):
        for child in self.__m_children:
            child.add_to_tree(performance_tree, fundamentals_tree)
            

class Portfolio(ItemBase):
    def __init__(self, name, description = ""):
        #init base
        ItemBase.__init__(self, PORTFOLIO)
        #init variables
        self.name = name
        self.description = description
        #children
        self.__m_children = []
    
    def add_child(self, item):
        """Add a child to the watchlist.
        @param item - Either a watchlist or a quote. This will be a child of the watchlist.
        """
        self.__m_children.append(item)
    
    def get_child_quotes(self):
        """ returns all quotes in this watchlist, including those in children watchlists"""
        returnlist = []
        for child in self.__m_children:
            if child.type == QUOTE:
                returnlist.append(child)
            elif child.type == WATCHLIST:
                returnlist.extend(child.get_child_quotes())
            else:
                print "unknown type!!!"
        return returnlist

    def remove_child(self, item):
        """Removes a child from the watchlist.
        @param item - Either a watchlist or a quote. This will be a removed.
        """
        try:
            self.__m_children.remove(item)
        except ValueError, e:
            helper.show_error_dlg(_("Error removing child %s = %s") % (item, e))

    def get_column_list(self, watchlistColumnList):
        """This function is used to get the display list
        for the watchlistTree. The watchlistColumnList controls the
        order that the list will be returned in.
        @param watchlistColumnList - list - A list of watchlistColumn items.
        Their type member should use used to determine the order
        of the returned list.
        @returns list - A list for the watchlistTree.
        """
        lst_return = []
        # Loop through the columns and create the return list
        for item_column in watchlistColumnList:
            if (item_column.ID == treeviews.COL_OBJECT):
                lst_return.append(self)
            elif (item_column.ID == treeviews.COL_OBJECT_TYPE):
                lst_return.append(self.type)
            elif (item_column.ID == treeviews.COL_FOLDER):
                lst_return.append(self.name)
            else:
                lst_return.append("")
        return lst_return
    
    def add_to_tree(self, tree, parent, columnList):
        """This function is used to add an item to a gtk.TreeStore, usually when loading.  All children will be added as well
        @param tree - gtk.TreeStore - The tree store that we will be adding to.
        @param parent gtk.TreeIter - The parent of this item.
        @param watchlistColumnList - list - A list of watchlistColumn items.
        Their type member should use used to determine the order of the returned list.
        """
        tree.append(parent, self.get_column_list(columnList))
        
    def add_stocks_to_tree(self, performance_tree, fundamentals_tree):
        for child in self.__m_children:
            child.add_to_tree(performance_tree, fundamentals_tree)
            

class WatchlistItem(ItemBase):
    """This is a quote in the watchlistTree.  It represents a quote in the watchlist """
    def __init__(self, symbol, name, comment):
        #init variables
        self.stock = stock.Stock(symbol, name, comment)
        #init base
        ItemBase.__init__(self, WATCHLISTITEM)

    def get_performance_column_list(self, columnList):
        """This function is used to get the display list
        for the watchlistTree. The watchlistCOlumnList controls the
        order that the list will be returned in.
        @param watchlistColumnList - list - A list of watchlistColumn items.
        Their type member should use used to determine the order of the returned list.
        @returns list - A list for the watchlistTree.
        """
        lst_return = []
        # Loop through the columns and create the return list      
        for item_column in columnList:
            if (item_column.ID == treeviews.COL_OBJECT):
                lst_return.append(self)
            elif (item_column.ID == treeviews.COL_OBJECT_TYPE):
                lst_return.append(self.type)
            elif (item_column.ID == treeviews.COL_NAME):
                lst_return.append(self.stock.get_name_text())  
            elif (item_column.ID == treeviews.COL_CURRENTPRICE):
                lst_return.append(self.stock.get_currentprice_text())    
            elif (item_column.ID == treeviews.COL_CURRENTCHANGE):
                lst_return.append(self.stock.get_currentchange_text())
            elif (item_column.ID == treeviews.COL_PRICE):
                lst_return.append(self.stock.get_price_text())    
            elif (item_column.ID == treeviews.COL_CHANGE):
                lst_return.append(self.stock.get_change_text())
            elif (item_column.ID == treeviews.COL_COMMENT):
                lst_return.append(self.stock.comment)
            else:
                helper.show_error_dlg(_("Error unknown column ID: %d" % item_column.ID))
                lst_return.append("")
        #return the list
        return lst_return
        
    def get_fundamentals_column_list(self, columnList):
        """This function is used to get the display list
        for the watchlistTree. The watchlistCOlumnList controls the
        order that the list will be returned in.
        @param watchlistColumnList - list - A list of watchlistColumn items.
        Their type member should use used to determine the order of the returned list.
        @returns list - A list for the watchlistTree.
        """
        lst_return = []
        # Loop through the columns and create the return list  
        for item_column in columnList:
            if (item_column.ID == treeviews.COL_OBJECT):
                lst_return.append(self)
            elif (item_column.ID == treeviews.COL_OBJECT_TYPE):
                lst_return.append(self.type)
            elif (item_column.ID == treeviews.COL_NAME):
                lst_return.append(self.stock.get_name_text())  
            elif (item_column.ID == treeviews.COL_MKTCAP):
                lst_return.append(str(self.stock.mkt_cap))   
            elif (item_column.ID == treeviews.COL_AVG_VOL):
                lst_return.append(str(self.stock.avg_vol))  
            elif (item_column.ID == treeviews.COL_52WEEK_HIGH):
                lst_return.append(str(self.stock.fiftytwoweek_high))  
            elif (item_column.ID == treeviews.COL_52WEEK_LOW):
                lst_return.append(str(self.stock.fiftytwoweek_low))  
            elif (item_column.ID == treeviews.COL_EPS):
                lst_return.append(str(self.stock.eps))  
            elif (item_column.ID == treeviews.COL_PE):
                lst_return.append(str(self.stock.pe))  
            else:
                helper.show_error_dlg(_("Error unknown column ID: %d" % item_column.ID))
                lst_return.append("")
        #return the list
        return lst_return
        
    def add_to_tree(self, performance_tree, fundamentals_tree):
        performance_tree.treestore.append(None, self.get_performance_column_list(performance_tree.tree_columns))
        fundamentals_tree.treestore.append(None, self.get_fundamentals_column_list(fundamentals_tree.tree_columns))

    def update(self):
        self.stock.update()


class PortfolioItem(WatchlistItem):
    def __init__(self, symbol, quantity, price, date, transactionCosts, comment):
        #init variables
        self.stock = stock.Stock(symbol, "", comment)
        self.quantity = quantity
        self.buyPrice = price
        self.buyDate = date
        self.transactionCosts = transactionCosts
        #init base
        ItemBase.__init__(self, PORTFOLIOITEM)
