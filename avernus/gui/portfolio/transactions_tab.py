#!/usr/bin/env python
from avernus.gui import gui_utils, page, get_avernus_builder
from avernus.gui.portfolio import buy_dialog, sell_dialog


class TransactionsTab(page.Page):

    DATE = 3
    SHARES = 4
    PRICE = 5
    TA_COSTS = 6
    TOTAL = 7

    def __init__(self):
        page.Page.__init__(self)
        self.builder = get_avernus_builder()
        self.treestore = self.builder.get_object("pf_transactions_treestore")
        self.tree = self.builder.get_object("pf_transactions_tree")
        self.tree.connect("draw", self.update_page)

        # date format
        cell = self.builder.get_object("cellrenderertext24")
        column = self.builder.get_object("treeviewcolumn24")
        column.set_cell_data_func(cell, gui_utils.date_to_string, self.DATE)
        self.treestore.set_sort_func(self.DATE, gui_utils.sort_by_datetime, self.DATE)
        # shares
        cell = self.builder.get_object("cellrenderertext27")
        column = self.builder.get_object("treeviewcolumn27")
        column.set_cell_data_func(cell, gui_utils.float_format, self.SHARES)
        # price
        cell = self.builder.get_object("cellrenderertext28")
        column = self.builder.get_object("treeviewcolumn28")
        column.set_cell_data_func(cell, gui_utils.currency_format, self.PRICE)
        # transaction costs
        cell = self.builder.get_object("cellrenderertext29")
        column = self.builder.get_object("treeviewcolumn29")
        column.set_cell_data_func(cell, gui_utils.currency_format, self.TA_COSTS)
        # total
        cell = self.builder.get_object("cellrenderertext30")
        column = self.builder.get_object("treeviewcolumn30")
        column.set_cell_data_func(cell, gui_utils.float_to_red_green_string_currency, self.TOTAL)

    def set_portfolio(self, portfolio):
        self.portfolio = portfolio
        self.treestore.clear()
        for position in self.portfolio:
            for ta in position.transactions:
                self.insert_transaction(ta)

    def insert_transaction(self, ta):
        self.treestore.append(None,
                    [ta,
                    str(ta),
                    gui_utils.get_name_string(ta.position.asset),
                    ta.date,
                    float(ta.position.quantity),
                    ta.price_per_share,
                    ta.cost,
                    ta.total
                    ])

    def get_info(self):
        return [('# transactions', self.portfolio.transaction_count),
                ('Last transaction', gui_utils.get_date_string(self.portfolio.date_of_last_transaction))]

    def on_edit_pf_transaction(self, widget):
        transaction, iterator = self.get_selected_transaction()
        toplevel = self.tree.get_toplevel()
        if transaction.type == "portfolio_sell_transaction":
            sell_dialog.SellDialog(transaction.position, transaction, parent=toplevel)
        elif transaction.type == "portfolio_buy_transaction":
            buy_dialog.BuyDialog(transaction.position.portfolio, transaction, parent=toplevel)

        # update treeview by removing and re-adding the transaction
        self.treestore.remove(iterator)
        self.insert_transaction(transaction)

    def on_pf_transactions_tree_button_press(self, widget, event):
        if event.button == 3:
            self.show_context_menu(event)

    def show_context_menu(self, event):
        transaction = self.get_selected_transaction()[0]
        if transaction:
            context_menu = self.builder.get_object("pf_transactions_contextmenu")
            context_menu.popup(None, None, None, None, event.button, event.time)

    def get_selected_transaction(self):
        selection = self.tree.get_selection()
        if selection:
            model, selection_iter = selection.get_selected()
            if selection_iter and model:
                return model[selection_iter][0], selection_iter
        return None, None

    def on_pf_transaction_row_activated(self, treeview, path, column):
        self.on_edit_pf_transaction(treeview)
