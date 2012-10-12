#!/usr/bin/env python
from avernus.gui import gui_utils, page
from avernus.gui.gui_utils import Tree
from avernus.gui.portfolio import buy_dialog, sell_dialog
from gi.repository import Gtk


class TransactionsTab(page.Page):

    def __init__(self, portfolio):
        page.Page.__init__(self)
        self.portfolio = portfolio
        sw = Gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        sw.set_property('vscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        self.transactions_tree = TransactionsTree(self.portfolio)
        sw.add(self.transactions_tree)
        self.pack_start(sw, True, True, 0)
        self.show_all()

    def show(self):
        self.transactions_tree.clear()
        self.transactions_tree.load_transactions()
        self.update_page()

    def get_info(self):
        return [('# transactions', self.portfolio.transaction_count),
                ('Last transaction', gui_utils.get_date_string(self.portfolio.date_of_last_transaction))]


class TransactionsTree(Tree):

    def __init__(self, portfolio):
        self.portfolio = portfolio
        Tree.__init__(self)
        self.model = Gtk.TreeStore(object, str, str, object, float, float, float, float)
        self.set_model(self.model)

        self.create_column(_('Date'), 3, func=gui_utils.date_to_string)
        self.model.set_sort_func(3, gui_utils.sort_by_time, 3)
        self.create_column(_('Type'), 1)
        self.create_column(_('Name'), 2)
        self.create_column(_('Shares'), 4, func=gui_utils.float_format)
        self.create_column(_('Price'), 5, func=gui_utils.currency_format)
        self.create_column(_('Transaction Costs'), 6, func=gui_utils.currency_format)
        self.create_column(_('Total'), 7, func=gui_utils.float_to_red_green_string_currency)

        self.model.set_sort_column_id(3, Gtk.SortType.ASCENDING)

        self.actiongroup = Gtk.ActionGroup('portfolio_transactions')
        self.actiongroup.add_actions([
                ('edit' , Gtk.STOCK_EDIT, 'edit transaction', None, _('Edit selected transaction'), self.on_edit),
                                ])
        self.connect('button_press_event', self.on_button_press)
        self.connect("row-activated", self.on_row_activated)

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

    def on_row_activated(self, treeview, path, column):
        self.on_edit(treeview)

    def on_edit(self, widget, data=None):
        transaction, iter = self.get_selected_item()
        if transaction.type == "portfolio_sell_transaction":
            sell_dialog.SellDialog(transaction.position, transaction, parent=self.get_toplevel())
        elif transaction.type == "portfolio_buy_transaction":
            buy_dialog.BuyDialog(transaction.position.portfolio, transaction, parent=self.get_toplevel())

        #update treeview by removing and re-adding the transaction
        self.model.remove(iter)
        self.insert_transaction(transaction)

    def insert_transaction(self, ta):
        self.model.append(None,
                    [ta,
                    str(ta),
                    gui_utils.get_name_string(ta.position.asset),
                    ta.date,
                    float(ta.position.quantity),
                    ta.price,
                    ta.cost,
                    ta.total
                    ])

    def show_context_menu(self, event):
        transaction, iter = self.get_selected_item()
        if transaction:
            self.context_menu = gui_utils.ContextMenu()
            for action in self.actiongroup.list_actions():
                self.context_menu.add(action.create_menu_item())
            self.context_menu.popup(None, None, None, None, event.button, event.time)
