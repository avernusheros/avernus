from avernus.gui import gui_utils
from avernus.objects import portfolio_transaction
from gi.repository import Gtk
import datetime


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
        label.set_markup(gui_utils.get_name_string(pos.asset))
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
            self.tacosts_entry.set_value(self.transaction.cost)
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
            date = datetime.date(year, month + 1, day)
            ta_costs = self.tacosts_entry.get_value()

            if self.transaction is None:
                if shares == 0.0:
                    return
                self.pos.quantity -= shares
                portfolio_transaction.SellTransaction(position=self.pos, date=date, quantity=shares, price=price, cost=ta_costs)
            else:
                self.pos.price = self.transaction.price = price
                self.pos.date = self.transaction.date = date
                self.transaction.cost = ta_costs
                self.pos.quantity = self.transaction.quantity = shares

    def on_change(self, widget=None):
        total = self.shares_entry.get_value() * self.price_entry.get_value() + self.tacosts_entry.get_value()
        self.total.set_markup('<b>' + gui_utils.get_currency_format_from_float(total) + '</b>')
