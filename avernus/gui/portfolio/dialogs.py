from gi.repository import Gtk

from avernus import pubsub
from avernus.gui import gui_utils
from avernus.controller import portfolio_controller, position_controller
import locale
import datetime


class BuyDialog(Gtk.Dialog):

    def __init__(self, pf, transaction=None, parent=None):
        Gtk.Dialog.__init__(self, _("Buy a position"), parent
                            , Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                     (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                      Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        self.pf = pf
        self.transaction = transaction
        self.position = None
        if transaction is None:
            self.b_new = True
        else:
            self.b_new = False

        vbox = self.get_content_area()
        table = Gtk.Table()
        table.set_row_spacings(4)
        table.set_col_spacings(4)
        vbox.pack_end(table, True, True, 0)
        if self.b_new:
            #stock entry
            self.stock_selector = StockSelector()
            table.attach(self.stock_selector, 0, 3, 0, 1)
            self.stock_selector.result_tree.connect('cursor-changed', self.on_stock_selection)
            self.stock_selector.result_tree.get_model().connect('row-deleted', self.on_stock_deselection)
            self.stock_ok = False
        else:
            label = Gtk.Label()
            label.set_markup(gui_utils.get_name_string(self.transaction.position.stock))
            label.set_alignment(0.0, 0.5)
            table.attach(label, 0, 3, 0, 1, xoptions=Gtk.AttachOptions.FILL, yoptions=0)

        #shares entry
        table.attach(Gtk.Label(label=_('Shares')), 1, 2, 1, 2, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK)
        self.shares_entry = Gtk.SpinButton()
        self.shares_entry.set_adjustment(Gtk.Adjustment(lower=0, upper=100000, step_increment=1.0, value=1))
        self.shares_entry.set_digits(2)
        self.shares_entry.connect("value-changed", self.on_change)
        table.attach(self.shares_entry, 2, 3, 1, 2, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK)

        #price entry
        table.attach(Gtk.Label(label=_('Price')), 1, 2, 2, 3, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK)
        self.price_entry = Gtk.SpinButton()
        self.price_entry.set_adjustment(Gtk.Adjustment(lower=0, upper=100000, step_increment=0.1, value=1.0))
        self.price_entry.set_digits(2)
        self.price_entry.connect("value-changed", self.on_change)
        table.attach(self.price_entry, 2, 3, 2, 3, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK)

        #ta_costs entry
        table.attach(Gtk.Label(label=_('Transaction Costs')), 1, 2, 3, 4, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK)
        self.tacosts_entry = Gtk.SpinButton()
        self.tacosts_entry.set_adjustment(Gtk.Adjustment(lower=0, upper=100000, step_increment=0.1, value=0.0))
        self.tacosts_entry.set_digits(2)
        self.tacosts_entry.connect("value-changed", self.on_change)
        table.attach(self.tacosts_entry, 2, 3, 3, 4, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK)

        #total
        table.attach(Gtk.Label(label=_('Total')), 1, 2, 4, 5, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK)
        self.total = Gtk.Label()
        self.total.set_markup('<b>' + gui_utils.get_currency_format_from_float(0.0) + '</b>')
        table.attach(self.total, 2, 3, 4, 5, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK)

        #date
        self.calendar = Gtk.Calendar()
        self.calendar.connect('day-selected', self.on_calendar_day_selected)
        table.attach(self.calendar, 0, 1, 1, 5, yoptions=Gtk.AttachOptions.SHRINK)
        self.date_ok = True

        self.infobar = Gtk.InfoBar()
        self.infobar.set_message_type(Gtk.MessageType.WARNING)

        if not self.b_new:
            self.stock_ok = True
            self.shares_entry.set_value(self.transaction.quantity)
            self.price_entry.set_value(self.transaction.price)
            self.tacosts_entry.set_value(self.transaction.costs)
            self.calendar.select_month(self.transaction.date.month - 1, self.transaction.date.year)
            self.calendar.select_day(self.transaction.date.day)
            self.on_change()

        content = self.infobar.get_content_area()
        label = Gtk.Label(label='Buy dates of positions can not be in the future.')
        image = Gtk.Image()
        image.set_from_stock(Gtk.STOCK_DIALOG_WARNING, Gtk.IconSize.DIALOG)
        content.pack_start(image, True, True, 0)
        content.pack_start(label, True, True, 0)
        vbox.pack_start(self.infobar, True, True, 0)

        if self.b_new:
            self.set_response_sensitive(Gtk.ResponseType.ACCEPT, False)
        table.show_all()
        response = self.run()
        self.process_result(response)
        self.destroy()

    def on_calendar_day_selected(self, calendar):
        year, month, day = self.calendar.get_date()
        date = datetime.datetime(year, month + 1, day)
        if date > datetime.datetime.today():
            self.infobar.show_all()
            self.date_ok = False
        else:
            self.infobar.hide()
            self.date_ok = True
        self.set_response_sensitivity()

    def on_change(self, widget=None):
        total = self.shares_entry.get_value() * self.price_entry.get_value() + self.tacosts_entry.get_value()
        self.total.set_markup('<b>' + gui_utils.get_currency_format_from_float(total) + '</b>')

    def on_stock_selection(self, *args):
        self.stock_ok = True
        st = self.stock_selector.get_stock()
        st.update_price()
        self.price_entry.set_value(st.price)
        self.set_response_sensitivity()

    def on_stock_deselection(self, *args):
        self.stock_ok = False
        self.set_response_sensitivity()

    def set_response_sensitivity(self):
        if self.stock_ok and self.date_ok:
            self.set_response_sensitive(Gtk.ResponseType.ACCEPT, True)
        else:
            self.set_response_sensitive(Gtk.ResponseType.ACCEPT, False)

    def process_result(self, response):
        if self.b_new:
            self.stock_selector.stop_search()
        if response == Gtk.ResponseType.ACCEPT:
            price = self.price_entry.get_value()
            year, month, day = self.calendar.get_date()
            date = datetime.datetime(year, month + 1, day)
            ta_costs = self.tacosts_entry.get_value()
            shares = self.shares_entry.get_value()

            if self.b_new:
                stock = self.stock_selector.get_stock()
                stock.update_price()
                if shares == 0.0:
                    return
                self.position = position_controller.new_portfolio_position(price=price, date=date, quantity=shares, portfolio=self.pf, stock=stock)
                ta = controller.newTransaction(type=1, date=date, quantity=shares, price=price, costs=ta_costs, position=self.position, portfolio=self.pf)
                #FIXME trigger publish in container.py and transaction.py
                pubsub.publish('container.position.added', self.pf, self.position)
                pubsub.publish('transaction.added', ta)
            else:
                self.transaction.position.price = self.transaction.price = price
                self.transaction.position.date = self.transaction.date = date
                self.transaction.costs = ta_costs
                self.transaction.position.quantity = self.transaction.quantity = shares


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
        self.stock_selector = StockSelector()
        vbox.pack_start(self.stock_selector, True, True, 0)
        self.stock_selector.result_tree.connect('cursor-changed', self.on_stock_selection)
        self.stock_selector.result_tree.get_model().connect('row-deleted', self.on_stock_deselection)

        self.set_size_request(self.WIDTH, self.HEIGHT)
        self.set_response_sensitive(Gtk.ResponseType.ACCEPT, False)
        self.show_all()
        response = self.run()
        self.process_result(response)
        self.destroy()

    def on_stock_selection(self, *args):
        self.set_response_sensitive(Gtk.ResponseType.ACCEPT, True)

    def on_stock_deselection(self, *args):
        self.set_response_sensitive(Gtk.ResponseType.ACCEPT, False)

    def process_result(self, response):
        self.stock_selector.stop_search()
        if response == Gtk.ResponseType.ACCEPT:
            stock = self.stock_selector.get_stock()
            stock.update_price()
            self.position = controller.newWatchlistPosition(price=stock.price, date=stock.date, watchlist=self.wl, stock=stock)
            pubsub.publish('container.position.added', self.wl, self.position)


class PosSelector(Gtk.ComboBox):

    def __init__(self, pf, position=None):
        Gtk.ComboBox.__init__(self)
        cell = Gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, 'text', 1)
        self.set_active(0)
        #self.set_button_sensitivity(GTK_SENSITIVITY_AUTO)

        liststore = Gtk.ListStore(object, str)
        liststore.append([-1, 'Select a position'])
        i = 1
        if pf is not None:
            for pos in sorted(pf, key=lambda pos: pos.stock.name):
                if pos.quantity > 0:
                    liststore.append([pos, str(pos.quantity) + ' ' + pos.name])
                    if position and position == pos:
                        self.set_active(i)
                    i += 1
        else:
            for pos in sorted(portfolio_controller.getAllPosition(), key=lambda pos: pos.stock.name):
                if pos.quantity > 0:
                    liststore.append([pos, pos.portfolio.name + ": " + str(pos.quantity) + ' ' + pos.name])
        self.set_model(liststore)


class EditStockDialog(Gtk.Dialog):

    def __init__(self, stock, parent=None):
        Gtk.Dialog.__init__(self, _("Edit stock"), parent
                            , Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                     (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                      Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))

        vbox = self.get_content_area()
        self.table = EditStockTable(stock)
        vbox.pack_start(self.table, True, True, 0)

        self.show_all()
        response = self.run()
        self.process_result(response=response)

    def process_result(self, widget=None, response=Gtk.ResponseType.ACCEPT):
        if response == Gtk.ResponseType.ACCEPT:
            self.table.process_result(response)
        self.destroy()



class DividendDialog(Gtk.Dialog):

    def __init__(self, pf=None, tree=None, date=None, price=None, position=None, dividend=None, parent=None):
        Gtk.Dialog.__init__(self, _("Add dividend"), parent
                            , Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                     (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                      'Add', Gtk.ResponseType.ACCEPT))
        self.tree = tree
        self.dividend = dividend
        vbox = self.get_content_area()
        table = Gtk.Table()
        vbox.pack_start(table, True, True, 0)

        table.attach(Gtk.Label(label=_('Position')), 0, 1, 0, 1)
        if dividend is not None:
            position = dividend.position
        self.pos_selector = PosSelector(pf, position)
        self.pos_selector.connect('changed', self.on_changed_pos)
        table.attach(self.pos_selector, 1, 2, 0, 1)
        self.selected_pos = position

        table.attach(Gtk.Label(label=_('Amount')), 0, 1, 1, 2)
        self.value_entry = Gtk.SpinButton(adjustment=Gtk.Adjustment(lower=0, upper=100000, step_increment=0.1, value=1.0), digits=2)
        self.value_entry.connect("value-changed", self.on_change)
        table.attach(self.value_entry, 1, 2, 1, 2)

        table.attach(Gtk.Label(label=_('Transaction costs')), 0, 1, 2, 3)
        self.tacosts_entry = Gtk.SpinButton(adjustment=Gtk.Adjustment(lower=0, upper=100000, step_increment=0.1, value=0.0), digits=2)
        self.tacosts_entry.connect("value-changed", self.on_change)
        table.attach(self.tacosts_entry, 1, 2, 2, 3)

        table.attach(Gtk.Label(label=_('Total')), 0, 1, 3, 4)
        self.total = Gtk.Label()
        self.total.set_markup('<b>' + gui_utils.get_currency_format_from_float(0.0) + '</b>')
        table.attach(self.total, 1, 2, 3, 4, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK)

        self.calendar = Gtk.Calendar()
        table.attach(self.calendar, 0, 2, 4, 5)

        if date is not None:
            self.calendar.select_month(date.month - 1, date.year)
            self.calendar.select_day(date.day)
        if price is not None:
            self.value_entry.set_value(price)
            self.on_change()

        if dividend is not None:
            self.calendar.select_month(dividend.date.month - 1, dividend.date.year)
            self.calendar.select_day(dividend.date.day)
            self.value_entry.set_value(dividend.price)
            self.tacosts_entry.set_value(dividend.costs)
            self.on_change()

        self.set_response_sensitive(Gtk.ResponseType.ACCEPT, self.selected_pos is not None)
        self.show_all()
        response = self.run()
        self.process_result(response)
        self.destroy()

    def on_change(self, widget=None):
        total = self.value_entry.get_value() - self.tacosts_entry.get_value()
        self.total.set_markup('<b>' + gui_utils.get_currency_format_from_float(total) + '</b>')

    def on_changed_pos(self, combobox):
        model = combobox.get_model()
        index = combobox.get_active()
        if index:
            self.selected_pos = model[index][0]
            self.set_response_sensitive(Gtk.ResponseType.ACCEPT, True)
        else:
            self.selected_pos = None
            self.set_response_sensitive(Gtk.ResponseType.ACCEPT, False)

    def process_result(self, response):
        if response == Gtk.ResponseType.ACCEPT:
            year, month, day = self.calendar.get_date()
            date = datetime.datetime(year, month + 1, day)
            value = self.value_entry.get_value()
            ta_costs = self.tacosts_entry.get_value()
            if self.dividend is None:
                div = controller.newDividend(price=value, date=date, costs=ta_costs, position=self.selected_pos, shares=self.selected_pos.quantity)
                if self.tree is not None:
                    self.tree.insert_dividend(div)
            else:
                self.dividend.price = value
                self.dividend.date = date
                self.dividend.costs = ta_costs
                self.dividend.position = self.selected_pos
                self.dividend.shares = self.selected_pos.quantity


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
        advs = asset.getAssetDimensionValue(dim)
        if len(advs) == 1:
            # we have 100% this value in its dimension
            return str(advs.pop(0))
        erg = ""
        i = 0
        for adv in advs:
            i += 1
            erg += self.get_adv_text(adv)
            if i < len(advs):
                erg += self.SEPARATOR + " "
        return erg

    def get_adv_text(self, adv):
        erg = adv.dimensionValue.name
        if adv.value != 100:
            erg += ":" + locale.str(adv.value)
        return erg

    def on_entry_changed(self, editable):
        parse = self.parse()
        if not parse and not parse == []: # unsuccesfull parse
            self.get_child().set_icon_from_stock(1, Gtk.STOCK_CANCEL)
            self.dialog.set_response_sensitive(Gtk.ResponseType.ACCEPT, False)
        else: # sucessful parse
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
                #print "|"+value+"|"
                if value == "": # no value given
                    if not currentName == "": # has the user not even entered a name?
                        value = "100" # he has, so consider it to be a full value
                    else:
                        continue # no name, no entry
                try:
                    value = locale.atof(value) # try parsing a float out of the number
                except:
                    return False # failure
                sum += value
                erg.append((unicode(currentName), value))
            if sum > 100:
                return False
            else:
                return erg
        return [(self.get_model()[iterator][self.COL_OBJ].name, 100)] # hack to have it easier in the calling method

    def get_active(self):
        erg = []
        parse = self.parse()
        if parse:
            for name, value in parse:
                erg.append((controller.newDimensionValue(self.dimension, name), value))
        return erg


class EditStockTable(Gtk.Table):

    def __init__(self, stock_to_edit, dialog):
        Gtk.Table.__init__(self)
        self.stock = stock_to_edit
        self.b_change = False

        self.attach(Gtk.Label(label=_('Name')), 0, 1, 0, 1, yoptions=Gtk.AttachOptions.FILL)
        self.name_entry = Gtk.Entry()
        self.name_entry.set_text(stock_to_edit.name)
        self.attach(self.name_entry, 1, 2, 0, 1, yoptions=Gtk.AttachOptions.FILL)

        self.attach(Gtk.Label(label=_('ISIN')), 0, 1, 1, 2, yoptions=Gtk.AttachOptions.FILL)
        self.isin_entry = Gtk.Entry()
        self.isin_entry.set_text(stock_to_edit.isin)
        self.attach(self.isin_entry, 1, 2, 1, 2, yoptions=Gtk.AttachOptions.FILL)

        self.attach(Gtk.Label(label=_('Type')), 0, 1, 2, 3, yoptions=Gtk.AttachOptions.FILL)
        liststore = Gtk.ListStore(str, int)
        for val, name in stock.TYPES.iteritems():
            liststore.append([name, val])
        self.type_cb = cb = Gtk.ComboBox(model=liststore)
        cell = Gtk.CellRendererText()
        cb.pack_start(cell, True)
        cb.add_attribute(cell, 'text', 0)
        cb.set_active(self.stock.type)
        self.attach(cb, 1, 2, 2, 3, yoptions=Gtk.AttachOptions.FILL)

        self.attach(Gtk.Label(label=_('TER')), 0, 1, 3, 4, yoptions=Gtk.AttachOptions.SHRINK)
        self.ter_entry = Gtk.SpinButton(adjustment=Gtk.Adjustment(lower=0, upper=100, step_increment=0.1, value=self.stock.ter), digits=2)
        self.attach(self.ter_entry, 1, 2, 3, 4, yoptions=Gtk.AttachOptions.SHRINK)

        currentRow = 4
        for dim in controller.getAllDimension():
            #print dim
            self.attach(Gtk.Label(label=_(dim.name)), 0, 1, currentRow, currentRow + 1, yoptions=Gtk.AttachOptions.FILL)
            comboName = dim.name + "ValueComboBox"
            setattr(self, comboName, DimensionComboBox(dim, stock_to_edit, dialog))
            self.attach(getattr(self, comboName), 1, 2, currentRow, currentRow + 1, yoptions=Gtk.AttachOptions.FILL)
            getattr(self, comboName).connect("changed", self.on_change)
            currentRow += 1

        self.name_entry.connect('changed', self.on_change)
        self.isin_entry.connect('changed', self.on_change)
        self.ter_entry.connect('changed', self.on_change)

    def on_change(self, widget):
        self.b_change = True

    def process_result(self, widget=None, response=Gtk.ResponseType.ACCEPT):
        if response == Gtk.ResponseType.ACCEPT and self.b_change:
            self.stock.name = self.name_entry.get_text()
            self.stock.isin = self.isin_entry.get_text()
            active_iter = self.type_cb.get_active_iter()
            self.stock.type = self.type_cb.get_model()[active_iter][1]
            self.stock.ter = self.ter_entry.get_value()
            for dim in controller.getAllDimension():
                box = getattr(self, dim.name + "ValueComboBox")
                active = box.get_active()
                self.stock.updateAssetDimensionValue(dim, active)
                pubsub.publish("stock.edited", self.stock)


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
        self.result_tree.create_icon_column(_('Type'), 5, size=Gtk.IconSize.DND)
        self.result_tree.set_size_request(self.WIDTH, self.HEIGHT)
        sw.add(self.result_tree)
        self.pack_end(sw, True , True, 0)
        self.spinner = None

    def get_stock(self):
        path, col = self.result_tree.get_cursor()
        return self.result_tree.get_model()[path][0]

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
        for item in controller.getStockForSearchstring(searchstring):
            if item.source == "yahoo":
                icon = 'yahoo'
            elif item.source == "onvista.de":
                icon = 'onvista'
            else:
                icon = 'gtk-harddisk'
            self.insert_item(item, icon)
        self.search_source_count = pfctlr.datasource_manager.get_source_count()
        portfolio_controller.datasource_manager.search(searchstring, self.insert_item, self.search_complete_callback)

    def search_complete_callback(self):
        self.search_source_count -= 1
        if self.search_source_count == 0:
            self._hide_spinner()

    def stop_search(self):
        self._hide_spinner()
        portfolio_controller.datasource_manager.stop_search()

    def insert_item(self, stock, icon):
        #FIXME bond icon
        icons = ['fund', 'stock', 'etf', 'stock']
        self.result_tree.get_model().append(None, [
                                       stock,
                                       icon,
                                       stock.name,
                                       stock.isin,
                                       stock.currency,
                                       icons[stock.type],
                                       ])


class SellDialog(Gtk.Dialog):

    def __init__(self, pos, transaction=None, parent=None):
        if transaction is None:
            title = _('Sell position')
            max_quantity = pos.quantity
        else:
            title = _('Edit position')
            max_quantity = pos.quantity + transaction.quantity
        Gtk.Dialog.__init__(self, title, parent
                            , Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                     (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                      Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        self.pos = pos
        self.transaction = transaction

        vbox = self.get_content_area()
        table = Gtk.Table()
        table.set_row_spacings(4)
        table.set_col_spacings(4)
        vbox.pack_end(table, True, True, 0)

        #name
        label = Gtk.Label()
        label.set_markup(gui_utils.get_name_string(pos.stock))
        label.set_alignment(0.0, 0.5)
        table.attach(label, 0, 2, 0, 1, Gtk.AttachOptions.FILL, 0)

        #shares entry
        table.attach(Gtk.Label(label=_('Shares')), 1, 2, 1, 2)
        self.shares_entry = Gtk.SpinButton()
        self.shares_entry.set_adjustment(Gtk.Adjustment(lower=0, upper=max_quantity, step_increment=1, value=0))
        self.shares_entry.set_digits(2)
        self.shares_entry.connect("value-changed", self.on_change)
        table.attach(self.shares_entry, 2, 3, 1, 2, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK)

        #price entry
        table.attach(Gtk.Label(label=_('Price:')), 1, 2, 2, 3)
        self.price_entry = Gtk.SpinButton()
        self.price_entry.set_adjustment(Gtk.Adjustment(lower=0, upper=100000, step_increment=0.1, value=1.0))
        self.price_entry.set_digits(2)
        self.price_entry.connect("value-changed", self.on_change)
        table.attach(self.price_entry, 2, 3, 2, 3, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK)

        #ta_costs entry
        table.attach(Gtk.Label(label=_('Transaction Costs')), 1, 2, 3, 4, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK)
        self.tacosts_entry = Gtk.SpinButton()
        self.tacosts_entry.set_adjustment(Gtk.Adjustment(lower=0, upper=100000, step_increment=0.1, value=0.0))
        self.tacosts_entry.set_digits(2)
        self.tacosts_entry.connect("value-changed", self.on_change)
        table.attach(self.tacosts_entry, 2, 3, 3, 4, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK)

        #total
        table.attach(Gtk.Label(label=_('Total')), 1, 2, 4, 5, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK)
        self.total = Gtk.Label()
        self.total.set_markup('<b>' + gui_utils.get_currency_format_from_float(0.0) + '</b>')
        table.attach(self.total, 2, 3, 4, 5, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK)

        #date
        self.calendar = Gtk.Calendar()
        table.attach(self.calendar, 0, 1, 1, 5)

        if self.transaction is not None:
            self.shares_entry.set_value(self.transaction.quantity)
            self.price_entry.set_value(self.transaction.price)
            self.tacosts_entry.set_value(self.transaction.costs)
            self.calendar.select_month(self.transaction.date.month - 1, self.transaction.date.year)
            self.calendar.select_day(self.transaction.date.day)
            self.on_change()

        self.show_all()
        self.response = self.run()
        self.process_result()

        self.destroy()

    def process_result(self):
        if self.response == Gtk.ResponseType.ACCEPT:
            shares = self.shares_entry.get_value()
            price = self.price_entry.get_value()
            year, month, day = self.calendar.get_date()
            date = datetime.datetime(year, month + 1, day)
            ta_costs = self.tacosts_entry.get_value()

            if self.transaction is None:
                if shares == 0.0:
                    return
                self.pos.quantity -= shares
                ta = controller.newTransaction(portfolio=self.pos.portfolio, position=self.pos, type=0, date=date, quantity=shares, price=price, costs=ta_costs)
                pubsub.publish('transaction.added', ta)
            else:
                self.pos.price = self.transaction.price = price
                self.pos.date = self.transaction.date = date
                self.transaction.costs = ta_costs
                self.pos.quantity = self.transaction.quantity = shares

    def on_change(self, widget=None):
        total = self.shares_entry.get_value() * self.price_entry.get_value() + self.tacosts_entry.get_value()
        self.total.set_markup('<b>' + gui_utils.get_currency_format_from_float(total) + '</b>')

