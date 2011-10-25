from avernus import config
from avernus.controller import controller
from avernus.gui import gui_utils
from gi.repository import Gtk
import os
from gi.repository import Pango
import time
import csv

class ExportDialog(Gtk.Dialog):

    TITLE = _('Export Account Transactions')

    def __init__(self, parent=None, account =None):
        Gtk.Dialog.__init__(self, self.TITLE, parent
                            , Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                     (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,))
        self.account = account
        self.config = config.avernusConfig()
        self.transactions = []
        self._init_widgets()

        response = self.run()
        self.process_result(response = response)

    def _init_widgets(self):
        self.export_button = self.add_button('Export', Gtk.ResponseType.ACCEPT)
        self.export_button.set_sensitive(False)
        vbox = self.get_content_area()
        fileBox = Gtk.HBox()
        vbox.pack_start(fileBox, False, False, 0)
        fileBox.pack_start(Gtk.Label(_('Location to export')), False, False, 0)
        self.fcbutton = Gtk.FileChooserButton()
        self.fcbutton.set_title(_('Folder to export to'))
        self.fcbutton.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
        self.file = None
        self.fcbutton.connect('file-set', self._on_file_set)
        folder = self.config.get_option('last_export_folder')
        if folder is not None:
            self.fcbutton.set_current_folder(folder)
            self.folder = folder
        fileBox.pack_start(self.fcbutton, True, True, 0)
        accBox = Gtk.HBox()
        vbox.pack_start(accBox, False, False, 0)
        accBox.pack_start(Gtk.Label('Target account'), False, False, 0)
        model = Gtk.ListStore(object, str)
        i = 0
        active = -1
        for account in controller.getAllAccount():
            model.append([account, account.name])
            if self.account == account:
                active = i
            i+=1
        self.account_cb = Gtk.ComboBox()
        self.account_cb.set_model(model)
        if active>-1:
            self.account_cb.set_active(active)
        cell = Gtk.CellRendererText()
        self.account_cb.pack_start(cell, True)
        self.account_cb.add_attribute(cell, 'text', 1)
        self.account_cb.connect('changed', self._on_account_changed)
        accBox.pack_start(self.account_cb, False, True, 0)
        frame = Gtk.Frame()
        frame.set_label('Transactions')
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC,Gtk.PolicyType.AUTOMATIC)
        self.tree = TransactionTree()
        frame.add(sw)

        sw.add(self.tree)
        vbox.pack_start(frame, True, True, 0)
        self.show_all()

    def _on_file_set(self, button):
        self.folder = button.get_current_folder()
        self.config.set_option('last_export_folder', self.folder)


    def _on_account_changed(self, *args):
        self.b_account = True
        self.account = self.account_cb.get_model()[self.account_cb.get_active()][0]
        self.tree.reload(self.account)
        self.export_button.set_sensitive(True)

    def process_result(self, widget=None, response = Gtk.ResponseType.ACCEPT):
        if response == Gtk.ResponseType.ACCEPT:
            # gather the transactions
            self.transactions = self.tree.getExportTransactions()
            # generate the filename
            name = "avernusAccountExport_v1_"
            name += self.account.name
            name += "_" + str(int(time.time()))
            name += ".csv"
            path = os.path.join(self.folder, name)
            with open(path, 'wb') as file:
                writer = csv.writer(file)
                for transaction in self.transactions:
                    writer.writerow([transaction.date, transaction.amount,
                                     transaction.description, transaction.category])
        self.destroy()

class TransactionTree(gui_utils.Tree):

    OBJECT = 0
    DATE = 1
    AMOUNT = 2
    DESC = 3
    EXPORT = 4

    def __init__(self):
        gui_utils.Tree.__init__(self)
        self.set_rules_hint(True)
        self.set_size_request(700,400)
        self.model = Gtk.ListStore(object, object, float, str, bool)
        self.set_model(self.model)

        column, cell = self.create_check_column('export?', self.EXPORT)
        cell.connect("toggled", self.on_toggled)
        column, cell = self.create_column('date', self.DATE, func=gui_utils.date_to_string)
        column.add_attribute(cell, 'foreground', 5)
        cell.set_property('foreground-set', True)
        column, cell = self.create_column('amount', self.AMOUNT, func=gui_utils.currency_format)
        column.add_attribute(cell, 'foreground', 5)
        cell.set_property('foreground-set', True)
        column, cell = self.create_column('description', self.DESC)
        column.add_attribute(cell, 'foreground', 5)
        cell.set_property('foreground-set', True)
        cell.props.wrap_mode = Pango.WrapMode.WORD
        cell.props.wrap_width = 300

    def getExportTransactions(self):
        erg = []
        for line in self.model:
            obj = line[self.OBJECT]
            export = line[self.EXPORT]
            if export:
                erg.append(obj)
        return erg

    def on_toggled(self, cellrenderertoggle, path):
        self.model[path][self.EXPORT] = not self.model[path][self.EXPORT]

    def reload(self, account):
        self.clear()
        self.account = account
        model = self.get_model()
        for trans in account:
            model.append([trans, trans.date, trans.amount, trans.description, True])
