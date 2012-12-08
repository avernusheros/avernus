from avernus.gui import gui_utils
from avernus.gui.portfolio import dialogs
from avernus.objects import asset
from gi.repository import Gtk
import datetime


class DividendDialog(Gtk.Dialog):

    def __init__(self, pf=None, date=None, price=None, position=None, dividend=None, parent=None):
        Gtk.Dialog.__init__(self, _("Add dividend"), parent
                            , Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                     (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                      'Add', Gtk.ResponseType.ACCEPT))
        self.dividend = dividend
        vbox = self.get_content_area()
        table = Gtk.Table()
        vbox.pack_start(table, True, True, 0)

        table.attach(Gtk.Label(label=_('Position')), 0, 1, 0, 1)
        if dividend is not None:
            position = dividend.position
        self.pos_selector = dialogs.PosSelector(pf, position)
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
            self.tacosts_entry.set_value(dividend.cost)
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
            date = datetime.date(year, month + 1, day)
            value = self.value_entry.get_value()
            ta_costs = self.tacosts_entry.get_value()
            if self.dividend is None:
                self.dividend = asset.Dividend(price=value, date=date, cost=ta_costs,
                                     position=self.selected_pos)
            else:
                self.dividend.price = value
                self.dividend.date = date
                self.dividend.cost = ta_costs
                self.dividend.position = self.selected_pos

