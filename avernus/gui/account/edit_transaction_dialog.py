from avernus.gui import gui_utils
from avernus.objects import account
from gi.repository import Gtk, Pango
import datetime


class EditTransactionDialog(Gtk.Dialog):

    def __init__(self, acc, transaction=None, parent=None):
        Gtk.Dialog.__init__(self, _("Edit transaction"), parent
                , Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                     (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                      Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        self.transaction = transaction
        self.account = acc
        vbox = self.get_content_area()

        #description
        frame = Gtk.Frame(label='Description')
        self.description_entry = Gtk.TextView()
        self.description_entry.set_wrap_mode(Gtk.WrapMode.WORD)
        entry_buffer = self.description_entry.get_buffer()
        frame.add(self.description_entry)
        vbox.pack_start(frame, True, True, 0)

        #amount
        hbox = Gtk.HBox()
        label = Gtk.Label(label=_('Amount'))
        hbox.pack_start(label, False, False, 0)
        self.amount_entry = Gtk.SpinButton(adjustment=Gtk.Adjustment(lower= -999999999, upper=999999999, step_increment=10, value=0.0), digits=2)
        hbox.pack_start(self.amount_entry, True, True, 0)
        vbox.pack_start(hbox, False, False, 0)

        #category
        if self.transaction:
            active_category = self.transaction.category
        else:
            active_category = None
        hbox = Gtk.HBox()
        label = Gtk.Label(label=_('Category'))
        hbox.pack_start(label, False, False, 0)
        treestore = Gtk.TreeStore(object, str)
        self.combobox = Gtk.ComboBox(model=treestore)
        cell = Gtk.CellRendererText()
        self.combobox.pack_start(cell, False)
        self.combobox.add_attribute(cell, 'text', 1)

        def insert_recursive(cat, parent):
            new_iter = treestore.append(parent, [cat, cat.name])
            if active_category == cat:
                self.combobox.set_active_iter(new_iter)
            for child_cat in cat.children:
                insert_recursive(child_cat, new_iter)
        new_iter = treestore.append(None, [None, 'None'])
        if active_category == None:
            self.combobox.set_active_iter(new_iter)
        root_categories = account.get_root_categories()
        for cat in root_categories:
            insert_recursive(cat, None)

        hbox.pack_start(self.combobox, False, False, 0)
        vbox.pack_start(hbox, False, False, 0)

        #date
        self.calendar = Gtk.Calendar()
        vbox.pack_start(self.calendar, False, False, 0)

        #transfer
        text = "Transfer: this transaction will not be shown in any of the graphs."
        self.transfer_button = Gtk.CheckButton(text)
        vbox.pack_start(self.transfer_button, False, False, 0)

        self.matching_transactions_tree = gui_utils.Tree()
        model = Gtk.ListStore(object, str, str, object)
        self.matching_transactions_tree.set_model(model)
        self.matching_transactions_tree.create_column(_('Account'), 1)
        col, cell = self.matching_transactions_tree.create_column(_('Description'), 2)
        cell.props.wrap_width = 200
        cell.props.wrap_mode = Pango.WrapMode.WORD
        self.matching_transactions_tree.create_column(_('Date'), 3, func=gui_utils.date_to_string)
        vbox.pack_end(self.matching_transactions_tree, True, True, 0)
        self.no_matches_label = Gtk.Label(label='No matching transactions found. Continue only if you want to mark this as a tranfer anyway.')
        vbox.pack_end(self.no_matches_label, True, True, 0)

        if self.transaction:
            entry_buffer.set_text(self.transaction.description)
            self.amount_entry.set_value(self.transaction.amount)
            self.calendar.select_month(self.transaction.date.month - 1, self.transaction.date.year)
            self.calendar.select_day(self.transaction.date.day)
            if self.transaction.transfer:
                self.transfer_button.set_active(True)
        else:
            today = datetime.date.today()
            self.calendar.select_month(today.month - 1, today.year)
            self.calendar.select_day(today.day)

        #connect signals
        self.transfer_button.connect("toggled", self.on_transfer_toggled)
        self.matching_transactions_tree.connect('cursor_changed', self.on_transfer_transaction_selected)

    def start(self):
        self.show_all()
        self.matching_transactions_tree.hide()
        self.no_matches_label.hide()
        return self.process_result(self.run())

    def on_transfer_toggled(self, checkbutton):
        if checkbutton.get_active():
            found_one = False
            for ta in self.transaction.yield_matching_transfer_transactions():
                if found_one == False:
                    self.matching_transactions_tree.clear()
                    self.matching_transactions_tree.show()
                    found_one = True
                self.matching_transactions_tree.get_model().append([ta, ta.account.name, ta.description, ta.date])
            self.transfer_transaction = self.transaction
            if not found_one:
                self.no_matches_label.show()
        else:
            self.matching_transactions_tree.hide()
            self.no_matches_label.hide()

    def on_transfer_transaction_selected(self, widget):
        selection = widget.get_selection()
        if selection:
            treestore, selection_iter = selection.get_selected()
            if (selection_iter and treestore):
                self.transfer_transaction = treestore.get_value(selection_iter, 0)

    def process_result(self, response):
        if response == Gtk.ResponseType.ACCEPT:
            buffer = self.description_entry.get_buffer()
            description = unicode(buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True), encoding="utf8")
            amount = self.amount_entry.get_value()
            year, month, day = self.calendar.get_date()
            date = datetime.date(year, month + 1, day)
            if iter is None:
                category = None
            else:
                category = self.combobox.get_model()[self.combobox.get_active_iter()][0]

            if self.transaction is None:
                self.transaction = account.AccountTransaction(
                                            account=self.account,
                                            description=description,
                                            amount=amount,
                                            date=date,
                                            category=category)
            else:
                self.transaction.description = description
                self.transaction.amount = amount
                self.transaction.date = date
                self.transaction.category = category

            if self.transfer_button.get_active():
                # only set if the transfer button is toggled
                if self.transfer_transaction:
                    self.transaction.transfer = self.transfer_transaction
                    self.transfer_transaction.transfer = self.transaction
            elif self.transaction.transfer is not None:
                self.transaction.transfer.transfer = None
                self.transaction.transfer = None
        self.destroy()
        return response == Gtk.ResponseType.ACCEPT, self.transaction
