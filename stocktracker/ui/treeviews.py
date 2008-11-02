import gtk, string
import gobject
import config, helper



class Tree:
    def remove(self, iter):
        self.model.remove(iter)

    def insert(self, item):
        return None

    def clear(self):
        self.model.clear()


class LeftTree(Tree):
    def __init__(self, tree):
        """
        @params tree - treeview
        """
        self.tree = tree
        #type, id, name
        self.model = gtk.TreeStore(int,int, str)
        self.tree.set_model(self.model)
        #self.tree.set_reorderable(True)
        #self.tree.set_rules_hint(True)
        self.cell = gtk.CellRendererText()
        self.column = gtk.TreeViewColumn('Folder', self.cell, markup = 2)
        self.tree.append_column(self.column)
        #self.cellicon = gtk.CellRendererPixbuf()
        #self.cellicon.set_property('xpad', 2)
        #self.cell.set_property('editable', False)
        #self.cell.connect('edited', self.edited_cb, self.model)
        #self.cell.connect('editing-started', self.editing_started, self.model)
        #self.column.pack_start(self.cellicon, False)
       # self.column.pack_start(self.cell, True)
        #self.column.set_attributes(self.cellicon, pixbuf=2)
        #self.column.add_attribute(self.cell, 'text' ,2)
        self.tree.set_search_column(2)
        self.column.set_sort_column_id(2)
        #self.tree.connect("drag_data_received", self.drag_data_received_data)
        self.watchlist_iter = self.model.append(None, [config.CATEGORY_W, -1,"<b>Watchlists</b>"])
        self.portfolio_iter = self.model.append(None, [config.CATEGORY_P, -1,"<b>Portfolios</b>"])

    def insert_after(self, iter, item):
        if not iter:
            if item['type'] == config.WATCHLIST:
                iter = self.watchlist_iter
            elif item['type'] == config.PORTFOLIO:
                iter = self.portfolio_iter
        iter = self.model.append(iter, [item['type'], item['id'], item['name']])
        return iter


class PerformanceTreeWatchlist(Tree):
    def __init__(self, tree):
        """
        @params tree - treeview
        """
        self.tree = tree
        #type, id, quantity, name, buyprice, buysum, lasttrade, change, icon, overallchange, icon, comment
        self.model = gtk.TreeStore(int,int, str, str,str, str,str,str,  gtk.gdk.Pixbuf, str,  gtk.gdk.Pixbuf, str)
        self.tree.set_model(self.model)
        #self.tree.set_reorderable(True)
        #self.tree.set_rules_hint(True)

        #quantity
        self.column_quantity = gtk.TreeViewColumn('Quantity', gtk.CellRendererText(), markup = 2)
        widget1 = gtk.Label()
        widget1.set_markup('<span size="medium"><b>Quantity</b></span>\n<span size="small"> </span>\n<span size="small"> </span>')
        self.column_quantity.set_widget(widget1)
        widget1.show()
        self.tree.append_column(self.column_quantity)

        #name
        self.column_name = gtk.TreeViewColumn('Name', gtk.CellRendererText(), markup = 3)
        widget2 = gtk.Label()
        widget2.set_markup('<span size="medium"><b>Name</b></span>\n<span size="small">ISIN</span>\n<span size="small">Exchange</span>')
        self.column_name.set_widget(widget2)
        widget2.show()
        self.tree.append_column(self.column_name)

        #buyprice
        self.column_buyprice = gtk.TreeViewColumn('buyprice', gtk.CellRendererText(), markup = 4)
        widget3 = gtk.Label()
        widget3.set_markup('<span size="medium"><b>Buy</b></span>\n<span size="small">Price</span>\n<span size="small">Trade Time</span>')
        self.column_buyprice.set_widget(widget3)
        widget3.show()
        self.tree.append_column(self.column_buyprice)

        #buysum
        self.column_buysum = gtk.TreeViewColumn('buysum', gtk.CellRendererText(), markup = 5)
        widget4 = gtk.Label()
        widget4.set_markup('<span size="medium"><b>Sum</b></span>\n<span size="small"> </span>\n<span size="small"> </span>')
        self.column_buysum.set_widget(widget4)
        widget4.show()
        self.tree.append_column(self.column_buysum)

        #lasttrade
        self.column_lasttrade = gtk.TreeViewColumn('lasttrade', gtk.CellRendererText(), markup = 6)
        widget5 = gtk.Label()
        widget5.set_markup('<span size="medium"><b>Last Trade</b></span>\n<span size="small">Price</span>\n<span size="small">Trade Time</span>')
        self.column_lasttrade.set_widget(widget5)
        widget5.show()
        self.tree.append_column(self.column_lasttrade)

        #change
        self.column_change = gtk.TreeViewColumn('change', gtk.CellRendererText(), markup = 7)
        widget5 = gtk.Label()
        widget5.set_markup('<span size="medium"><b>Change</b></span>\n<span size="small">$</span>\n<span size="small">%</span>')
        self.column_change.set_widget(widget5)
        widget5.show()
        self.tree.append_column(self.column_change)
        icon1 = gtk.CellRendererPixbuf()
        self.column_change.pack_start(icon1, True)
        self.column_change.add_attribute(icon1, "pixbuf", 8)

        #overallchange
        self.column_overallchange = gtk.TreeViewColumn('overallchange', gtk.CellRendererText(), markup = 9)
        widget6 = gtk.Label()
        widget6.set_markup('<span size="medium"><b>Change</b></span>\n<span size="small">$</span>\n<span size="small">%</span>')
        self.column_overallchange.set_widget(widget6)
        widget6.show()
        self.tree.append_column(self.column_overallchange)
        icon2 = gtk.CellRendererPixbuf()
        self.column_overallchange.pack_start(icon2, True)
        self.column_overallchange.add_attribute(icon2, "pixbuf", 10)

        #comment
        self.column_comment = gtk.TreeViewColumn('Name', gtk.CellRendererText(), markup = 9)
        widget7 = gtk.Label()
        widget7.set_markup('<span size="medium"><b>Comment</b></span>\n<span size="small"> </span>\n<span size="small"> </span>')
        self.column_comment.set_widget(widget7)
        widget7.show()
        self.tree.append_column(self.column_comment)

    def insert(self, item):
        color = '#606060'
        #print item
        name = "" + item['name'] +"\n<span foreground=\""+ color +"\"><small>" +item['isin']+ "</small></span>\n<span foreground=\""+ color +"\"><small>" +item['exchange']+ "</small></span>"
        buy = "" + str(item['buyprice']) + "\n<span foreground=\""+ color +"\"><small>" +helper.makeStringFromTime(item['buydate'])+ "</small></span>"
        icon1 = gtk.gdk.pixbuf_new_from_file(helper.get_arrow_type(item['change']))
        icon2 = gtk.gdk.pixbuf_new_from_file(helper.get_arrow_type(item['change']))
        iter = self.model.append(None, [item['type'], item['id']
                ,  str(item['quantity']), name, buy
                , str(item['buysum']), str(item['price'])
                , str(item['change']), icon1
                , str(item['change']), icon2
                , item['comment']])
        return iter




class PerformanceTreePortfolio(PerformanceTreeWatchlist):
    pass


class FundamentalsTree(Tree):
    def __init__(self, tree):
        """
        @params tree - treeview
        """
        self.tree = tree
        #type, id, name, mktcap, avg_vol, 52week high, 52week low, eps, pe
        self.model = gtk.TreeStore(int,int, str, str, str, str, str, str, str)
        self.tree.set_model(self.model)

        #name
        self.column_name = gtk.TreeViewColumn('Name', gtk.CellRendererText(), markup = 2)
        widget1 = gtk.Label()
        widget1.set_markup('<span size="medium"><b>Name</b></span>\n<span size="small">ISIN</span>\n<span size="small">Exchange</span>')
        self.column_name.set_widget(widget1)
        widget1.show()
        self.tree.append_column(self.column_name)

        #mktcap
        self.column_mktcap = gtk.TreeViewColumn('Mktcap', gtk.CellRendererText(), markup = 3)
        self.tree.append_column(self.column_mktcap)

        #avgvol
        self.column_avgvol = gtk.TreeViewColumn('Avg. Volume', gtk.CellRendererText(), markup = 4)
        self.tree.append_column(self.column_avgvol)

        #52week high
        self.column_52high = gtk.TreeViewColumn('', gtk.CellRendererText(), markup = 5)
        widget2 = gtk.Label()
        widget2.set_markup('<span size="medium"><b>52week high</b></span>\n<span size="small">Price</span>\n<span size="small">Trade Time</span>')
        self.column_52high.set_widget(widget2)
        widget2.show()
        self.tree.append_column(self.column_52high)

        #52week low
        self.column_52low = gtk.TreeViewColumn('', gtk.CellRendererText(), markup = 6)
        widget3 = gtk.Label()
        widget3.set_markup('<span size="medium"><b>52week low</b></span>\n<span size="small">Price</span>\n<span size="small">Trade Time</span>')
        self.column_52low.set_widget(widget3)
        widget3.show()
        self.tree.append_column(self.column_52low)

        #eps
        self.column_eps = gtk.TreeViewColumn('EPS', gtk.CellRendererText(), markup = 7)
        self.tree.append_column(self.column_eps)

        #pe
        self.column_pe = gtk.TreeViewColumn('PE', gtk.CellRendererText(), markup = 8)
        self.tree.append_column(self.column_pe)

    def insert(self, item):
        color = '#606060'
        name = "" + item['name'] +"\n \
                <span foreground=\""+ color +"\"><small>" +item['isin']+ "</small></span>\n \
                 <span foreground=\""+ color +"\"><small>" +item['exchange']+ "</small></span>"
        iter = self.model.append(None, [item['type'], item['id']
                , name, item['market_cap'], item['avg_daily_volume']
                , item['52_week_high'], item['52_week_low']
                , item['earnings_per_share'], item['price_earnings_ratio']])
        return iter


class TransactionsTree(Tree):
    def __init__(self, tree):
        """
        @params tree - treeview
        """
        self.tree = tree
        #type, id,datetime, name, type, quantity, price, transaction costs, value
        self.model = gtk.TreeStore(int,int, str, str, str, str, str, str, str)
        self.tree.set_model(self.model)

        #pe
        self.column_date = gtk.TreeViewColumn('Date', gtk.CellRendererText(), markup = 2)
        self.tree.append_column(self.column_date)

        #name
        self.column_name = gtk.TreeViewColumn('Name', gtk.CellRendererText(), markup = 3)
        widget2 = gtk.Label()
        widget2.set_markup('<span size="medium"><b>Name</b></span>\n<span size="small">ISIN</span>\n<span size="small">Exchange</span>')
        self.column_name.set_widget(widget2)
        widget2.show()
        self.tree.append_column(self.column_name)

        #type
        self.column_type = gtk.TreeViewColumn('type', gtk.CellRendererText(), markup = 4)
        self.tree.append_column(self.column_type)

        #quantity
        self.column_quantity = gtk.TreeViewColumn('quantity', gtk.CellRendererText(), markup = 5)
        self.tree.append_column(self.column_quantity)

        #price
        self.column_price = gtk.TreeViewColumn('price', gtk.CellRendererText(), markup = 6)
        self.tree.append_column(self.column_price)

        #transaction costs
        self.column_transaction = gtk.TreeViewColumn('transaction costs', gtk.CellRendererText(), markup = 7)
        self.tree.append_column(self.column_transaction)

        #value
        self.column_value = gtk.TreeViewColumn('value', gtk.CellRendererText(), markup = 8)
        self.tree.append_column(self.column_value)


    def insert(self, item):        #type, id,datetime, name, type, quantity, price, transaction costs, value, comment
        color = '#606060'
        name = "" + item['name'] +"\n"+ helper.makePangoStringSmall(color, item['isin'], True) + helper.makePangoStringSmall(color,item['exchange'])
        value = float(item['transaction_costs']) + int(item['quantity'])*float(item['price'])
        iter = self.model.append(None, [item['type'], item['id']
                ,  helper.makePangoStringSmall(color, helper.makeStringFromTime(item['datetime'])), name, str(item['type'])
                , str(item['quantity']), str(item['price'])
                , str(item['transaction_costs']), value
                ])
        return iter
