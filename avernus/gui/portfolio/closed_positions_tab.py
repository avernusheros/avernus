#!/usr/bin/env python
from avernus.gui import gui_utils, page, get_avernus_builder
from gi.repository import Gtk


class ClosedPositionsTab(page.Page):

    def __init__(self):
        page.Page.__init__(self)
        builder = get_avernus_builder()
        sw = builder.get_object("closed_positions_sw")
        self.closed_positions_tree = ClosedPositionsTree()
        self.closed_positions_tree.connect("draw", self.update_page)
        sw.add(self.closed_positions_tree)
        sw.show_all()

    def set_portfolio(self, portfolio):
        self.portfolio = portfolio
        self.closed_positions_tree.clear()
        self.closed_positions_tree.load_positions(portfolio)
        self.update_page()

    def get_info(self):
        count = 0
        total = 0.0
        for pos in self.portfolio.get_closed_positions():
            count += 1
            total += pos.sell_total
        return [('# positions', count),
                ('Sum', gui_utils.get_currency_format_from_float(total))
                ]


class ClosedPositionsTree(gui_utils.Tree):

    def __init__(self):
        gui_utils.Tree.__init__(self)
        self.model = Gtk.ListStore(object, str, float, object, float, float, float, object, float, float, float, float, float)
        self.set_model(self.model)
        self.create_column('#', 2, func=gui_utils.float_format)
        self.create_column(_('Name'), 1)
        self.create_column(_('Buy date'), 3, func=gui_utils.date_to_string)
        self.model.set_sort_func(3, gui_utils.sort_by_datetime, 3)
        self.create_column(_('Buy price'), 4, func=gui_utils.currency_format)
        self.create_column(_('Expenses'), 5, func=gui_utils.currency_format)
        self.create_column(_('Total'), 6, func=gui_utils.currency_format)
        self.create_column(_('Sell date'), 7, func=gui_utils.date_to_string)
        self.model.set_sort_func(7, gui_utils.sort_by_datetime, 7)
        self.create_column(_('Sell price'), 8, func=gui_utils.currency_format)
        self.create_column(_('Expenses'), 9, func=gui_utils.currency_format)
        self.create_column(_('Total'), 10, func=gui_utils.currency_format)
        self.create_column(_('Gain'), 11, func=gui_utils.float_to_red_green_string_currency)
        self.create_column('%', 12, func=gui_utils.float_to_red_green_string_percent)

    def load_positions(self, portfolio):
        for pos in portfolio.get_closed_positions():
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
