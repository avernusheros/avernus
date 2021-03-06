#!/usr/bin/env python
from avernus.gui import gui_utils
from avernus.objects import account
from gi.repository import Gtk, Pango


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
        self.model = Gtk.TreeStore(object, str, float, int, object, object, int)
        self.set_model(self.model)
        col, cell = self.create_column(_('Name'), 1)
        cell.set_property('weight-set', True)
        col.add_attribute(cell, 'weight', 6)
        col, cell = self.create_column(_('Amount'), 2, func=gui_utils.currency_format)
        cell.set_property('weight-set', True)
        col.add_attribute(cell, 'weight', 6)
        col, cell = self.create_column(_('# Transactions'), 3)
        cell.set_property('weight-set', True)
        col.add_attribute(cell, 'weight', 6)
        self.create_column(_('First transaction'), 4, func=gui_utils.date_to_string)
        self.create_column(_('Last transaction'), 5, func=gui_utils.date_to_string)
        self._load_accounts()
        self.expand_all()

    def _load_accounts(self):
        accounts = account.get_all_accounts()
        for account_type, type_name in account.yield_account_types():
            iterator = self.model.append(None, [None, type_name, 0.0, 0, None, None, Pango.Weight.BOLD])
            ta_count = 0
            balance = 0
            for acc in accounts:
                if acc.type == account_type:
                    new_iter = self.model.append(iterator, [acc,
                               acc.name,
                               acc.balance,
                               len(acc.transactions),
                               acc.birthday,
                               acc.lastday,
                               Pango.Weight.NORMAL
                              ])
                    new_row = self.model[new_iter]
                    balance += acc.balance
                    ta_count += new_row[3]
                    self.model[iterator] = [None, type_name, balance, ta_count, None, None, Pango.Weight.BOLD]
