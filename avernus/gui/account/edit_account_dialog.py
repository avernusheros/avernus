#!/usr/bin/env python
from avernus.objects import account as account_m
from avernus.gui import get_ui_file
from gi.repository import Gtk


class EditAccountDialog:

    def __init__(self, account, parent):
        self.account = account
        builder = Gtk.Builder()
        builder.add_from_file(get_ui_file("account/edit_account_dialog.glade"))
        self.dlg = builder.get_object("dialog")
        self.dlg.set_transient_for(parent.tree.get_toplevel())
        self.name_entry = builder.get_object("name_entry")
        self.name_entry.set_text(account.name)
        self.balance_entry = builder.get_object("balance_entry")
        adjustment = builder.get_object("adjustment1")
        adjustment.set_value(account.balance)
        self.combobox = builder.get_object("type_combobox")
        liststore = Gtk.ListStore(int, str)
        self.combobox.set_model(liststore)
        cell = Gtk.CellRendererText()
        self.combobox.pack_start(cell, True)
        self.combobox.add_attribute(cell, 'text', 1)
        for account_type, name in account_m.yield_account_types():
            iterator = liststore.append([account_type, name])
            if account_type == account.type:
                self.combobox.set_active_iter(iterator)

        self.dlg.add_buttons(Gtk.STOCK_CLOSE, Gtk.ResponseType.ACCEPT)
        self.dlg.connect('response', self.on_response)
        self.dlg.show()

    def on_response(self, widget, response):
        self.account.name = self.name_entry.get_text()
        # FIXME
        #
        self.account.balance = self.balance_entry.get_value()
        # self.get_model()[row][3] = gui_utils.get_currency_format_from_float(acc.balance)
        self.account.type = self.combobox.get_model()[self.combobox.get_active_iter()][0]
        self.dlg.destroy()
