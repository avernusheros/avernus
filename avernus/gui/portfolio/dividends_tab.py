#!/usr/bin/env python
from avernus.gui import gui_utils, page, get_avernus_builder
from avernus.gui.portfolio import dividend_dialog
from gi.repository import Gtk


class DividendsTab(page.Page):

    OBJECT = 0
    POSITION = 1
    DATE = 2
    AMOUNT = 3
    TA_COSTS = 4
    TOTAL = 5
    DIVIDEND_YIELD = 6

    def __init__(self):
        page.Page.__init__(self)
        self.builder = get_avernus_builder()
        self.actiongroup = self.builder.get_object("dividend_actiongroup")
        self.treestore = self.builder.get_object("dividend_treestore")
        self.tree = self.builder.get_object("dividend_tree")
        self.tree.connect("draw", self.update_page)

        # date format
        cell = self.builder.get_object("cellrenderertext32")
        column = self.builder.get_object("treeviewcolumn32")
        column.set_cell_data_func(cell, gui_utils.date_to_string, self.DATE)
        self.treestore.set_sort_func(self.DATE, gui_utils.sort_by_datetime, self.DATE)
        # amount
        cell = self.builder.get_object("cellrenderertext33")
        column = self.builder.get_object("treeviewcolumn33")
        column.set_cell_data_func(cell, gui_utils.currency_format, self.AMOUNT)
        # transaction costs
        cell = self.builder.get_object("cellrenderertext34")
        column = self.builder.get_object("treeviewcolumn34")
        column.set_cell_data_func(cell, gui_utils.currency_format, self.TA_COSTS)
        # total
        cell = self.builder.get_object("cellrenderertext35")
        column = self.builder.get_object("treeviewcolumn35")
        column.set_cell_data_func(cell, gui_utils.currency_format, self.TOTAL)
        # dividend yield
        cell = self.builder.get_object("cellrenderertext36")
        column = self.builder.get_object("treeviewcolumn36")
        column.set_cell_data_func(cell, gui_utils.percent_format, self.DIVIDEND_YIELD)

    def set_portfolio(self, portfolio):
        self.portfolio = portfolio
        self.treestore.clear()
        for pos in self.portfolio:
            for div in pos.dividends:
                self.insert_dividend(div)
        self.update_page()

    def find_item(self, row0, itemtype=None):
        def search(rows):
            if not rows:
                return None
            for row in rows:
                if row[0] == row0 and (itemtype is None or itemtype == row[1].type):
                    return row
                result = search(row.iterchildren())
                if result:
                    return result
            return None
        return search(self.treestore)

    def get_selected_dividend(self):
        selection = self.tree.get_selection()
        if selection:
            model, selection_iter = selection.get_selected()
            if selection_iter and model:
                return model[selection_iter][0], selection_iter
        return None, None

    def on_add_dividend(self, widget):
        dlg = dividend_dialog.DividendDialog(self.portfolio, parent=self.tree.get_toplevel())
        if dlg.dividend:
            self.insert_dividend(dlg.dividend)
            self.update_page()

    def on_delete_dividend(self, widget):
        dividend, iterator = self.get_selected_dividend()
        if dividend:
            dlg = Gtk.MessageDialog(None,
                 Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.QUESTION,
                 Gtk.ButtonsType.OK_CANCEL,
                 _("Permanently delete dividend?"))
            response = dlg.run()
            dlg.destroy()
            if response == Gtk.ResponseType.OK:
                dividend.delete()
                self.treestore.remove(iterator)
                self.actiongroup.set_sensitive(False)

    def on_edit_dividend(self, widget):
        dividend = self.get_selected_dividend()[0]
        if dividend:
            dividend_dialog.DividendDialog(self.portfolio, tree=self, dividend=dividend, parent=self.tree.get_toplevel())

    def get_info(self):
        return [('# dividends', self.portfolio.get_dividends_count()),
                ('Sum', gui_utils.get_currency_format_from_float(self.portfolio.get_dividends_sum())),
                ('Last dividend', gui_utils.get_date_string(self.portfolio.date_of_last_dividend))]

    def insert_dividend(self, div):
        parent_row = self.find_item(div.position)
        if parent_row is None:
            parent = self.treestore.append(None, [div.position,
                            gui_utils.get_name_string(div.position.asset),
                            None,
                            div.price,
                            div.cost,
                            div.price - div.cost,
                            None
                            ])
        else:
            parent_row[self.AMOUNT] += div.price
            parent_row[self.TA_COSTS] += div.cost
            parent_row[self.TOTAL] += div.total
            parent_row[self.DIVIDEND_YIELD] = parent_row[self.TOTAL] / div.position.buy_value
            parent = parent_row.iter
        self.treestore.append(parent,
                [div,
                "",
                div.date,
                div.price,
                div.cost,
                div.total,
                div.dividend_yield
                ])

    def on_dividend_tree_cursor_changed(self, widget):
        obj = self.get_selected_dividend()[0]
        if obj.__class__.__name__ == "Dividend":
            self.actiongroup.set_sensitive(True)
        else:
            self.actiongroup.set_sensitive(False)
