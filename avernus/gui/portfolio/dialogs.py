from avernus.controller import datasource_controller
from avernus.gui import gui_utils
from avernus.objects import asset, dimension, position as position_m
from gi.repository import Gtk, GObject
import locale
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


class DimensionComboBox(Gtk.ComboBoxText):

    COL_OBJ = 0
    COL_TEXT = 1
    SEPARATOR = ';'

    def __init__(self, dimension, asset, dialog):
        self.dimension = dimension
        self.dialog = dialog
        liststore = Gtk.ListStore(object, str)
        Gtk.ComboBox.__init__(self, model=liststore, id_column=self.COL_TEXT, has_entry=True)
        for dimVal in sorted(dimension.values):
            liststore.append([dimVal, dimVal.name])
        self.get_child().set_text(self.get_dimension_text(asset, dimension))
        completion = Gtk.EntryCompletion()
        completion.set_model(liststore)
        completion.set_text_column(self.COL_TEXT)
        completion.set_match_func(self.match_func, None)
        self.get_child().set_completion(completion)
        self.get_child().set_icon_from_stock(1, Gtk.STOCK_APPLY)
        self.get_child().set_property('secondary-icon-activatable', False)
        self.get_child().set_property('secondary-icon-tooltip-markup', '<b>ValueA</b> or <b>ValueA:40, ValueB:30 ...</b>')
        completion.connect("match-selected", self.on_completion_match)
        self.connect('changed', self.on_entry_changed)

    def get_dimension_text(self, asset, dim):
        advs = dim.get_asset_dimension_value(asset)
        if len(advs) == 1:
            # we have 100% this value in its dimension
            return advs.pop(0).get_text()
        erg = ""
        i = 0
        for adv in advs:
            i += 1
            erg += self.get_adv_text(adv)
            if i < len(advs):
                erg += self.SEPARATOR + " "
        return erg

    def get_adv_text(self, adv):
        erg = adv.dimension_value.name
        if adv.value != 100:
            erg += ":" + locale.str(adv.value)
        return erg

    def on_entry_changed(self, editable):
        parse = self.parse()
        if not parse and not parse == []:  # unsuccesfull parse
            self.get_child().set_icon_from_stock(1, Gtk.STOCK_CANCEL)
            self.dialog.set_response_sensitive(Gtk.ResponseType.ACCEPT, False)
        else:  # sucessful parse
            self.get_child().set_icon_from_stock(1, Gtk.STOCK_APPLY)
            self.dialog.set_response_sensitive(Gtk.ResponseType.ACCEPT, True)

    def match_func(self, completion, key, iter):
        model = completion.get_model()
        text = model.get_value(iter, self.COL_TEXT).lower()
        key = key.split(self.SEPARATOR)[-1].strip().lower()
        if text.startswith(key):
            return True
        return False

    def on_completion_match(self, completion, model, iter):
        current_text = self.get_child().get_active_text()
        current_text = current_text[:-len(current_text.split(self.SEPARATOR)[-1])]
        if len(current_text) == 0:
            self.get_child().set_text(model[iter][self.COL_TEXT])
        else:
            self.get_child().set_text(current_text + ' ' + model[iter][self.COL_TEXT])
        self.get_child().set_position(-1)
        # stop the event propagation
        return True

    def parse(self):
        iterator = self.get_active_iter()
        if iterator is None:
            name = self.get_active_text()
            portions = name.split(self.SEPARATOR)
            sum = 0
            erg = []
            for portion in portions:
                data = portion.partition(":")
                currentName = data[0].strip()
                value = data[2].strip()
                # print "|"+value+"|"
                if value == "":  # no value given
                    if not currentName == "":  # has the user not even entered a name?
                        value = "100"  # he has, so consider it to be a full value
                    else:
                        continue  # no name, no entry
                try:
                    value = locale.atof(value)  # try parsing a float out of the number
                except:
                    return False  # failure
                sum += value
                erg.append((unicode(currentName), value))
            if sum > 100:
                return False
            else:
                return erg
        return [(self.get_model()[iterator][self.COL_OBJ].name, 100)]  # hack to have it easier in the calling method

    def get_active(self):
        erg = []
        parse = self.parse()
        if parse:
            for name, value in parse:
                erg.append((dimension.DimensionValue(dimension=self.dimension, name=name), value))
        return erg


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
        self.price_entry = Gtk.SpinButton(adjustment=Gtk.Adjustment(lower=0, upper=100, step_increment=0.1, value=asset_to_edit.price), digits=2)
        self.attach(self.price_entry, 1, 2, 1, 2, yoptions=Gtk.AttachOptions.SHRINK)

        self.attach(Gtk.Label(label=_('ISIN')), 0, 1, 2, 3, yoptions=Gtk.AttachOptions.FILL)
        self.isin_entry = Gtk.Entry()
        self.isin_entry.set_text(asset_to_edit.isin)
        self.attach(self.isin_entry, 1, 2, 2, 3, yoptions=Gtk.AttachOptions.FILL)

        self.attach(Gtk.Label(label=_('Type')), 0, 1, 3, 4, yoptions=Gtk.AttachOptions.FILL)
        entry = Gtk.Entry()
        entry.set_text(datasource_controller.ASSET_TYPES[type(asset_to_edit)])
        entry.set_editable(False)
        self.attach(entry, 1, 2, 3, 4, yoptions=Gtk.AttachOptions.FILL)

        self.attach(Gtk.Label(label=_('TER')), 0, 1, 4, 5, yoptions=Gtk.AttachOptions.SHRINK)
        ter_value = 0.0
        if self.asset.ter != None:
            ter_value = self.asset.ter
        self.ter_entry = Gtk.SpinButton(adjustment=Gtk.Adjustment(lower=0, upper=100, step_increment=0.1, value=ter_value), digits=2)
        self.attach(self.ter_entry, 1, 2, 4, 5, yoptions=Gtk.AttachOptions.SHRINK)

        currentRow = 5
        for dim in dimension.get_all_dimensions():
            # print dim
            self.attach(Gtk.Label(label=_(dim.name)), 0, 1, currentRow, currentRow + 1, yoptions=Gtk.AttachOptions.FILL)
            comboName = dim.name + "ValueComboBox"
            setattr(self, comboName, DimensionComboBox(dim, asset_to_edit, dialog))
            self.attach(getattr(self, comboName), 1, 2, currentRow, currentRow + 1, yoptions=Gtk.AttachOptions.FILL)
            getattr(self, comboName).connect("changed", self.on_change)
            currentRow += 1

        self.name_entry.connect('changed', self.on_change)
        self.isin_entry.connect('changed', self.on_change)
        self.ter_entry.connect('changed', self.on_change)
        self.price_entry.connect('changed', self.on_change)

    def on_change(self, widget):
        self.b_change = True

    def process_result(self, widget=None, response=Gtk.ResponseType.ACCEPT):
        if response == Gtk.ResponseType.ACCEPT and self.b_change:
            self.asset.name = self.name_entry.get_text()
            self.asset.isin = self.isin_entry.get_text()
            self.asset.ter = self.ter_entry.get_value()
            new_price = self.price_entry.get_value()
            if self.asset.price != new_price:
                self.asset.price = new_price
                self.asset.date = datetime.datetime.now()
            for dim in dimension.get_all_dimensions():
                box = getattr(self, dim.name + "ValueComboBox")
                active = box.get_active()
                dim.update_asset_dimension_values(self.asset, active)


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
        self.result_tree.model = Gtk.TreeStore(object, str, str, str, str, str)
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
        if self.spinner:
            self.remove(self.spinner)

    def on_search(self, *args):
        self.stop_search()
        self.result_tree.clear()
        searchstring = self.search_field.get_text().strip()
        self._show_spinner()
        for item in asset.get_asset_for_searchstring(searchstring):
            if item.source == "yahoo":
                icon = 'yahoo'
            elif item.source == "onvista.de":
                icon = 'onvista'
            else:
                icon = 'gtk-harddisk'
            self.insert_item(item, icon)
        self.search_source_count = datasource_controller.get_source_count()
        datasource_controller.search(searchstring, self.insert_item, self.search_complete_callback)

    def search_complete_callback(self):
        self.search_source_count -= 1
        if self.search_source_count == 0:
            self._hide_spinner()

    def stop_search(self):
        self._hide_spinner()
        datasource_controller.stop_search()

    def insert_item(self, asset, icon):
        self.result_tree.get_model().append(None, [
                                       asset,
                                       icon,
                                       GObject.markup_escape_text(asset.name),
                                       asset.isin,
                                       asset.currency,
                                       asset.type,
                                       ])
