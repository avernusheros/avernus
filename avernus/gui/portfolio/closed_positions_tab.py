#!/usr/bin/env python

from gi.repository import Gtk
from avernus.gui import gui_utils, page
from avernus.controller import portfolio_controller


class ClosedPositionsTab(page.Page):

    def __init__(self, portfolio):
        page.Page.__init__(self)
        sw = Gtk.ScrolledWindow()
        self.add(sw)
        self.portfolio = portfolio
        self.closed_positions_tree = ClosedPositionsTree(portfolio)
        sw.set_property('hscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        sw.set_property('vscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        sw.add(self.closed_positions_tree)
        self.show_all()

    def show(self):
        self.closed_positions_tree.clear()
        self.closed_positions_tree.load_positions()
        self.update_page()

    def get_info(self):
        count = 0
        total = 0.0
        for pos in portfolio_controller.get_closed_positions(self.portfolio):
            count += 1
            total += pos.sell_total
        return [('# positions', count),
                ('Sum', gui_utils.get_currency_format_from_float(total))
                ]


class ClosedPositionsTree(gui_utils.Tree):

    def __init__(self, portfolio):
        self.portfolio = portfolio
        gui_utils.Tree.__init__(self)
        self.model = Gtk.ListStore(object, str, float, object, float, float, float, object, float, float, float, float, float)
        self.set_model(self.model)
        self.create_column('#', 2, func=gui_utils.float_format)
        self.create_column(_('Name'), 1)
        self.create_column(_('Buy date'), 3, func=gui_utils.date_to_string)
        self.model.set_sort_func(3, gui_utils.sort_by_time, 3)
        self.create_column(_('Buy price'), 4, func=gui_utils.currency_format)
        self.create_column(_('Expenses'), 5, func=gui_utils.currency_format)
        self.create_column(_('Total'), 6, func=gui_utils.currency_format)
        self.create_column(_('Sell date'), 7, func=gui_utils.date_to_string)
        self.model.set_sort_func(7, gui_utils.sort_by_time, 7)
        self.create_column(_('Sell price'), 8, func=gui_utils.currency_format)
        self.create_column(_('Expenses'), 9, func=gui_utils.currency_format)
        self.create_column(_('Total'), 10, func=gui_utils.currency_format)
        self.create_column(_('Gain'), 11, func=gui_utils.float_to_red_green_string_currency)
        self.create_column('%', 12, func=gui_utils.float_to_red_green_string_percent)

    def load_positions(self):
        for pos in portfolio_controller.get_closed_positions(self.portfolio):
            self.insert_position(pos)

    def insert_position(self, pos):
        self.model.append([pos,
                           gui_utils.get_name_string(pos.asset),
                           pos.quantity,
                           pos.buy_date,
                           pos.buy_price,
                           pos.buy_cost,
                           pos.buy_total,
                           pos.sell_date,
                           pos.sell_price,
                           pos.sell_cost,
                           pos.sell_total,
                           pos.gain,
                           pos.gain_percent
                           ])
