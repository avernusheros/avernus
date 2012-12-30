from avernus.controller import datasource_controller
from avernus.gui import get_ui_file, gui_utils
from avernus.gui.portfolio import dialogs
from avernus.objects import portfolio_transaction, position
from gi.repository import Gtk
import datetime


class BuyDialog:

    def __init__(self, pf, transaction=None, parent=None):
        self.pf = pf
        self.transaction = transaction

        builder = Gtk.Builder()
        builder.add_from_file(get_ui_file("portfolio/buy_dialog.glade"))

        self.dlg = builder.get_object("dialog")
        self.shares_entry = builder.get_object("shares_entry")
        self.price_entry = builder.get_object("price_entry")
        self.costs_entry = builder.get_object("costs_entry")
        self.total_entry = builder.get_object("total_entry")
        self.calendar = builder.get_object("calendar")
        grid = builder.get_object("grid")

        self.dlg.set_transient_for(parent)
        self.dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                      Gtk.STOCK_APPLY, Gtk.ResponseType.ACCEPT)
        self.dlg.set_response_sensitive(Gtk.ResponseType.ACCEPT, False)
        self.on_change()

        # asset entry
        if not self.transaction:
            self.asset_selector = dialogs.StockSelector()
            grid.attach(self.asset_selector, 0, 1, 3, 1)
            self.asset_selector.result_tree.connect('cursor-changed', self.on_asset_selection)
            self.asset_selector.result_tree.get_model().connect('row-deleted', self.on_asset_deselection)
        else:
            self.shares_entry.set_value(self.transaction.quantity)
            self.total_entry.set_value(-self.transaction.total)
            self.costs_entry.set_value(self.transaction.cost)
            self.calendar.select_month(self.transaction.date.month - 1, self.transaction.date.year)
            self.calendar.select_day(self.transaction.date.day)
            self.on_change()

        # info bar to show warnings
        self.infobar = Gtk.InfoBar()
        self.infobar.set_message_type(Gtk.MessageType.WARNING)
        content = self.infobar.get_content_area()
        label = Gtk.Label(label=_('Buy dates can not be in the future.'))
        image = Gtk.Image()
        image.set_from_stock(Gtk.STOCK_DIALOG_WARNING, Gtk.IconSize.DIALOG)
        content.pack_start(image, True, True, 0)
        content.pack_start(label, True, True, 0)
        self.dlg.get_content_area().pack_start(self.infobar, True, True, 0)

        builder.connect_signals(self)

        self.date_ok = True
        if self.transaction:
            self.asset_ok = True
            self.position = transaction.position
            self.dlg.set_response_sensitive(Gtk.ResponseType.ACCEPT, True)
        else:
            self.asset_ok = False
            self.position = None
            self.dlg.set_response_sensitive(Gtk.ResponseType.ACCEPT, False)

        self.dlg.run()

    def on_day_selected(self, calendar):
        year, month, day = calendar.get_date()
        date = datetime.datetime(year, month + 1, day)
        if date > datetime.datetime.today():
            self.infobar.show_all()
            self.date_ok = False
        else:
            self.infobar.hide()
            self.date_ok = True
        self.set_response_sensitivity()

    def on_change(self, widget=None):
        price = self.total_entry.get_value() - self.costs_entry.get_value()
        price_per_share = price / self.shares_entry.get_value()
        self.price_entry.set_value(price_per_share)

    def on_asset_selection(self, *args):
        self.asset_ok = True
        asset = self.asset_selector.get_asset()
        #TODO update does not work
        datasource_controller.update_asset(asset)
        if asset != None:
            self.price_entry.set_value(asset.price)
            self.set_response_sensitivity()
        else:
            logger.error("Asset is None")

    def on_asset_deselection(self, *args):
        self.asset_ok = False
        self.set_response_sensitivity()

    def set_response_sensitivity(self):
        if self.asset_ok and self.date_ok:
            self.dlg.set_response_sensitive(Gtk.ResponseType.ACCEPT, True)
        else:
            self.dlg.set_response_sensitive(Gtk.ResponseType.ACCEPT, False)

    def on_response(self, widget, response):
        if not self.transaction:
            self.asset_selector.stop_search()
            ass = self.asset_selector.get_asset()
        else:
            ass = self.transaction.position.asset

        if response == Gtk.ResponseType.ACCEPT:
            total = self.total_entry.get_value()
            year, month, day = self.calendar.get_date()
            date = datetime.date(year, month + 1, day)
            ta_costs = self.costs_entry.get_value()
            shares = self.shares_entry.get_value()
            price = total - ta_costs

            if shares == 0.0:
                return
            if self.transaction:
                self.transaction.price = total - ta_costs
                self.transaction.date = date
                self.transaction.quantity = shares
                self.transaction.cost = ta_costs
            else:
                self.position = position.get_position(portfolio=self.pf, asset=ass)
                if not self.position:
                    self.position = position.PortfolioPosition(price=price,
                                                           quantity=shares,
                                                           portfolio=self.pf,
                                                           asset=ass)
                    self.position.date = date
                portfolio_transaction.BuyTransaction(date=date, quantity=shares,
                                     price=price, cost=ta_costs,
                                     position=self.position)
                self.position.recalculate()
        self.dlg.destroy()
