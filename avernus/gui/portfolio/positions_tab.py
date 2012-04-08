#!/usr/bin/env python

from gi.repository import Gtk
from gi.repository import Gdk
import sys
from avernus import pubsub
from avernus.gui.portfolio.plot import ChartWindow
from avernus.gui.portfolio import dialogs
from avernus.gui.portfolio.position_dialog import PositionDialog
from avernus.gui.gui_utils import Tree, get_name_string
from avernus.gui import gui_utils, progress_manager, page, threads
from avernus.objects.position import MetaPosition
from avernus.controller import controller
from avernus.controller import portfolio_controller as pfctrl


gain_thresholds = {
                   (-sys.maxint, -0.5):'arrow_down',
                   (-0.5, -0.2):'arrow_med_down',
                   (-0.2, 0.2):'arrow_right',
                   (0.2, 0.5):'arrow_med_up',
                   (0.5, sys.maxint):'arrow_up'
                   }


def get_arrow_icon(perc):
    for (min_val, max_val), name in gain_thresholds.items():
        if min_val <= perc and max_val >= perc:
            return name


def start_price_markup(column, cell, model, iter, user_data):
    pos = model.get_value(iter, 0)
    markup = gui_utils.get_currency_format_from_float(model.get_value(iter, user_data)) + '\n' + '<small>' + gui_utils.get_date_string(pos.date.date()) + '</small>'
    if isinstance(pos, MetaPosition):
        markup = unichr(8709) + " " + markup
    cell.set_property('markup', markup)


def current_price_markup(column, cell, model, iter, user_data):
    stock = model.get_value(iter, 0).stock
    markup = gui_utils.get_currency_format_from_float(model.get_value(iter, user_data)) + '\n' + '<small>' + gui_utils.get_datetime_string(stock.date) + '</small>'
    cell.set_property('markup', markup)


class PositionsTree(Tree):

    COLS = {'obj':0,
         'name':1,
         'start':2,
         'last_price':3,
         'change':4,
         'gain':5,
         'shares':6,
         'buy_value':7,
         'mkt_value':8,
         'days_gain':9,
         'gain_percent':10,
         'gain_icon':11,
         'change_percent':12,
         'type': 13,
         'pf_percent': 14
          }

    def __init__(self, container, actiongroup):
        self.container = container
        self.actiongroup = actiongroup
        Tree.__init__(self)

        self._init_widgets()
        self.set_rules_hint(True)
        self.stock_cache = {}
        self.load_positions()
        self._connect_signals()
        self.selected_item = None

    def _connect_signals(self):
        self.connect('button-press-event', self.on_button_press_event)
        self.connect('cursor_changed', self.on_cursor_changed)
        pubsub.subscribe('stock.updated', self.on_stocks_updated)

    def on_button_press_event(self, widget, event):
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            self.on_edit(widget)
            return False
        if event.button == 3:
            if self.selected_item is not None:
                self.show_context_menu(event)

    def show_context_menu(self, event):
        self.context_menu = gui_utils.ContextMenu()
        for action in self.actiongroup.list_actions():
            self.context_menu.add(action.create_menu_item())

        all_portfolios = pfctrl.getAllPortfolio()
        if len(all_portfolios) > 1:
            self.context_menu.add_item('----')

            #Move to another portfolio
            item = Gtk.MenuItem(label=_("Move"))
            self.context_menu.add(item)
            menu = Gtk.Menu()
            item.set_submenu(menu)
            for pf in all_portfolios:
                if pf != self.container:
                    item = Gtk.MenuItem(label=pf.name)
                    item.connect("activate", self.on_move_position, pf)
                    menu.append(item)
        self.context_menu.popup(None, None, None, None, event.button, event.time)

    def on_move_position(self, widget, new_portfolio):
        position, iterator = self.selected_item
        position.portfolio = new_portfolio

    def load_positions(self):
        for pos in self.container:
            self.insert_position(pos)

    def on_update_positions(self, *args):
        def finished_cb():
            progress_manager.remove_monitor(555)
        m = progress_manager.add_monitor(555, _('updating stocks...'), Gtk.STOCK_REFRESH)
        threads.GeneratorTask(self.container.update_positions, m.progress_update, complete_callback=finished_cb).start()

    def on_chart(self, widget, user_data=None):
        ChartWindow(self.selected_item[0].stock)

    def on_edit(self, widget, user_data=None):
        position, iter = self.selected_item
        PositionDialog(position, self.get_toplevel())
        self.update_position_after_edit(position, iter)

    def update_position_after_edit(self, pos, iter=None):
        if iter is None:
            iter = self.find_position(pos).iter
        col = 0
        for item in self._get_row(pos):
            self.model.set_value(iter, col, item)
            col += 1
        if not isinstance(pos, MetaPosition) and pos.stock.id in self.stock_cache:
            item = self.stock_cache[pos.stock.id]
            if isinstance(item, MetaPosition):
                item.recalculate()
                self.update_position_after_edit(item)

    def on_cursor_changed(self, widget):
        #Get the current selection in the Gtk.TreeView
        selection = widget.get_selection()
        # Get the selection iter
        treestore, selection_iter = selection.get_selected()
        if (selection_iter and treestore):
            #Something is selected so get the object
            obj = treestore.get_value(selection_iter, 0)
            self.selected_item = obj, selection_iter
            self.on_select(obj)
            return
        self.on_unselect()

    def _move_position(self, position, parent=None):
        row = self.find_position(position)
        if row:
            self.model.remove(row.iter)
            self.model.append(parent, self._get_row(position))

    def find_position(self, pos):
        #search recursiv
        def search(rows):
            if not rows: return None
            for row in rows:
                if row[0] == pos:
                    return row
                result = search(row.iterchildren())
                if result: return result
            return None
        return search(self.model)


class PortfolioPositionsTree(PositionsTree):

    def __init__(self, portfolio, actiongroup):
        PositionsTree.__init__(self, portfolio, actiongroup)
        self.actiongroup.add_actions([
                ('add', Gtk.STOCK_ADD, 'add', None, _('Add new position'), self.on_add),
                ('edit' , Gtk.STOCK_EDIT, 'edit', None, _('Edit selected position'), self.on_edit),
                ('sell', Gtk.STOCK_DELETE, 'sell', None, _('Sell selected position'), self.on_sell),
                ('remove', Gtk.STOCK_DELETE, 'remove', None, _('Delete selected position'), self.on_remove),
                ('chart', None, 'chart', None, _('Chart selected position'), self.on_chart),
                ('dividend', None, 'dividend', None, _('Add dividend payment'), self.on_dividend),
                ('update', Gtk.STOCK_REFRESH, 'update', None, _('Update positions'), self.on_update_positions)
                                ])
        self.actiongroup.get_action('chart').set_icon_name('avernus')
        accelgroup = Gtk.AccelGroup()
        for action in self.actiongroup.list_actions():
            action.set_accel_group(accelgroup)

    def _init_widgets(self):
        self.model = Gtk.TreeStore(object, str, float, float, float, float, str, float, float, float, float, str, float, str, float)
        self.set_model(self.model)

        self.create_column('#', self.COLS['shares'])
        self.create_column(_('Name'), self.COLS['name'])
        self.create_icon_column(_('Type'), self.COLS['type'], size=Gtk.IconSize.DND)
        self.create_column(_('Pf %'), self.COLS['pf_percent'], func=gui_utils.percent_format)
        self.create_column(_('Start'), self.COLS['start'], func=start_price_markup)
        self.create_column(_('Buy value'), self.COLS['buy_value'], func=gui_utils.currency_format)
        self.create_column(_('Last price'), self.COLS['last_price'], func=current_price_markup)
        self.create_column(_('Change'), self.COLS['change'], func=gui_utils.float_to_red_green_string_currency)
        self.create_column('%', self.COLS['change_percent'], func=gui_utils.float_to_red_green_string_percent)
        self.create_column(_('Mkt value'), self.COLS['mkt_value'], gui_utils.currency_format)
        self.create_column(_('Gain'), self.COLS['gain'], gui_utils.float_to_red_green_string_currency)
        self.create_icon_text_column('%', self.COLS['gain_icon'], self.COLS['gain_percent'], func2=gui_utils.float_to_red_green_string_percent)
        self.create_column(_('Today'), self.COLS['days_gain'], gui_utils.float_to_red_green_string_currency)

    def on_add(self, widget):
        dl = dialogs.BuyDialog(self.container, parent=self.get_toplevel())
        if dl.position is not None:
            self.on_position_added(dl.position)

    def insert_position(self, position):
        if position.quantity != 0:
            tree_iter = None
            if position.stock.id in self.stock_cache:
                if isinstance(self.stock_cache[position.stock.id], MetaPosition):
                    mp = self.stock_cache[position.stock.id]
                    tree_iter = self.find_position(mp).iter
                else:
                    p1 = self.stock_cache[position.stock.id]
                    mp = MetaPosition(p1)
                    mp.controller = controller
                    tree_iter = self.model.append(None, self._get_row(mp))
                    self.stock_cache[position.stock.id] = mp
                    self._move_position(p1, tree_iter)
                mp.add_position(position)
                self.update_position_after_edit(mp, tree_iter)
            else:
                self.stock_cache[position.stock.id] = position
            self.model.append(tree_iter, self._get_row(position))

    def _get_row(self, position):
        stock = position.stock
        gain = position.gain
        gain_icon = get_arrow_icon(gain[1])
        c_change = position.current_change
        icons = ['fund', 'stock', 'etf', 'bond']
        ret = [position,
               get_name_string(stock),
               position.price,
               stock.price,
               c_change[0],
               gain[0],
               gui_utils.get_string_from_float(position.quantity),
               position.bvalue,
               position.cvalue,
               position.days_gain,
               float(gain[1]),
               gain_icon,
               float(c_change[1]),
               icons[position.stock.type],
               float(self.container.fraction(position))]

        if isinstance(position, MetaPosition):
            ret[self.COLS['shares']] = unichr(8721) + " " + ret[self.COLS['shares']]
        return ret

    def on_remove(self, widget):
        position, iterator = self.selected_item
        dlg = Gtk.MessageDialog(None,
             Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.QUESTION,
                Gtk.ButtonsType.OK_CANCEL, _("This will delete the selected position and all related data. Are you sure?"))
        response = dlg.run()
        dlg.destroy()
        if response == Gtk.ResponseType.OK:
            position.delete()
            self.model.remove(iterator)

    def on_sell(self, widget):
        position, iterator = self.selected_item
        d = dialogs.SellDialog(position, parent=self.get_toplevel())
        if d.response == Gtk.ResponseType.ACCEPT:
            self.model.remove(iterator)
            if position.quantity != 0.0:
                self.insert_position(position)

    def on_dividend(self, widget):
        if self.selected_item is not None:
            dialogs.DividendDialog(pf=self.container, position=self.selected_item[0], parent=self.get_toplevel())
        else:
            dialogs.DividendDialog(pf=self.container, parent=self.get_toplevel())

    def on_stocks_updated(self, container):
        if container.name == self.container.name:
            for row in self.model:
                item = row[0]
                if isinstance(item, MetaPosition):
                    item.recalculate()
                gain, gain_percent = item.gain
                row[self.COLS['name']] = get_name_string(item.stock)
                row[self.COLS['last_price']] = item.stock.price
                row[self.COLS['change']] = item.current_change[0]
                row[self.COLS['change_percent']] = float(item.current_change[1])
                row[self.COLS['gain']] = gain
                row[self.COLS['gain_percent']] = gain_percent
                row[self.COLS['gain_icon']] = get_arrow_icon(gain_percent)
                row[self.COLS['days_gain']] = item.days_gain
                row[self.COLS['mkt_value']] = item.cvalue
                row[self.COLS['pf_percent']] = self.container.fraction(item)

    def on_position_added(self, item):
        self.insert_position(item)
        #update portfolio fractions
        for row in self.model:
            pos = row[self.COLS['obj']]
            row[self.COLS['pf_percent']] = float(self.container.fraction(item))

    def on_unselect(self):
        for action in ['edit', 'sell', 'remove', 'chart']:
            self.actiongroup.get_action(action).set_sensitive(False)

    def on_select(self, obj):
        for action in ['edit', 'sell', 'remove', 'chart']:
            self.actiongroup.get_action(action).set_sensitive(True)



class WatchlistPositionsTree(PositionsTree):

    def __init__(self, watchlist, actiongroup):
        PositionsTree.__init__(self, watchlist, actiongroup)
        self.actiongroup.add_actions([
                ('add', Gtk.STOCK_ADD, 'add', None, _('Add new position'), self.on_add),
                ('edit' , Gtk.STOCK_EDIT, 'edit', None, _('Edit selected position'), self.on_edit),
                ('remove', Gtk.STOCK_DELETE, 'remove', None, _('Delete selected position'), self.on_remove),
                ('chart', None, 'chart', None, _('Chart selected position'), self.on_chart),
                ('update', Gtk.STOCK_REFRESH, 'update', None, _('Update positions'), self.on_update_positions)
                                ])
        self.actiongroup.get_action('chart').set_icon_name('avernus')
        accelgroup = Gtk.AccelGroup()
        for action in self.actiongroup.list_actions():
            action.set_accel_group(accelgroup)

    def _init_widgets(self):
        self.model = Gtk.TreeStore(object, str, float, float, float, float, str, float, float, float, float, str, float, str, float)
        self.set_model(self.model)

        self.create_column(_('Name'), self.COLS['name'])
        self.create_icon_column(_('Type'), self.COLS['type'], size=Gtk.IconSize.DND)
        self.create_column(_('Start'), self.COLS['start'], func=start_price_markup)
        self.create_column(_('Last price'), self.COLS['last_price'], func=current_price_markup)
        self.create_column(_('Change'), self.COLS['change'], func=gui_utils.float_to_red_green_string_currency)
        self.create_column('%', self.COLS['change_percent'], func=gui_utils.float_to_red_green_string_percent)
        self.create_column(_('Gain'), self.COLS['gain'], gui_utils.float_to_red_green_string_currency)
        self.create_icon_text_column('%', self.COLS['gain_icon'], self.COLS['gain_percent'], func2=gui_utils.float_to_red_green_string_percent)

    def on_add(self, widget, user_data=None):
        dl = dialogs.NewWatchlistPositionDialog(self.container, parent=self.get_toplevel())
        if dl.position is not None:
            self.insert_position(dl.position)

    def insert_position(self, position):
        self.model.append(None, self._get_row(position))

    def _get_row(self, position):
        stock = position.stock
        gain = position.gain
        gain_icon = get_arrow_icon(gain[1])
        c_change = position.current_change
        icons = ['fund', 'stock', 'etf', 'bond']
        ret = [position,
               get_name_string(stock),
               position.price,
               stock.price,
               c_change[0],
               gain[0],
               gui_utils.get_string_from_float(position.quantity),
               position.bvalue,
               position.cvalue,
               position.days_gain,
               float(gain[1]),
               gain_icon,
               float(c_change[1]),
               icons[position.stock.type],
               0.0]

        return ret

    def on_remove(self, widget, user_data=None):
        position, iter = self.selected_item
        dlg = Gtk.MessageDialog(None,
             Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.QUESTION,
                Gtk.ButtonsType.OK_CANCEL, _("Are you sure?"))
        response = dlg.run()
        dlg.destroy()
        if response == Gtk.ResponseType.OK:
            position.delete()
            self.model.remove(iter)

    def on_stocks_updated(self, container):
        if container.name == self.container.name:
            for row in self.model:
                item = row[0]
                gain, gain_percent = item.gain
                row[self.COLS['name']] = get_name_string(item.stock)
                row[self.COLS['last_price']] = item.stock.price
                row[self.COLS['change']] = item.current_change[0]
                row[self.COLS['change_percent']] = float(item.current_change[1])
                row[self.COLS['gain']] = gain
                row[self.COLS['gain_percent']] = gain_percent
                row[self.COLS['gain_icon']] = get_arrow_icon(gain_percent)
                row[self.COLS['days_gain']] = item.days_gain
                row[self.COLS['mkt_value']] = item.cvalue

    def on_unselect(self):
        for action in ['edit', 'remove', 'chart']:
            self.actiongroup.get_action(action).set_sensitive(False)

    def on_select(self, obj):
        for action in ['edit', 'remove', 'chart']:
            self.actiongroup.get_action(action).set_sensitive(True)


class WatchlistPositionsTab(Gtk.VBox, page.Page):

    def __init__(self, watchlist):
        Gtk.VBox.__init__(self)
        self.watchlist = watchlist
        actiongroup = Gtk.ActionGroup('watchlist positions tab')
        positions_tree = WatchlistPositionsTree(watchlist, actiongroup)
        tb = Gtk.Toolbar()

        for action in ['add', 'remove', 'edit', 'chart', '---', 'update']:
            if action == '---':
                tb.insert(Gtk.SeparatorToolItem(), -1)
            else:
                button = actiongroup.get_action(action).create_tool_item()
                tb.insert(button, -1)

        self.pack_start(tb, False, True, 0)

        sw = Gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        sw.set_property('vscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        sw.add(positions_tree)
        self.pack_start(sw, True, True, 0)

        pubsub.subscribe('position.created', self.update_page)
        pubsub.subscribe('stocks.updated', self.update_page)
        pubsub.subscribe('container.updated', self.update_page)
        pubsub.subscribe('container.position.added', self.update_page)
        self.show_all()

    def show(self):
        self.update_page()

    def get_info(self):
        return [('# positions', len(self.watchlist)),
                ('Last update', gui_utils.datetime_format(self.watchlist.last_update, False))]


class PortfolioPositionsTab(Gtk.VBox, page.Page):

    def __init__(self, portfolio):
        Gtk.VBox.__init__(self)
        self.portfolio = portfolio
        actiongroup = Gtk.ActionGroup('portfolio positions tab')
        positions_tree = PortfolioPositionsTree(portfolio, actiongroup)
        tb = Gtk.Toolbar()

        for action in ['add', 'sell', 'remove', 'edit', 'chart', '---', 'update']:
            if action == '---':
                tb.insert(Gtk.SeparatorToolItem(), -1)
            else:
                button = actiongroup.get_action(action).create_tool_item()
                tb.insert(button, -1)

        self.pack_start(tb, False, True, 0)

        sw = Gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        sw.set_property('vscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        sw.add(positions_tree)
        self.pack_start(sw, True, True, 0)

        pubsub.subscribe('position.created', self.update_page)
        pubsub.subscribe('stocks.updated', self.update_page)
        pubsub.subscribe('container.updated', self.update_page)
        pubsub.subscribe('container.position.added', self.update_page)
        self.show_all()

    def show(self):
        self.update_page()

    def get_info(self):
        change, percent = pfctrl.get_current_change(self.portfolio)
        change_text = gui_utils.get_string_from_float(percent) + '%' + ' | ' + gui_utils.get_currency_format_from_float(change)
        o_change, o_percent = pfctrl.get_overall_change(self.portfolio)
        o_change_text = gui_utils.get_string_from_float(o_percent) + '%' + ' | ' + gui_utils.get_currency_format_from_float(o_change)
        return [(_('Day\'s gain'), gui_utils.get_green_red_string(change, change_text)),
                (_('Overall gain'), gui_utils.get_green_red_string(o_change, o_change_text)),
                ('Investments', gui_utils.get_currency_format_from_float(pfctrl.get_current_value(self.portfolio))),
                ('# positions', len(self.portfolio.positions)),
                ('Last update', gui_utils.datetime_format(self.portfolio.last_update, False))
                ]
