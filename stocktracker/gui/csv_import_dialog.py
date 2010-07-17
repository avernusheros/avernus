#!/usr/bin/env python

import gtk
from stocktracker.gui.gui_utils import Tree, float_to_string, resize_wrap
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
        fcbutton = gtk.FileChooserButton('File to import')
        self.file = None
        fcbutton.connect('file-set', self._on_file_set)
        fileBox.pack_start(fcbutton, fill=True)
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
                         resize_wrap, 
                         self.tree, 
                         self.tree.dynamicWrapColumn, 
                         self.tree.dynamicWrapCell)
        frame.add(sw)
        
        sw.add(self.tree)
        vbox.pack_start(frame)
        #table.attach(frame, 0,3,2,3)
        self.show_all()

    def process_result(self, widget=None, response = gtk.RESPONSE_ACCEPT):
        if response == gtk.RESPONSE_ACCEPT:
            model = self.account_cb.get_model()
            print "do import to account", model[self.account_cb.get_active()][1]
            account = model[self.account_cb.get_active()][0]
            self.importer.create_transactions(account)
        self.destroy()  

    def _on_refresh(self, *args):
        transactions = self.importer.get_transactions_from_csv(self.file)
        self.tree.reload(transactions)

    def _on_file_set(self, button):
        self.b_file = True
        if self.b_account:
            self.import_button.set_sensitive(True)
        self.file = button.get_filename()
        self._on_refresh()
    
    def _on_account_changed(self, *args):
        self.b_account = True
        if self.b_file:
            self.import_button.set_sensitive(True)
            
        

class PreviewTree(Tree):
    
    def __init__(self):
        Tree.__init__(self)
        self.set_rules_hint(True)
        
        self.set_size_request(700,400)
        model = gtk.ListStore(str, str, float)
        self.set_model(model)
        
        self.create_column('date', 0)
        column, cell = self.create_column('description', 1)
        self.dynamicWrapColumn = column
        self.dynamicWrapCell = cell
        cell.props.wrap_mode = gtk.WRAP_WORD
        self.create_column('amount', 2, func=float_to_string)
    
    def reload(self, transactions):
        self.clear()
        model = self.get_model()
        for trans in transactions:
            model.append(trans)

