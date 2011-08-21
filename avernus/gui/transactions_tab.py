#!/usr/bin/env python

import gtk
from avernus import pubsub
from avernus.gui import gui_utils, dialogs
from avernus.gui.gui_utils import Tree, get_datetime_string
import avernus.objects


class TransactionsTab(gtk.ScrolledWindow):
    def __init__(self, item):
        gtk.ScrolledWindow.__init__(self)
        self.transactions_tree = TransactionsTree(item)
        self.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        self.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        self.add(self.transactions_tree)
        self.show_all()

    def show(self):
        self.transactions_tree.clear()
        self.transactions_tree.load_transactions()


class TransactionsTree(Tree):

    def __init__(self, portfolio):
        self.portfolio = portfolio
        Tree.__init__(self)
        self.model = gtk.TreeStore(object,str, str, object,float, float, float, float)
        self.set_model(self.model)

        self.create_column(_('Date'), 3, func=gui_utils.date_to_string)
        self.model.set_sort_func(3, gui_utils.sort_by_time, 3)
        self.create_column(_('Type'), 1)
        self.create_column(_('Name'), 2)
        self.create_column(_('Shares'), 4, func=gui_utils.float_format)
        self.create_column(_('Price'), 5, func=gui_utils.currency_format)
        self.create_column(_('Transaction Costs'), 6, func=gui_utils.currency_format)
        self.create_column(_('Total'), 7, func=gui_utils.float_to_red_green_string_currency)

        self.actiongroup = gtk.ActionGroup('portfolio_transactions')
        self.actiongroup.add_actions([
                ('edit' ,  gtk.STOCK_EDIT, 'edit transaction',   None, _('Edit selected transaction'),   self.on_edit),
                                ])
        pubsub.subscribe('transaction.added', self.on_transaction_created)
        self.connect('button_press_event', self.on_button_press)

    def load_transactions(self):
        for position in self.portfolio:
            for ta in position.transactions:
                self.insert_transaction(ta)

    def on_transaction_created(self, ta):
        if ta.position.portfolio.id == self.portfolio.id:
            self.insert_transaction(ta)

    def on_button_press(self, widget, event):
        if event.button == 3:
            self.show_context_menu(event)

    def on_edit(self, widget):
        transaction, iter = self.get_selected_item()
        if transaction.type == 0: #SELL
            dialogs.SellDialog(transaction.position, transaction)
        elif transaction.type == 1: #Buy
            dialogs.BuyDialog(transaction.position.portfolio, transaction)
        else:
            print "TODO edit transaction"

    def insert_transaction(self, ta):
        model = self.get_model()
        if model:
            model.append(None, [ta, ta.type_string, gui_utils.get_name_string(ta.position.stock), ta.date.date(), ta.quantity, ta.price, ta.costs, ta.total])

    def show_context_menu(self, event):
        transaction, iter = self.get_selected_item()
        if transaction:
            context_menu = gui_utils.ContextMenu()
            for action in self.actiongroup.list_actions():
                context_menu.add(action.create_menu_item())
            context_menu.show(event)
