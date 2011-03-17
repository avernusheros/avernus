#!/usr/bin/env python

import gtk
from avernus import pubsub
from avernus.controller import controller
from avernus.gui import gui_utils


class ContainerOverviewTab(gtk.VBox):

    def __init__(self, item):
        gtk.VBox.__init__(self)
        if item.name == 'Accounts':
            tree = AccountOverviewTree()
        else:
            tree = ContainerOverviewTree(item)
        sw = gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.add(tree)

        self.pack_start(sw)
        self.show_all()


class AccountOverviewTree(gui_utils.Tree):

    def __init__(self):
        gui_utils.Tree.__init__(self)
        self.set_rules_hint(True)
        self.model = gtk.ListStore(object, str, float, int, object, object)
        self.set_model(self.model)
        self.create_column(_('Name'), 1)
        self.create_column(_('Amount'), 2, func=gui_utils.currency_format)
        self.create_column(_('# Transactions'), 3)
        self.create_column(_('First transaction'), 4, func = gui_utils.date_to_string)
        self.create_column(_('Last transaction'), 5, func =gui_utils.date_to_string)
        self._load_accounts()

    def _load_accounts(self):
        for acc in controller.getAllAccount():
            self.model.append([acc,
                               acc.name,
                               acc.amount,
                               acc.transaction_count,
                               acc.birthday,
                               acc.lastday])


class ContainerOverviewTree(gui_utils.Tree):

    OBJ = 0
    NAME = 1
    LAST_PRICE = 2
    CHANGE = 3
    CHANGE_PERCENT = 4
    TER = 5

    def __init__(self, container):
        self.container = container
        gui_utils.Tree.__init__(self)
        self.set_model(gtk.ListStore(object,str, str,float, float, float))

        self.create_column(_('Name'), self.NAME)
        self.create_column(_('Current value'), self.LAST_PRICE)
        col, cell = self.create_column(_('Change'), self.CHANGE, func=gui_utils.float_to_red_green_string)
        col, cell = self.create_column(_('Change %'), self.CHANGE_PERCENT, func=gui_utils.float_to_red_green_string)
        col, cell = self.create_column(unichr(8709)+' TER', self.TER, func=gui_utils.float_format)

        def sort_price(model, iter1, iter2):
            item1 = model.get_value(iter1, self.OBJ)
            item2 = model.get_value(iter2, self.OBJ)
            if item1.price == item2.price: return 0
            elif item1.price < item2.price: return -1
            else: return 1

        self.get_model().set_sort_func(self.LAST_PRICE, sort_price)

        self.set_rules_hint(True)
        self.load_items()
        self.connect("destroy", self.on_destroy)
        self.connect("row-activated", self.on_row_activated)
        self.subscriptions = (
            ('stocks.updated', self.on_stocks_updated),
            ('shortcut.update', self.on_update)
        )
        for topic, callback in self.subscriptions:
            pubsub.subscribe(topic, callback)

        self.selected_item = None

    def on_update(self):
        self.container.update_positions()

    def on_row_activated(self, treeview, path, view_column):
        item = self.get_model()[path][0]
        pubsub.publish('overview.item.selected', item)

    def on_destroy(self, x):
        for topic, callback in self.subscriptions:
            pubsub.unsubscribe(topic, callback)

    def load_items(self):
        items = []
        if self.container.name == 'Watchlists':
            items = controller.getAllWatchlist()
        elif self.container.name == 'Portfolios':
            items = controller.getAllPortfolio()
        for item in items:
            self.insert_item(item)

    def on_stocks_updated(self, container):
        if container.id == self.container.id:
            for row in self.get_model():
                item = row[0]
                row[self.LAST_PRICE] = gui_utils.get_price_string(item)
                row[self.CHANGE] = item.change
                row[self.CHANGE_PERCENT] = item.percent
                row[self.TER] = item.ter

    def insert_item(self, item):
        self.get_model().append([item,
                               item.name,
                               gui_utils.get_price_string(item),
                               item.change,
                               item.percent,
                               item.ter])
