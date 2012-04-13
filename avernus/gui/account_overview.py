#!/usr/bin/env python

from gi.repository import Gtk
from avernus.controller import account_controller
from avernus.gui import gui_utils


class AccountOverview(Gtk.VBox):

    def __init__(self, *args):
        Gtk.VBox.__init__(self)
        tree = AccountOverviewTree()
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
        for acc in account_controller.get_all_account():
            self.model.append([acc,
                               acc.name,
                               acc.balance,
                               len(acc.transactions),
                               account_controller.account_birthday(acc),
                               account_controller.account_lastday(acc),
                              ])


