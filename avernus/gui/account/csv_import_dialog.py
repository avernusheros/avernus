#!/usr/bin/env python
from avernus import csvimporter, config
from avernus.gui import gui_utils, get_ui_file
from avernus.objects import account
from gi.repository import Gtk, Pango, GLib
import os


class CSVImportDialog(object):

    def __init__(self, account=None, parent=None):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(get_ui_file("account/import_csv_dialog.glade"))
        self.dlg = self.builder.get_object("dialog")
        self.dlg.set_transient_for(parent)
        self.import_button = self.builder.get_object("import_button")
        self.builder.connect_signals(self)

        self.account = account
        self.config = config.avernusConfig()
        self.importer = csvimporter.CsvImporter()
        self.b_categories = self.config.get_option('category_assignments_on_import') == 'True'
        self.importer.do_categories = self.b_categories
        self.b_file = False
        self.b_account = not account is None

        self._init_widgets()
        self.dlg.show_all()
        response = self.dlg.run()
        self.process_result(response=response)

    def _init_widgets(self):
        self.fcbutton = self.builder.get_object("file_chooser")
        self.account_cb = self.builder.get_object("account_combobox")
        category_assignment_button = self.builder.get_object("assignment_button")
        self.filename = None
        folder = self.config.get_option('last_csv_folder')
        if folder is not None:
            self.fcbutton.set_current_folder(folder)
        model = self.builder.get_object("account_liststore")
        i = 0
        active = -1
        for acc in account.get_all_accounts():
            model.append([acc, acc.name])
            if self.account == acc:
                active = i
            i += 1

        if active > -1:
            self.account_cb.set_active(active)

        category_assignment_button.set_active(self.b_categories)
        sw = self.builder.get_object("sw")
        self.tree = PreviewTree()
        sw.add(self.tree)

    def process_result(self, widget=None, response=Gtk.ResponseType.ACCEPT):
        if response == Gtk.ResponseType.ACCEPT:
            self.account_cb.get_model()
            self.importer.create_transactions(self.account)
        self.dlg.destroy()

    def on_toggle_assignments(self, button):
        self.importer.do_categories = self.b_categories = button.get_active()
        self.config.set_option('category_assignments_on_import', self.b_categories)
        if self.b_file:
            self.importer.check_categories()
            self.tree.refresh(self.importer.results)

    def on_file_set(self, button):
        self.b_file = True
        self.filename = button.get_filename()
        self.dlg.set_title(_('Import CSV') + ' - ' + os.path.basename(self.filename))
        last_folder = button.get_current_folder()
        # last folder is None if Gnome's recent files was used
        if last_folder:
            self.config.set_option('last_csv_folder', last_folder)
            self.fcbutton.set_current_folder(last_folder)
        try:
            self.importer.load_transactions_from_csv(self.filename)
        except:
            self.show_import_error_dialog()
            return
        if self.b_account:
            self.import_button.set_sensitive(True)
            self.importer.check_duplicates(self.account)
        self.tree.refresh(self.importer.results)

    def on_account_changed(self, *args):
        self.b_account = True
        self.account = self.account_cb.get_model()[self.account_cb.get_active()][0]
        if self.b_file:
            self.import_button.set_sensitive(True)
            self.importer.check_duplicates(self.account)
            self.tree.refresh(self.importer.results)

    def show_import_error_dialog(self):
        text = _("Avernus was unable to parse your csv file.") + "\n"
        text += "-" + _("Is the submitted file a csv?") + "\n"
        text += "-" + _("Using a csv with more data might give better results.") + "\n"
        text += "-" + _("Maybe you want to report a bug.")
        dlg = Gtk.MessageDialog(None, Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.ERROR, Gtk.ButtonsType.CLOSE, text)
        dlg.run()
        dlg.destroy()


class PreviewTree(gui_utils.Tree):
    COLOR_DUPLICATES = 'grey'

    def __init__(self):
        gui_utils.Tree.__init__(self)
        self.set_rules_hint(True)

        self.set_size_request(700, 400)
        self.model = Gtk.ListStore(object, str, float, bool, str, str)
        self.set_model(self.model)

        column, cell = self.create_check_column('', 3)
        cell.connect("toggled", self.on_toggled)
        column, cell = self.create_column(_('Date'), 0, func=gui_utils.date_to_string)
        column.add_attribute(cell, 'foreground', 5)
        cell.set_property('foreground-set', True)
        column, cell = self.create_column(_('Description'), 1)
        column.add_attribute(cell, 'foreground', 5)
        cell.set_property('foreground-set', True)
        cell.props.wrap_mode = Pango.WrapMode.WORD
        cell.props.wrap_width = 300
        column, cell = self.create_column(_('Amount'), 2, func=gui_utils.currency_format)
        column.add_attribute(cell, 'foreground', 5)
        cell.set_property('foreground-set', True)
        column, cell = self.create_column(_('Category'), 4)
        column.add_attribute(cell, 'foreground', 5)
        cell.set_property('foreground-set', True)

    def refresh(self, transactions):
        self.transactions = transactions
        self.clear()
        model = self.get_model()
        for trans in transactions:
            if trans.b_import:
                color = 'black'
            else:
                color = self.COLOR_DUPLICATES
            if trans.category:
                if type(trans.category) == type(unicode()):
                    cat = trans.category
                else:
                    cat = trans.category.name
            else:
                cat = ''
            model.append([trans.date, GLib.markup_escape_text(trans.description), trans.amount, trans.b_import, cat, color])

    def on_toggled(self, cellrenderertoggle, path):
        self.model[path][3] = self.transactions[int(path)].b_import = not self.model[path][3]
