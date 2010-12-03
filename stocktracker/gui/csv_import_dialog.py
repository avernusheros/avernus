#!/usr/bin/env python

import gtk
from stocktracker.gui import gui_utils
from stocktracker import csvimporter
from stocktracker.objects import controller


class CSVImportDialog(gtk.Dialog):
    
    def __init__(self, *args):
        gtk.Dialog.__init__(self, _("Import CSV"), None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,))
        
        self._init_widgets()
        self.importer = csvimporter.CsvImporter()
        self.profile = {}
        self.b_file = False
        self.b_account = False
        
        response = self.run()  
        self.process_result(response = response)

    def _init_widgets(self):
        self.import_button = self.add_button('Import', gtk.RESPONSE_ACCEPT)
        self.import_button.set_sensitive(False)
        vbox = self.get_content_area()
        fileBox = gtk.HBox()
        vbox.pack_start(fileBox, fill=False, expand=False)
        fileBox.pack_start(gtk.Label('File to import'), fill=False, expand=False)
        self.fcbutton = gtk.FileChooserButton('File to import')
        self.file = None
        self.fcbutton.connect('file-set', self._on_file_set)
        fileBox.pack_start(self.fcbutton, fill=True)
        accBox = gtk.HBox()
        vbox.pack_start(accBox, fill=False, expand=False)
        accBox.pack_start(gtk.Label('Target account'), fill=False, expand=False)
        model = gtk.ListStore(object, str)
        for account in controller.getAllAccount():
            model.append([account, account.name])
        self.account_cb = gtk.ComboBox(model)
        cell = gtk.CellRendererText()
        self.account_cb.pack_start(cell, True)
        self.account_cb.add_attribute(cell, 'text', 1)
        self.account_cb.connect('changed', self._on_account_changed)
        accBox.pack_start(self.account_cb, fill=False, expand=False)
        frame = gtk.Frame('Preview')
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
        self.tree = PreviewTree()
        sw.connect_after('size-allocate', 
                         gui_utils.resize_wrap, 
                         self.tree, 
                         self.tree.dynamicWrapColumn, 
                         self.tree.dynamicWrapCell)
        frame.add(sw)
        
        sw.add(self.tree)
        vbox.pack_start(frame)
        self.show_all()

    def process_result(self, widget=None, response = gtk.RESPONSE_ACCEPT):
        if response == gtk.RESPONSE_ACCEPT:
            model = self.account_cb.get_model()
            self.importer.create_transactions(self.account)
        self.destroy()  

    def _on_file_set(self, button):
        self.b_file = True
        self.file = button.get_filename()
        self.fcbutton.set_current_folder(button.get_current_folder())
        self.importer.load_transactions_from_csv(self.file)
        if self.b_account:
            self.import_button.set_sensitive(True)
            self.importer.check_duplicates(self.account)
        self.tree.reload(self.importer.results)
    
    def _on_account_changed(self, *args):
        self.b_account = True
        self.account = self.account_cb.get_model()[self.account_cb.get_active()][0]
        if self.b_file:
            self.import_button.set_sensitive(True)
            self.importer.check_duplicates(self.account)
            self.tree.reload(self.importer.results)


class PreviewTree(gui_utils.Tree):
    COLOR_DUPLICATES = 'grey'
    
    def __init__(self):
        gui_utils.Tree.__init__(self)
        self.set_rules_hint(True)
        
        self.set_size_request(700,400)
        self.model = gtk.ListStore(str, str, float, bool, str)
        self.set_model(self.model)
        
        column, cell = self.create_check_column('import?', 3)
        cell.connect("toggled", self.on_toggled)
        column, cell = self.create_column('date', 0)
        column.add_attribute(cell, 'foreground', 4)
        cell.set_property('foreground-set', True)
        column, cell = self.create_column('description', 1)
        column.add_attribute(cell, 'foreground', 4)
        cell.set_property('foreground-set', True)
        self.dynamicWrapColumn = column
        self.dynamicWrapCell = cell
        cell.props.wrap_mode = gtk.WRAP_WORD
        column, cell = self.create_column('amount', 2, func=gui_utils.float_to_string)
        column.add_attribute(cell, 'foreground', 4)
        cell.set_property('foreground-set', True)
    
    def reload(self, transactions):
        self.transactions = transactions
        self.clear()
        model = self.get_model()
        for trans in transactions:
            if trans[-1]:
                color = 'black'
            else:
                color = self.COLOR_DUPLICATES
            model.append(trans+[color])

    def on_toggled(self, cellrenderertoggle, path):
        self.model[path][3] = self.transactions[int(path)][3] = not self.model[path][3]
