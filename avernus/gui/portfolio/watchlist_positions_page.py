from avernus.controller import datasource_controller
from avernus.gui import page, get_avernus_builder, gui_utils, progress_manager
from avernus.gui.portfolio import positions_tab, dialogs, position_dialog, plot
from gi.repository import Gtk


class WatchlistPositionsPage(page.Page):

    OBJECT = 0
    NAME = 1
    TYPE = 2
    START = 3
    LAST_PRICE = 4
    CHANGE = 5
    CHANGE_PERCENT = 6
    GAIN = 7
    GAIN_PERCENT = 8
    GAIN_ICON = 9

    def __init__(self):
        page.Page.__init__(self)
        self.builder = get_avernus_builder()
        self.widget = self.builder.get_object("watchlist_box")
        self.treestore = self.builder.get_object("wl_positions_treestore")
        self.actiongroup = self.builder.get_object("wl_position_actiongroup")
        self.watchlist = None

        # start price
        cell = self.builder.get_object("cellrenderertext39")
        column = self.builder.get_object("treeviewcolumn39")
        column.set_cell_data_func(cell, positions_tab.start_price_markup, self.START)
        # last price
        cell = self.builder.get_object("cellrenderertext40")
        column = self.builder.get_object("treeviewcolumn40")
        column.set_cell_data_func(cell, positions_tab.current_price_markup, self.LAST_PRICE)
        # change
        cell = self.builder.get_object("cellrenderertext41")
        column = self.builder.get_object("treeviewcolumn41")
        column.set_cell_data_func(cell, gui_utils.float_to_red_green_string_currency, self.CHANGE)
        # change %
        cell = self.builder.get_object("cellrenderertext42")
        column = self.builder.get_object("treeviewcolumn42")
        column.set_cell_data_func(cell, gui_utils.float_to_red_green_string_percent, self.CHANGE_PERCENT)
        # gain
        cell = self.builder.get_object("cellrenderertext43")
        column = self.builder.get_object("treeviewcolumn43")
        column.set_cell_data_func(cell, gui_utils.float_to_red_green_string_currency, self.GAIN)
        # gain %
        cell = self.builder.get_object("cellrenderertext44")
        column = self.builder.get_object("treeviewcolumn44")
        column.set_cell_data_func(cell, gui_utils.float_to_red_green_string_percent, self.GAIN_PERCENT)

    def set_watchlist(self, watchlist):
        self.treestore.clear()
        if self.watchlist:
            self.watchlist.disconnect(self.signal_id)
        self.watchlist = watchlist
        self.signal_id = self.watchlist.connect('position_added', self.update_page)

        for pos in watchlist:
            self.insert_position(pos)
        self.update_page()

    def on_wlpositionstree_cursor_changed(self, widget):
        selection = widget.get_selection()
        if selection:
            treestore, selection_iter = selection.get_selected()
            if selection_iter and treestore:
                obj = treestore.get_value(selection_iter, 0)
                self.selected_item = obj, selection_iter
                self.actiongroup.set_sensitive(True)
        else:
            self.actiongroup.set_sensitive(False)

    def insert_position(self, position):
        self.treestore.append(None, self._get_row(position))

    def _get_row(self, position):
        gain = position.gain
        gain_icon = positions_tab.get_arrow_icon(gain[1])
        c_change = position.current_change
        return [position,
               gui_utils.get_name_string(position.asset),
               position.asset.type_str,
               position.price,
               position.asset.price,
               c_change[0],
               c_change[1],
               gain[0],
               gain[1],
               gain_icon]

    def get_info(self):
        return [('# positions', len(self.watchlist.positions)),
                ('Last update', gui_utils.datetime_format(self.watchlist.last_update, False))]

    def on_wlposition_remove(self, widget):
        if self.selected_item:
            position, iterator = self.selected_item
            dlg = Gtk.MessageDialog(None,
                 Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.QUESTION,
                    Gtk.ButtonsType.OK_CANCEL, _("Are you sure?"))
            response = dlg.run()
            dlg.destroy()
            if response == Gtk.ResponseType.OK:
                position.delete()
                self.treestore.remove(iterator)

    def on_update_wlpositions(self, *args):
        progress_manager.add_task(datasource_controller.update_positions,
                            self.watchlist,
                            _('updating assets...'),
                            self.update)

    def on_add_wlposition(self, widget):
        dl = dialogs.NewWatchlistPositionDialog(self.watchlist,
                                        parent=self.widget.get_toplevel())
        if dl.position:
            self.insert_position(dl.position)
            self.update_page()

    def on_wlposition_edit(self, widget):
        if self.selected_item:
            position, iterator = self.selected_item
            position_dialog.PositionDialog(position, self.widget.get_toplevel())
            self.update_position_after_edit(position, iterator)

    def on_wlposition_chart(self, widget):
        if self.selected_item:
            plot.ChartWindow(self.selected_item[0].asset)
