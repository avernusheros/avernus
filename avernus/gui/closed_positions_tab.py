#!/usr/bin/env python

from gi.repository import Gtk
from avernus import pubsub
from avernus.gui import gui_utils
from avernus.controller import controller


class ClosedPositionsTab(Gtk.ScrolledWindow):
    
    def __init__(self, item):
        Gtk.ScrolledWindow.__init__(self)
        self.closed_positions_tree = ClosedPositionsTree(item)
        self.set_property('hscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        self.set_property('vscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        self.add(self.closed_positions_tree)
        self.show_all()

    def show(self):
        self.closed_positions_tree.clear()
        self.closed_positions_tree.load_positions()


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
        self.create_column('%', 12, func=gui_utils.float_to_red_green_string)
        
    def load_positions(self):
        for pos in self.portfolio.closed_positions:
            self.insert_position(pos)

    def insert_position(self, pos):
        self.model.append([pos, 
                           gui_utils.get_name_string(pos.stock),
                           float(pos.quantity),
                           pos.buy_date,
                           pos.buy_price,
                           pos.buy_costs,
                           pos.buy_total,
                           pos.sell_date,
                           pos.sell_price,
                           pos.sell_costs,
                           pos.sell_total,
                           pos.gain,
                           pos.gain_percent])
