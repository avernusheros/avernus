#!/usr/bin/env python
from avernus.controller import datasource_controller
from avernus.gui import gui_utils, progress_manager, page, threads, get_avernus_builder
from avernus.gui.gui_utils import get_name_string
from avernus.gui.portfolio import buy_dialog, sell_dialog, dividend_dialog
from avernus.gui.portfolio.plot import ChartWindow
from avernus.gui.portfolio.position_dialog import PositionDialog
from avernus.objects import container
from avernus.objects import position as position_model
from gi.repository import Gdk, Gtk
import datetime
import sys


# FIXME
gain_thresholds = {
                   (-sys.maxint, -0.5): 'arrow_down',
                   (-0.5, -0.2): 'arrow_med_down',
                   (-0.2, 0.2): 'arrow_right',
                   (0.2, 0.5): 'arrow_med_up',
                   (0.5, sys.maxint): 'arrow_up'
                   }


def get_arrow_icon(perc):
    for (min_val, max_val), name in gain_thresholds.items():
        if min_val <= perc and max_val >= perc:
            return name


def start_price_markup(column, cell, model, iterator, user_data):
    pos = model.get_value(iterator, 0)
    markup = "%s\n<small>%s</small>" % (gui_utils.get_currency_format_from_float(model.get_value(iterator, user_data)), gui_utils.get_date_string(pos.date))
    if isinstance(pos, position_model.MetaPosition):
        markup = unichr(8709) + " " + markup
    cell.set_property('markup', markup)


def quantity_markup(column, cell, model, iterator, user_data):
    pos = model.get_value(iterator, 0)
    markup = gui_utils.get_string_from_float(model.get_value(iterator, 6))
    if isinstance(pos, position_model.MetaPosition):
        markup = unichr(8721) + " " + markup
    cell.set_property('markup', markup)


def current_price_markup(column, cell, model, iterator, user_data):
    asset = model.get_value(iterator, 0).asset
    markup = "%s\n<small>%s</small>" % (gui_utils.get_currency_format_from_float(model.get_value(iterator, user_data)), gui_utils.get_datetime_string(asset.date))
    cell.set_property('markup', markup)


class PortfolioPositionsTab(page.Page):

    """
    obj: 0,
    name: 1,
    start: 2,
    last_price: 3,
    change: 4,
    gain: 5,
    shares: 6,
    buy_value: 7,
    mkt_value: 8,
    days_gain: 9,
    gain_percent: 10,
    gain_icon: 11,
    change_percent: 12,
    type: 13,
    pf_percent: 14,
    gain_div: 15,
    gain_div_percent: 16,
    annual_return: 17,
    """

    def __init__(self):
        page.Page.__init__(self)
        self.builder = get_avernus_builder()
        self.treestore = self.builder.get_object("positions_treestore")
        self.widget = self.builder.get_object("portfolio_notebook")
        self.widget.connect("draw", self.update_page)
        self.actiongroup = self.builder.get_object("position_actiongroup")
        self.portfolio = None

        # quantity
        cell = self.builder.get_object("cellrenderertext8")
        column = self.builder.get_object("treeviewcolumn7")
        column.set_cell_data_func(cell, quantity_markup)
        # pf percent format
        cell = self.builder.get_object("cellrenderertext11")
        column = self.builder.get_object("treeviewcolumn11")
        column.set_cell_data_func(cell, gui_utils.percent_format, 14)
        # start price
        cell = self.builder.get_object("cellrenderertext12")
        column = self.builder.get_object("treeviewcolumn12")
        column.set_cell_data_func(cell, start_price_markup, 2)
        # buy value
        cell = self.builder.get_object("cellrenderertext13")
        column = self.builder.get_object("treeviewcolumn13")
        column.set_cell_data_func(cell, gui_utils.currency_format, 7)
        # last price
        cell = self.builder.get_object("cellrenderertext14")
        column = self.builder.get_object("treeviewcolumn14")
        column.set_cell_data_func(cell, current_price_markup, 3)
        # change
        cell = self.builder.get_object("cellrenderertext15")
        column = self.builder.get_object("treeviewcolumn15")
        column.set_cell_data_func(cell, gui_utils.float_to_red_green_string_currency, 4)
        # change %
        cell = self.builder.get_object("cellrenderertext16")
        column = self.builder.get_object("treeviewcolumn16")
        column.set_cell_data_func(cell, gui_utils.float_to_red_green_string_percent, 12)
        # market value
        cell = self.builder.get_object("cellrenderertext17")
        column = self.builder.get_object("treeviewcolumn17")
        column.set_cell_data_func(cell, gui_utils.currency_format, 8)
        # gain
        cell = self.builder.get_object("cellrenderertext18")
        column = self.builder.get_object("treeviewcolumn18")
        column.set_cell_data_func(cell, gui_utils.float_to_red_green_string_currency, 5)
        # gain %
        cell = self.builder.get_object("cellrenderertext19")
        column = self.builder.get_object("treeviewcolumn19")
        column.set_cell_data_func(cell, gui_utils.float_to_red_green_string_percent, 10)
        # today
        cell = self.builder.get_object("cellrenderertext20")
        column = self.builder.get_object("treeviewcolumn20")
        column.set_cell_data_func(cell, gui_utils.float_to_red_green_string_currency, 9)
        # gain incl dividends
        cell = self.builder.get_object("cellrenderertext21")
        column = self.builder.get_object("treeviewcolumn21")
        column.set_cell_data_func(cell, gui_utils.float_to_red_green_string_currency, 15)
        # gain incl dividends percent
        cell = self.builder.get_object("cellrenderertext22")
        column = self.builder.get_object("treeviewcolumn22")
        column.set_cell_data_func(cell, gui_utils.float_to_red_green_string_percent, 16)
        # annual return
        cell = self.builder.get_object("cellrenderertext23")
        column = self.builder.get_object("treeviewcolumn23")
        column.set_cell_data_func(cell, gui_utils.percent_format, 17)

    def set_portfolio(self, portfolio):
        # clear
        self.treestore.clear()
        self.asset_cache = {}
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
            tree_iter = None
            if position.asset.id in self.asset_cache:
                if isinstance(self.asset_cache[position.asset.id], position_model.MetaPosition):
                    mp = self.asset_cache[position.asset.id]
                    tree_iter = self.find_position(mp).iter
                else:
                    p1 = self.asset_cache[position.asset.id]
                    mp = position_model.MetaPosition(p1)
                    tree_iter = self.treestore.append(None, self._get_row(mp))
                    self.asset_cache[position.asset.id] = mp
                    self._move_position(p1, tree_iter)
                mp.add_position(position)
                self.update_position_after_edit(mp, tree_iter)
            else:
                self.asset_cache[position.asset.id] = position
                position.asset.connect("updated", self.on_asset_updated)
            self.treestore.append(tree_iter, self._get_row(position, tree_iter != None))

    def _get_row(self, position, child=False):
        asset = position.asset
        gain = position.gain
        gain_div = position.gain_with_dividends
        gain_icon = get_arrow_icon(gain[1])
        c_change = position.current_change
        ret = [position,
               get_name_string(asset),
               position.price,
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
               position.get_annual_return()
               ]
        if child:
            ret[1] = ""
        return ret

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
                if row[0] == pos:
                    return row
                result = search(row.iterchildren())
                if result:
                    return result
            return None
        return search(self.treestore)

    def show(self):
        self.update_page()

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
                ('# positions', len(self.portfolio.positions)),
                ('Last update', gui_utils.datetime_format(self.portfolio.last_update, False))
                ]

    def on_asset_updated(self, asset):
        position = self.asset_cache[asset.id]
        tree_iter = self.find_position(position).iter
        if isinstance(position, position_model.MetaPosition):
            position.recalculate()
            self.treestore[tree_iter] = self._get_row(self.treestore[tree_iter][0])
            child_iter = self.treestore.iter_children(tree_iter)
            self.treestore[child_iter] = self._get_row(self.treestore[child_iter][0], True)
            while self.treestore.iter_next(child_iter) != None:
                child_iter = self.treestore.iter_next(child_iter)
                self.treestore[child_iter] = self._get_row(self.treestore[child_iter][0], True)
        else:
            self.treestore[tree_iter] = self._get_row(position)

    def update_position_after_edit(self, pos, iterator=None):
        if iterator is None:
            iterator = self.find_position(pos).iterator
        self.treestore[iterator] = self._get_row(pos)
        if not isinstance(pos, position_model.MetaPosition) and pos.asset.id in self.asset_cache:
            item = self.asset_cache[pos.asset.id]
            if isinstance(item, position_model.MetaPosition):
                item.recalculate()
                self.update_position_after_edit(item)

    def on_update_portfolio_positions(self, *args):
        def finished_cb():
            progress_manager.remove_monitor(self.portfolio.id)
            self.update()
        m = progress_manager.add_monitor(self.portfolio.id, _('updating assets...'),
                                         Gtk.STOCK_REFRESH)
        threads.GeneratorTask(datasource_controller.update_positions,
                              m.progress_update,
                              complete_callback=finished_cb,
                              args=(self.portfolio)).start()

    def on_add_position(self, widget):
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

    def on_add_dividend(self, widget):
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
            item = row[0]
            row[14] = self.portfolio.get_fraction(item)
        self.update_page()

    def on_position_added(self, portfolio, position):
        self.insert_position(position)
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
                obj = treestore.get_value(selection_iter, 0)
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
