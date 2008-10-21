#!/usr/bin/env python

import stocktracker
import datetime
import time
import config
import treeviews
import stock
import helper

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

    def update(self):
        for child in self.__m_children:
            child.update()



class Watchlist(ItemBase):
    def __init__(self, name, description = ""):
        #init base
        ItemBase.__init__(self, WATCHLIST)
        #init variables
        self.name = name
        self.description = description
        self.empty = True
        #children
        self.__m_children = []

    def add_child(self, item):
        """Add a child to the watchlist.
        @param item - Either a watchlist or a quote. This will be a child of the watchlist.
        """
        self.__m_children.append(item)
        self.empty = False

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
            if len(self.__m_children) == 0:
                self.empty = True
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

    def show(self, performance_tree, fundamentals_tree):
        #adding stocks to treeview
        for child in self.__m_children:
            child.add_to_tree(performance_tree, fundamentals_tree)

    def get_performance(self):
        if self.empty:
            return ['',None]
        start = 0
        change = 0
        for child in self.__m_children:
            start += child.stock.currentPrice - child.stock.currentChange
            change += child.stock.currentChange
        percent = 100/start * change
        return ['<span size="medium"><b> Performance </b></span>\n \
                <span size="small">$ '+ str(round(change,2)) +'</span>\n \
                <span size="small">% '+ str(round(percent,2)) +'</span>',
                config.get_arrow_type(percent, True)]

    def get_overall_performance(self):
        if self.empty:
            return ['',None]
        start = 0
        current_sum = 0
        for child in self.__m_children:
            current_sum += child.stock.currentPrice
            start += child.stock.startPrice
        change = current_sum - start
        percent = 100/start * change
        return ['<span size="medium"><b> Overall </b></span>\n \
                <span size="small">$ '+ str(round(change,2)) +'</span>\n \
                <span size="small">% '+ str(round(percent,2)) +'</span>',
                config.get_arrow_type(percent, True)]


    def update(self):
        for child in self.__m_children:
            child.update()


class Portfolio(ItemBase):
    def __init__(self, name, description = ""):
        #init base
        ItemBase.__init__(self, PORTFOLIO)
        #init variables
        self.name = name
        self.description = description
        self.buy_sum = 0.0
        self.empty = True
        #children
        self.__m_children = []

    def add_child(self, item):
        """Add a child to the watchlist.
        @param item - Either a watchlist or a quote. This will be a child of the watchlist.
        """
        self.__m_children.append(item)
        self.buy_sum += item.buy_sum
        self.empty = False

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
            self.buy_sum -= item.buy_sum
            self.__m_children.remove(item)
            if len(self.__m_children) == 0:
                self.empty = True
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

    def show(self, performance_tree, fundamentals_tree, transactions_tree):
        #adding positions to treeview...
        for child in self.__m_children:
            child.add_to_tree(performance_tree, fundamentals_tree, transactions_tree)

    def get_performance(self):
        if self.empty:
            return ['',None]
        start = 0
        change = 0
        for child in self.__m_children:
            start += child.quantity * (child.stock.currentPrice - child.stock.currentChange)
            change += child.stock.currentChange*child.quantity
        percent = 100/start * change
        return ['<span size="medium"><b> Performance </b></span>\n \
                <span size="small">$ '+ str(round(change,2)) +'</span>\n \
                <span size="small">% '+ str(round(percent,2)) +'</span>',
                config.get_arrow_type(percent, True)]

    def get_overall_performance(self):
        if self.empty:
            return ['',None]
        start = 0
        current_sum = 0
        for child in self.__m_children:
            current_sum += child.stock.currentPrice * child.quantity
            start += child.quantity * child.stock.startPrice
        change = current_sum - start
        percent = 100/start * change
        return ['<span size="medium"><b> Overall </b></span>\n \
                <span size="small">$ '+ str(round(change,2)) +'</span>\n \
                <span size="small">% '+ str(round(percent,2)) +'</span>',
                config.get_arrow_type(percent, True)]

    def update(self):
        for child in self.__m_children:
            child.update()

class WatchlistItem(ItemBase):
    """This is a quote in the watchlistTree.  It represents a quote in the watchlist """
    def __init__(self, stock_id, comment):
        #init variables
        self.stock = stock.Stock(stock_id, comment)
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
            elif (item_column.ID == treeviews.COL_CURRENTICON):
                lst_return.append(gtk.gdk.pixbuf_new_from_file(config.get_arrow_type(self.stock.currentChange)))
            elif (item_column.ID == treeviews.COL_ICON):
                lst_return.append(gtk.gdk.pixbuf_new_from_file(config.get_arrow_type(self.stock.change)))

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
    def __init__(self, stock_id, quantity, price, date, transactionCosts, comment):
        #init variables
        self.stock = stock.Stock(stock_id, comment)
        self.stock.startPrice = float(price.replace(",","."))
        self.stock.startDate = date
        self.transactionCosts = float(transactionCosts.replace(",","."))
        self.quantity = float(quantity.replace(",","."))
        self.buy_sum = self.stock.startPrice * self.quantity
        #init base
        ItemBase.__init__(self, PORTFOLIOITEM)

    def update(self):
        self.stock.update()

    def add_to_tree(self, performance_tree, fundamentals_tree, transactions_tree):
        WatchlistItem.add_to_tree(self, performance_tree, fundamentals_tree)
        #TODO
        #transactions_tree.treestore.append(None, self.get_transactions_column_list(transactions_tree.tree_columns))

    def get_buy_sum_text(self):
        color = '#606060'
        text = ""
        text = text + str(round(self.buy_sum, 2)) +"\n<span foreground=\""+ color +"\"><small>" +str(round(self.transactionCosts, 2)) + "</small></span>"
        return text

    def get_change_text(self):
        color = '#606060'
        text = ""
        text = text + str(round(self.stock.percent, 2)) +"\n \
                <span foreground=\""+ color +"\"><small>" +str(self.stock.change*self.quantity) + "</small></span> \n \
                <span foreground=\""+ color +"\"><small>" +str(self.stock.currentPrice*self.quantity) + "</small></span>"
        return text

    def get_currentchange_text(self):
        color = '#606060'
        text = ""
        text = text + str(self.stock.currentChange) +"\n \
                <span foreground=\""+ color +"\"><small>" +str(round(self.stock.currentPercent, 2)) + "</small></span> \n \
                <span foreground=\""+ color +"\"><small>" +str(self.stock.currentChange*self.quantity) + "</small></span>"
        return text

    def get_transactions_column_list(self, columnList):
        lst_return = []
        return lst_return

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
            elif (item_column.ID == treeviews.COL_QUANTITY):
                lst_return.append(self.quantity)
            elif (item_column.ID == treeviews.COL_PF_NAME):
                lst_return.append(self.stock.get_name_text())
            elif (item_column.ID == treeviews.COL_BUYPRICE):
                lst_return.append(self.stock.get_price_text())
            elif (item_column.ID == treeviews.COL_BUYSUM):
                lst_return.append(self.get_buy_sum_text())
            elif (item_column.ID == treeviews.COL_LASTTRADE):
                lst_return.append(self.stock.get_currentprice_text())
            elif (item_column.ID == treeviews.COL_PF_CHANGE):
                lst_return.append(self.get_currentchange_text())
            elif (item_column.ID == treeviews.COL_PF_OVERALL):
                lst_return.append(self.get_change_text())
            elif (item_column.ID == treeviews.COL_PF_COMMENT):
                lst_return.append(self.stock.comment)
            elif (item_column.ID == treeviews.COL_PF_ICON):
                lst_return.append(gtk.gdk.pixbuf_new_from_file(config.get_arrow_type(self.stock.currentChange)))
            elif (item_column.ID == treeviews.COL_PF_OALL_ICON):
                lst_return.append(gtk.gdk.pixbuf_new_from_file(config.get_arrow_type(self.stock.change)))
            else:
                helper.show_error_dlg(_("Error unknown column ID: %d" % item_column.ID))
                lst_return.append("")
        #return the list
        return lst_return


