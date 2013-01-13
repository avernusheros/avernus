#!/usr/bin/env python
from avernus.controller import datasource_controller
from avernus.gui import gui_utils, progress_manager, page, get_avernus_builder
from avernus.gui.gui_utils import get_name_string
from avernus.gui.portfolio import buy_dialog, sell_dialog, dividend_dialog
from avernus.gui.portfolio.plot import ChartWindow
from avernus.gui.portfolio.position_dialog import PositionDialog
from avernus.objects import container, position
from gi.repository import Gdk, Gtk
import datetime
import sys
import logging

logger = logging.getLogger(__name__)


gain_thresholds = {
                   (-sys.maxint, -0.5): 'arrow_down',
                   (-0.5, -0.2): 'arrow_med_down',
                   (-0.2, 0.2): 'arrow_right',
                   (0.2, 0.5): 'arrow_med_up',
                   (0.5, sys.maxint): 'arrow_up'
                   }


def get_arrow_icon(perc):
    for (min_val, max_val), name in gain_thresholds.items():
        if min_val < perc and max_val >= perc:
            return name


def start_price_markup(column, cell, model, iterator, column_id):
    pos = model.get_value(iterator, 0)
    markup = "%s\n<small>%s</small>" % (gui_utils.get_currency_format_from_float(model.get_value(iterator, column_id)), gui_utils.get_date_string(pos.date))
    cell.set_property('markup', markup)


def quantity_markup(column, cell, model, iterator, column_id):
    pos = model.get_value(iterator, 0)
    markup = gui_utils.get_string_from_float(model.get_value(iterator, column_id))
    cell.set_property('markup', markup)


def current_price_markup(column, cell, model, iterator, column_id):
    try:
        asset = model.get_value(iterator, 0).asset
        # why? model.get_value(iterator, column_id)
        markup = "%s\n<small>%s</small>" % (gui_utils.get_currency_format_from_float(asset.price), gui_utils.get_datetime_string(asset.date))
        cell.set_property('markup', markup)
    except:
        pass


class PortfolioPositionsTab(page.Page):

    OBJECT = 0
    NAME = 1
    START = 2
    LAST_PRICE = 3
    CHANGE = 4
    GAIN = 5
    QUANTITY = 6
    BUY_VALUE = 7
    MKT_VALUE = 8
    DAYS_GAIN = 9
    GAIN_PERCENT = 10
    GAIN_ICON = 11
    CHANGE_PERCENT = 12
    TYPE = 13
    PF_PERCENT = 14
    GAIN_DIV = 15
    GAIN_DIV_PERCENT = 16
    ANNUAL_RETURN = 17
    IS_POSITION = 18

    def __init__(self):
        page.Page.__init__(self)
        self.builder = get_avernus_builder()
        self.treestore = self.builder.get_object("positions_treestore")
        self.widget = self.builder.get_object("positions_box")
        self.widget.connect("map", self.update_page)
        self.actiongroup = self.builder.get_object("position_actiongroup")
        self.portfolio = None

        # quantity
        cell = self.builder.get_object("cellrenderertext8")
        column = self.builder.get_object("treeviewcolumn7")
        column.set_cell_data_func(cell, quantity_markup, self.QUANTITY)
        # pf percent format
        cell = self.builder.get_object("cellrenderertext11")
        column = self.builder.get_object("treeviewcolumn11")
        column.set_cell_data_func(cell, gui_utils.percent_format, self.PF_PERCENT)
        # start price
        cell = self.builder.get_object("cellrenderertext12")
        column = self.builder.get_object("treeviewcolumn12")
        column.set_cell_data_func(cell, start_price_markup, self.START)
        # buy value
        cell = self.builder.get_object("cellrenderertext13")
        column = self.builder.get_object("treeviewcolumn13")
        column.set_cell_data_func(cell, gui_utils.currency_format, self.BUY_VALUE)
        # last price
        cell = self.builder.get_object("cellrenderertext14")
        column = self.builder.get_object("treeviewcolumn14")
        column.set_cell_data_func(cell, current_price_markup, self.LAST_PRICE)
        # change
        cell = self.builder.get_object("cellrenderertext15")
        column = self.builder.get_object("treeviewcolumn15")
        column.set_cell_data_func(cell, gui_utils.float_to_red_green_string_currency, self.CHANGE)
        # change %
        cell = self.builder.get_object("cellrenderertext16")
        column = self.builder.get_object("treeviewcolumn16")
        column.set_cell_data_func(cell, gui_utils.float_to_red_green_string_percent, self.CHANGE_PERCENT)
        # market value
        cell = self.builder.get_object("cellrenderertext17")
        column = self.builder.get_object("treeviewcolumn17")
        column.set_cell_data_func(cell, gui_utils.currency_format, self.MKT_VALUE)
        # gain
        cell = self.builder.get_object("cellrenderertext18")
        column = self.builder.get_object("treeviewcolumn18")
        column.set_cell_data_func(cell, gui_utils.float_to_red_green_string_currency, self.GAIN)
        # gain %
        cell = self.builder.get_object("cellrenderertext19")
        column = self.builder.get_object("treeviewcolumn19")
        column.set_cell_data_func(cell, gui_utils.float_to_red_green_string_percent, self.GAIN_PERCENT)
        # today
        cell = self.builder.get_object("cellrenderertext20")
        column = self.builder.get_object("treeviewcolumn20")
        column.set_cell_data_func(cell, gui_utils.float_to_red_green_string_currency, self.DAYS_GAIN)
        # gain incl dividends
        cell = self.builder.get_object("cellrenderertext21")
        column = self.builder.get_object("treeviewcolumn21")
        column.set_cell_data_func(cell, gui_utils.float_to_red_green_string_currency, self.GAIN_DIV)
        # gain incl dividends percent
        cell = self.builder.get_object("cellrenderertext22")
        column = self.builder.get_object("treeviewcolumn22")
        column.set_cell_data_func(cell, gui_utils.float_to_red_green_string_percent, self.GAIN_DIV_PERCENT)
        # annual return
        cell = self.builder.get_object("cellrenderertext23")
        column = self.builder.get_object("treeviewcolumn23")
        column.set_cell_data_func(cell, gui_utils.percent_format, self.ANNUAL_RETURN)

    def set_portfolio(self, portfolio):
        # clear
        self.treestore.clear()
        if self.portfolio:
            self.portfolio.disconnect(self.signal_id)
        # set new portfolio
        self.portfolio = portfolio
        self.signal_id = portfolio.connect('position_added', self.on_position_added)
        # load_positions
        for pos in portfolio:
            self.insert_position(pos)
        # auto-update assets
        if not portfolio.last_update or datetime.datetime.now() - portfolio.last_update > datetime.timedelta(minutes=5):
            self.on_update_portfolio_positions()
        self.update_page()

    def insert_position(self, position):
        if position.quantity != 0:
            tree_iter = self.treestore.append(None, self.get_row_position(position))
            sold_quantity = sum([pos.quantity for pos in position.get_sell_transactions()])
            buy_transactions = position.get_buy_transactions()
            if len(buy_transactions) > 1:
                for buy in buy_transactions:
                    if sold_quantity >= buy.quantity:
                        sold_quantity -= buy.quantity
                    else:
                        if sold_quantity > 0:
                            # FIXME parts are already sold, show only the remaining shares
                            pass
                        self.treestore.append(tree_iter, self.get_row_transaction(buy))
            position.asset.connect("updated", self.on_asset_updated)

    def get_row_position(self, position):
        asset = position.asset
        gain = position.gain
        gain_div = position.gain_with_dividends
        gain_icon = get_arrow_icon(gain[1])
        c_change = position.current_change
        return [position,
               get_name_string(asset),
               position.price_per_share,
               asset.price,
               c_change[0],
               gain[0],
               position.quantity,
               position.buy_value,
               position.current_value,
               position.days_gain,
               float(gain[1]),
               gain_icon,
               float(c_change[1]),
               datasource_controller.ASSET_TYPES[type(position.asset)],
               self.portfolio.get_fraction(position),
               gain_div[0],
               float(gain_div[1]),
               position.get_annual_return(),
               True
               ]

    def get_row_transaction(self, transaction):
        asset = transaction.position.asset
        gain = transaction.gain
        gain_icon = get_arrow_icon(gain[1])
        c_change = transaction.current_change
        return [transaction,
               get_name_string(asset),
               transaction.price_per_share,
               asset.price,
               c_change[0],
               gain[0],
               transaction.quantity,
               - transaction.total,
               transaction.current_value,
               transaction.days_gain,
               float(gain[1]),
               gain_icon,
               float(c_change[1]),
               "",
               self.portfolio.get_fraction(transaction),
               0.0,
               0.0,
               0.0,
               False,
               ]

    def _move_position(self, position, parent=None):
        row = self.find_position(position)
        if row:
            self.treestore.remove(row.iter)
            self.treestore.append(parent, self._get_row(position, parent != None))

    def find_position(self, pos):
        # search recursiv
        def search(rows):
            if not rows:
                return None
            for row in rows:
                if row[self.OBJECT] == pos:
                    return row
                result = search(row.iterchildren())
                if result:
                    return result
            return None
        return search(self.treestore)

    def find_position_from_asset(self, asset):
        # search recursiv
        def search(rows):
            if not rows:
                return None
            for row in rows:
                if isinstance(row[self.OBJECT], position.PortfolioPosition):
                    if row[self.OBJECT].asset == asset:
                        return row
                result = search(row.iterchildren())
                if result:
                    return result
            return None
        return search(self.treestore)

    def get_info(self):
        if not self.portfolio:
            return []
        change, percent = self.portfolio.current_change
        change_text = gui_utils.get_string_from_float(percent) + '%' + ' | ' + gui_utils.get_currency_format_from_float(change)
        o_change, o_percent = self.portfolio.overall_change
        o_change_text = gui_utils.get_string_from_float(o_percent) + '%' + ' | ' + gui_utils.get_currency_format_from_float(o_change)
        return [(_('Day\'s gain'), gui_utils.get_green_red_string(change, change_text)),
                (_('Overall gain'), gui_utils.get_green_red_string(o_change, o_change_text)),
                ('Investments', gui_utils.get_currency_format_from_float(self.portfolio.get_current_value())),
                ('# positions', self.portfolio.active_positions_count),
                ('Last update', gui_utils.datetime_format(self.portfolio.last_update, False))
                ]

    def on_asset_updated(self, asset):
        item = self.find_position_from_asset(asset)
        if item:
            tree_iter = item.iter
            self.treestore[tree_iter] = self.get_row_position(self.treestore[tree_iter][self.OBJECT])
            child_iter = self.treestore.iter_children(tree_iter)
            if child_iter:
                self.treestore[child_iter] = self.get_row_transaction(self.treestore[child_iter][self.OBJECT])
                while self.treestore.iter_next(child_iter) != None:
                    child_iter = self.treestore.iter_next(child_iter)
                    self.treestore[child_iter] = self.get_row_transaction(self.treestore[child_iter][self.OBJECT])
        else:
            logger.error("update from unknown asset")

    def update_position_after_edit(self, pos, iterator=None):
        if iterator is None:
            iterator = self.find_position(pos).iterator
        self.treestore[iterator] = self.get_row_position(pos)

    def on_update_portfolio_positions(self, *args):
        progress_manager.add_task(datasource_controller.update_positions,
                            self.portfolio,
                            _('updating assets...'),
                            self.update)

    def on_positionstab_add_position(self, widget):
        buy_dialog.BuyDialog(self.portfolio, parent=self.widget.get_toplevel())

    def on_delete_position(self, widget):
        position, iterator = self.selected_item
        dlg = Gtk.MessageDialog(None,
             Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.QUESTION,
                Gtk.ButtonsType.OK_CANCEL, _("This will delete the selected position and all related data. Are you sure?"))
        response = dlg.run()
        dlg.destroy()
        if response == Gtk.ResponseType.OK:
            position.delete()
            self.treestore.remove(iterator)

    def on_sell_position(self, widget):
        position, iterator = self.selected_item
        d = sell_dialog.SellDialog(position, parent=self.widget.get_toplevel())
        if d.response == Gtk.ResponseType.ACCEPT:
            self.treestore.remove(iterator)
            if position.quantity != 0.0:
                self.insert_position(position)

    def on_add_dividend_for_position(self, widget):
        if self.selected_item is not None:
            dividend_dialog.DividendDialog(pf=self.portfolio, position=self.selected_item[0], parent=self.widget.get_toplevel())
        else:
            dividend_dialog.DividendDialog(pf=self.portfolio, parent=self.widget.get_toplevel())

    def on_chart_position(self, widget):
        if self.selected_item:
            ChartWindow(self.selected_item[0].asset)

    def on_edit_position(self, widget):
        if self.selected_item:
            position, iterator = self.selected_item
            PositionDialog(position, self.widget.get_toplevel())
            self.update_position_after_edit(position, iterator)

    def update(self):
        for row in self.treestore:
            item = row[self.OBJECT]
            row[self.PF_PERCENT] = self.portfolio.get_fraction(item)
        self.update_page()

    def on_position_added(self, portfolio, position):
        self.insert_position(position)
        position.asset.connect("updated", self.on_asset_updated)
        # update portfolio fractions
        self.update()

    def on_positionstree_cursor_changed(self, widget):
        # Get the current selection in the Gtk.TreeView
        selection = widget.get_selection()
        if selection:
            # Get the selection iter
            treestore, selection_iter = selection.get_selected()
            if selection_iter and treestore:
                # Something is selected so get the object
                obj = treestore.get_value(selection_iter, self.OBJECT)
                self.selected_item = obj, selection_iter
                self.actiongroup.set_sensitive(True)
                return
        self.actiongroup.set_sensitive(False)

    def on_positionstree_button_press(self, widget, event):
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            self.on_edit_position(widget)
            return False
        if event.button == 3:
            if self.selected_item is not None:
                self.show_context_menu(event)

    def show_context_menu(self, event):
        context_menu = self.builder.get_object("position_contextmenu")
        move_menu = self.builder.get_object("move_menu")
        all_portfolios = container.get_all_portfolios()
        if len(all_portfolios) == 1:
            move_menu.set_visible(False)
        else:
            move_menu.set_visible(True)
            menu = Gtk.Menu()
            move_menu.set_submenu(menu)
            for pf in all_portfolios:
                if pf != self.portfolio:
                    item = Gtk.MenuItem(label=pf.name)
                    item.connect("activate", self.on_move_position, pf)
                    menu.append(item)
            move_menu.show_all()
        context_menu.popup(None, None, None, None, event.button, event.time)

    def on_move_position(self, widget, new_portfolio):
        position, iterator = self.selected_item
        position.portfolio = new_portfolio
        self.treestore.remove(iterator)
