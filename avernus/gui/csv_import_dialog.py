#!/usr/bin/env python

from gi.repository import Gtk
import os
from gi.repository import Pango
from avernus.gui import gui_utils
from avernus import csvimporter, config
from avernus.controller import controller


class CSVImportDialog(Gtk.Dialog):

    TITLE = _("Import CSV")

    def __init__(self, widget=None, account=None):
        Gtk.Dialog.__init__(self, self.TITLE, None
                            , Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                     (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,))
        self.account = account
        self.config = config.avernusConfig()
        self._init_widgets()
        self.importer = csvimporter.CsvImporter()
        self.profile = {}
        self.b_file = False
        if account is None:
            self.b_account = False
        else:
            self.b_account = True
        response = self.run()
        self.process_result(response = response)

    def _init_widgets(self):
        self.import_button = self.add_button('Import', Gtk.ResponseType.ACCEPT)
        self.import_button.set_sensitive(False)
        vbox = self.get_content_area()
        fileBox = Gtk.HBox()
        vbox.pack_start(fileBox, False, False, 0)
        fileBox.pack_start(Gtk.Label('File to import'), False, False, 0)
        self.fcbutton = Gtk.FileChooserButton()
        self.fcbutton.set_title(_('File to import'))
        self.file = None
        self.fcbutton.connect('file-set', self._on_file_set)
        folder = self.config.get_option('last_csv_folder')
        if folder is not None:
            self.fcbutton.set_current_folder(folder)
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

        if self.config.get_option('category_assignments_on_import') == 'True':
            self.b_assignments = True
        else:
            self.b_assignments = False
        category_assignment_button = Gtk.CheckButton(label=_('Do category assignments'))
        category_assignment_button.set_active(self.b_assignments)
        accBox.pack_start(category_assignment_button, True, True, 0)
        category_assignment_button.connect('toggled', self.on_toggle_assignments)

        frame = Gtk.Frame()
        frame.set_label('Preview')
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC,Gtk.PolicyType.AUTOMATIC)
        self.tree = PreviewTree()
        frame.add(sw)

        sw.add(self.tree)
        vbox.pack_start(frame, True, True, 0)
        self.show_all()

    def process_result(self, widget=None, response = Gtk.ResponseType.ACCEPT):
        if response == Gtk.ResponseType.ACCEPT:
            model = self.account_cb.get_model()
            self.importer.create_transactions(self.account)
        self.destroy()

    def on_toggle_assignments(self, button):
        self.b_assignments = button.get_active()
        self.config.set_option('category_assignments_on_import', self.b_assignments)
        if self.b_file:
            self.importer.set_categories(self.b_assignments)
            self.tree.reload(self.importer.results)

    def _on_file_set(self, button):
        self.b_file = True
        self.file = button.get_filename()
        self.set_title(self.TITLE+' - '+os.path.basename(self.file))
        self.config.set_option('last_csv_folder', button.get_current_folder())
        self.fcbutton.set_current_folder(button.get_current_folder())
        self.importer.load_transactions_from_csv(self.file)
        if self.b_account:
            self.import_button.set_sensitive(True)
            self.importer.check_duplicates(self.account)
            self.importer.set_categories(self.b_assignments)
        self.tree.reload(self.importer.results)

    def _on_account_changed(self, *args):
        self.b_account = True
        self.account = self.account_cb.get_model()[self.account_cb.get_active()][0]
        if self.b_file:
            self.import_button.set_sensitive(True)
            self.importer.check_duplicates(self.account)
            self.importer.set_categories(self.b_assignments)
            self.tree.reload(self.importer.results)


class PreviewTree(gui_utils.Tree):
    COLOR_DUPLICATES = 'grey'

    def __init__(self):
        gui_utils.Tree.__init__(self)
        self.set_rules_hint(True)

        self.set_size_request(700,400)
        self.model = Gtk.ListStore(object, str, float, bool, str, str)
        self.set_model(self.model)

        column, cell = self.create_check_column('import?', 3)
        cell.connect("toggled", self.on_toggled)
        column, cell = self.create_column('date', 0, func=gui_utils.date_to_string)
        column.add_attribute(cell, 'foreground', 5)
        cell.set_property('foreground-set', True)
        column, cell = self.create_column('description', 1)
        column.add_attribute(cell, 'foreground', 5)
        cell.set_property('foreground-set', True)
        cell.props.wrap_mode = Pango.WrapMode.WORD
        cell.props.wrap_width = 300
        column, cell = self.create_column('amount', 2, func=gui_utils.currency_format)
        column.add_attribute(cell, 'foreground', 5)
        cell.set_property('foreground-set', True)
        column, cell = self.create_column('category', 4)
        column.add_attribute(cell, 'foreground', 5)
        cell.set_property('foreground-set', True)

    def reload(self, transactions):
        self.transactions = transactions
        self.clear()
        model = self.get_model()
        for trans in transactions:
            if trans.b_import:
                color = 'black'
            else:
                color = self.COLOR_DUPLICATES
            model.append([trans.date, trans.description, trans.amount, trans.b_import, trans.category, color])

    def on_toggled(self, cellrenderertoggle, path):
        self.model[path][3] = self.transactions[int(path)].b_import = not self.model[path][3]
