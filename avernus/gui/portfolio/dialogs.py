from avernus.controller import datasource_controller
from avernus.gui import gui_utils
from avernus.objects import asset, position as position_m
from gi.repository import Gtk, GLib
import datetime


class NewWatchlistPositionDialog(Gtk.Dialog):

    WIDTH = 500
    HEIGHT = 400

    def __init__(self, wl, parent=None):
        Gtk.Dialog.__init__(self, _("Add watchlist position"), parent
                            , Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                     (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                      Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        self.wl = wl
        self.position = None

        vbox = self.get_content_area()
        self.asset_selector = StockSelector()
        vbox.pack_start(self.asset_selector, True, True, 0)
        self.asset_selector.result_tree.connect('cursor-changed', self.on_asset_selection)
        self.asset_selector.result_tree.get_model().connect('row-deleted', self.on_asset_deselection)

        self.set_size_request(self.WIDTH, self.HEIGHT)
        self.set_response_sensitive(Gtk.ResponseType.ACCEPT, False)
        self.show_all()
        response = self.run()
        self.process_result(response)
        self.destroy()

    def on_asset_selection(self, *args):
        self.set_response_sensitive(Gtk.ResponseType.ACCEPT, True)

    def on_asset_deselection(self, *args):
        self.set_response_sensitive(Gtk.ResponseType.ACCEPT, False)

    def process_result(self, response):
        self.asset_selector.stop_search()
        if response == Gtk.ResponseType.ACCEPT:
            new_asset = self.asset_selector.get_asset()
            datasource_controller.update_asset(asset)
            self.position = position_m.WatchlistPosition(price=new_asset.price,
                                                         date=new_asset.date,
                                                         watchlist=self.wl,
                                                         asset=new_asset)


class PosSelector(Gtk.ComboBox):

    def __init__(self, pf, position=None):
        Gtk.ComboBox.__init__(self)
        cell = Gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, 'text', 1)
        self.set_active(0)
        # self.set_button_sensitivity(GTK_SENSITIVITY_AUTO)

        liststore = Gtk.ListStore(object, str)
        liststore.append([-1, 'Select a position'])
        i = 1
        if pf is not None:
            for pos in sorted(pf, key=lambda pos: pos.asset.name):
                if pos.quantity > 0:
                    liststore.append([pos, str(pos.quantity) + ' ' + pos.asset.name])
                    if position and position == pos:
                        self.set_active(i)
                    i += 1
        else:
            for pos in sorted(position_m.get_all_portfolio_positions(), key=lambda pos: pos.asset.name):
                if pos.quantity > 0:
                    liststore.append([pos, pos.portfolio.name + ": " + str(pos.quantity) + ' ' + pos.asset.name])
        self.set_model(liststore)


class EditAssetDialog(Gtk.Dialog):

    def __init__(self, asset, parent=None):
        Gtk.Dialog.__init__(self, _("Edit asset"), parent
                            , Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                     (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                      Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))

        vbox = self.get_content_area()
        self.table = EditAssetTable(asset, self)
        vbox.pack_start(self.table, True, True, 0)

        self.show_all()
        response = self.run()
        self.process_result(response=response)

    def process_result(self, widget=None, response=Gtk.ResponseType.ACCEPT):
        if response == Gtk.ResponseType.ACCEPT:
            self.table.process_result(response)
        self.destroy()



class EditAssetTable(Gtk.Table):

    def __init__(self, asset_to_edit, dialog):
        Gtk.Table.__init__(self)
        self.asset = asset_to_edit
        self.b_change = False

        self.attach(Gtk.Label(label=_('Name')), 0, 1, 0, 1, yoptions=Gtk.AttachOptions.FILL)
        self.name_entry = Gtk.Entry()
        self.name_entry.set_text(asset_to_edit.name)
        self.attach(self.name_entry, 1, 2, 0, 1, yoptions=Gtk.AttachOptions.FILL)

        self.attach(Gtk.Label(label=_('Current price')), 0, 1, 1, 2, yoptions=Gtk.AttachOptions.SHRINK)
        self.price_entry = Gtk.SpinButton(adjustment=Gtk.Adjustment(lower=0, upper=1000000, step_increment=0.1, value=asset_to_edit.price), digits=2)
        self.attach(self.price_entry, 1, 2, 1, 2, yoptions=Gtk.AttachOptions.SHRINK)

        self.attach(Gtk.Label(label=_('ISIN')), 0, 1, 2, 3, yoptions=Gtk.AttachOptions.FILL)
        self.isin_entry = Gtk.Entry()
        self.isin_entry.set_text(asset_to_edit.isin)
        self.attach(self.isin_entry, 1, 2, 2, 3, yoptions=Gtk.AttachOptions.FILL)

        self.attach(Gtk.Label(label=_('Type')), 0, 1, 3, 4, yoptions=Gtk.AttachOptions.FILL)
        entry = Gtk.Entry()
        entry.set_text(asset_to_edit.type_str)
        entry.set_editable(False)
        self.attach(entry, 1, 2, 3, 4, yoptions=Gtk.AttachOptions.FILL)

        self.attach(Gtk.Label(label=_('Data source')), 0, 1, 4, 5, yoptions=Gtk.AttachOptions.FILL)
        self.source_cb = Gtk.ComboBoxText()
        self.source_cb.set_entry_text_column(0)
        self.source_cb.append_text(_("None"))
        index = 0
        if self.asset.source is None:
            found = True
            self.source_cb.set_active(index)
        else:
            found = False
        for source in datasource_controller.get_available_sources():
            self.source_cb.append_text(source)
            index += 1
            if self.asset.source == source:
                self.source_cb.set_active(index)
                found = True
        # the asset is using source that is currently not available...
        if not found:
            self.source_cb.append_text(self.asset.source)
            self.source_cb.set_active(index+1)
        self.attach(self.source_cb, 1, 2, 4, 5, yoptions=Gtk.AttachOptions.FILL)

        if hasattr(self.asset, 'ter'):
            self.attach(Gtk.Label(label=_('TER')), 0, 1, 4, 5, yoptions=Gtk.AttachOptions.SHRINK)
            self.ter_entry = Gtk.SpinButton(adjustment=Gtk.Adjustment(lower=0, upper=100, step_increment=0.1, value=self.asset.ter), digits=2)
            self.attach(self.ter_entry, 1, 2, 4, 5, yoptions=Gtk.AttachOptions.SHRINK)
            self.ter_entry.connect('changed', self.on_change)

        self.name_entry.connect('changed', self.on_change)
        self.isin_entry.connect('changed', self.on_change)
        self.price_entry.connect('changed', self.on_change)
        self.source_cb.connect("changed", self.on_change)

    def on_change(self, widget):
        self.b_change = True

    def process_result(self, widget=None, response=Gtk.ResponseType.ACCEPT):
        if response == Gtk.ResponseType.ACCEPT and self.b_change:
            self.asset.name = self.name_entry.get_text()
            self.asset.isin = self.isin_entry.get_text()
            if self.source_cb.get_active() == 0:
                self.asset.source = None
            else:
                self.asset.source = self.source_cb.get_active_text()
            if hasattr(self.asset, 'ter'):
                self.asset.ter = self.ter_entry.get_value()
            new_price = self.price_entry.get_value()
            if self.asset.price != new_price:
                self.asset.price = new_price
                self.asset.change = 0.0
                self.asset.date = datetime.datetime.now()
            

class StockSelector(Gtk.VBox):

    SPINNER_SIZE = 40
    WIDTH = 600
    HEIGHT = 300

    def __init__(self):
        Gtk.VBox.__init__(self)
        self.search_field = Gtk.Entry()
        self.search_field.set_icon_from_stock(1, Gtk.STOCK_FIND)
        self.search_field.connect('activate', self.on_search)
        self.search_field.connect('icon-press', self.on_search)
        self.pack_start(self.search_field, False, False, 0)

        sw = Gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        sw.set_property('vscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        self.result_tree = gui_utils.Tree()
        self.result_tree.model = Gtk.ListStore(object, str, str, str, str, str)
        self.result_tree.set_model(self.result_tree.model)
        self.result_tree.create_icon_column(None, 1)
        col, cell = self.result_tree.create_column(_('Name'), 2)
        cell.props.wrap_width = self.WIDTH / 2
        cell.props.wrap_mode = Gtk.WrapMode.WORD
        self.result_tree.create_column('ISIN', 3)
        self.result_tree.create_column(_('Currency'), 4)
        self.result_tree.create_column(_('Type'), 5)
        self.set_size_request(self.WIDTH, self.HEIGHT)
        sw.add(self.result_tree)
        self.pack_end(sw, True , True, 0)
        self.show_all()
        self.spinner = None

    def get_asset(self):
        path, col = self.result_tree.get_cursor()
        if path:
            return self.result_tree.get_model()[path][0]
        return None

    def _show_spinner(self):
        self.spinner = Gtk.Spinner()
        self.pack_start(self.spinner, True, False, 0)
        self.spinner.show()
        self.spinner.set_size_request(self.SPINNER_SIZE, self.SPINNER_SIZE)
        self.spinner.start()

    def _hide_spinner(self):
        if self.spinner is not None:
            self.remove(self.spinner)
            self.spinner = None
            
    def on_search(self, *args):
        self.stop_search()
        self.result_tree.clear()
        searchstring = self.search_field.get_text().strip()
        self._show_spinner()
        for item in asset.get_asset_for_searchstring(searchstring):
            self.insert_item(item, "")
        self.search_source_count = datasource_controller.get_source_count()
        datasource_controller.search(searchstring, self.insert_item, self.search_complete_callback)

    def search_complete_callback(self):
        self.search_source_count -= 1
        if self.search_source_count == 0:
            self._hide_spinner()

    def stop_search(self):
        self._hide_spinner()
        datasource_controller.stop_search()
        self.cache = set()
        
    def insert_item(self, asset, icon):
        if asset.id not in self.cache:
            self.cache.add(asset.id)
            self.result_tree.get_model().append([
                                       asset,
                                       icon,
                                       GLib.markup_escape_text(asset.name),
                                       asset.isin,
                                       asset.currency,
                                       asset.type,
                                       ])
