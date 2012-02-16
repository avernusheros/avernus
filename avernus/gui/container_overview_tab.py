#!/usr/bin/env python

from gi.repository import Gtk
from avernus import pubsub
from avernus.controller import portfolio_controller as pfctlr
from avernus.controller import controller
from avernus.gui import gui_utils


class ContainerOverviewTab(Gtk.VBox):

    def __init__(self, item):
        Gtk.VBox.__init__(self)
        if item.name == 'Accounts':
            tree = AccountOverviewTree()
        else:
            tree = ContainerOverviewTree(item)
        sw = Gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        sw.set_property('vscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        sw.add(tree)

        self.pack_start(sw, True, True, 0)
        self.show_all()


class AccountOverviewTree(gui_utils.Tree):

    def __init__(self):
        gui_utils.Tree.__init__(self)
        self.set_rules_hint(True)
        self.model = Gtk.ListStore(object, str, float, int, object, object)
        self.set_model(self.model)
        self.create_column(_('Name'), 1)
        self.create_column(_('Amount'), 2, func=gui_utils.currency_format)
        self.create_column(_('# Transactions'), 3)
        self.create_column(_('First transaction'), 4, func=gui_utils.date_to_string)
        self.create_column(_('Last transaction'), 5, func=gui_utils.date_to_string)
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
    VALUE = 2
    CHANGE = 3
    CHANGE_PERCENT = 4
    TER = 5
    LAST_UPDATE = 6
    COUNT = 7
    PERCENT = 8

    def __init__(self, container):
        self.container = container
        gui_utils.Tree.__init__(self)
        self.set_model(Gtk.ListStore(object,str, float,float, float, float, object,int,float))

        self.create_column(_('Name'), self.NAME)
        self.create_column(_('Current value'), self.VALUE, func=gui_utils.currency_format)
        self.create_column(_('%'), self.PERCENT, func=gui_utils.percent_format)
        self.create_column(_('Last update'), self.LAST_UPDATE, func=gui_utils.date_to_string)
        self.create_column(_('# positions'), self.COUNT)
        col, cell = self.create_column(_('Change'), self.CHANGE, func=gui_utils.float_to_red_green_string)
        col, cell = self.create_column(_('Change %'), self.CHANGE_PERCENT, func=gui_utils.float_to_red_green_string)
        col, cell = self.create_column(unichr(8709)+' TER', self.TER, func=gui_utils.float_format)

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
            items = pfctlr.getAllWatchlist()
        elif self.container.name == 'Portfolios':
            items = pfctlr.getAllPortfolio()
        self.overall_value = sum([i.cvalue for i in items])
        if self.overall_value == 0.0:
            self.overall_value = 1
        for item in items:
            self.insert_item(item)

    def on_stocks_updated(self, container):
        if container.id == self.container.id:
            for row in self.get_model():
                item = row[0]
                row[self.VALUE] = item.cvalue
                row[self.LAST_UPDATE] = item.last_update
                row[self.CHANGE] = item.change
                row[self.CHANGE_PERCENT] = item.percent
                row[self.TER] = item.ter

    def insert_item(self, item):
        self.get_model().append([item,
                               item.name,
                               item.cvalue,
                               item.change,
                               float(item.percent),
                               item.ter,
                               item.last_update,
                               len(item),
                               100*item.cvalue/self.overall_value])
