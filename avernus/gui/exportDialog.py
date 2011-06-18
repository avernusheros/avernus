'''
Created on 12 Jun 2011

@author: bastian
'''
from avernus import config
from avernus.controller import controller
from avernus.gui import gui_utils
from avernus.gui.csv_import_dialog import PreviewTree
import gtk
import os
import pango
import time
import csv

class ExportDialog(gtk.Dialog):
    
    TITLE = _('Export Account Transactions')

    def __init__(self, widget=None, account=None):
        gtk.Dialog.__init__(self, self.TITLE, None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,))
        self.account = account
        self.config = config.avernusConfig()
        self.transactions = []
        self._init_widgets()
        
        response = self.run()
        self.process_result(response = response)
        
    def _init_widgets(self):
        self.export_button = self.add_button('Export', gtk.RESPONSE_ACCEPT)
        self.export_button.set_sensitive(False)
        vbox = self.get_content_area()
        fileBox = gtk.HBox()
        vbox.pack_start(fileBox, fill=False, expand=False)
        fileBox.pack_start(gtk.Label('Location to export'), fill=False, expand=False)
        self.fcbutton = gtk.FileChooserButton('Folder to export to')
        self.fcbutton.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        self.file = None
        self.fcbutton.connect('file-set', self._on_file_set)
        folder = self.config.get_option('last_export_folder')
        if folder is not None:
            self.fcbutton.set_current_folder(folder)
            self.folder = folder
        fileBox.pack_start(self.fcbutton, fill=True)
        accBox = gtk.HBox()
        vbox.pack_start(accBox, fill=False, expand=False)
        accBox.pack_start(gtk.Label('Target account'), fill=False, expand=False)
        model = gtk.ListStore(object, str)
        i = 0
        active = -1
        for account in controller.getAllAccount():
            model.append([account, account.name])
            if self.account == account:
                active = i
            i+=1
        self.account_cb = gtk.ComboBox(model)
        if active>-1:
            self.account_cb.set_active(active)
        cell = gtk.CellRendererText()
        self.account_cb.pack_start(cell, True)
        self.account_cb.add_attribute(cell, 'text', 1)
        self.account_cb.connect('changed', self._on_account_changed)
        accBox.pack_start(self.account_cb, fill=False, expand=True)
        frame = gtk.Frame('Transactions')
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
        self.tree = TransactionTree()
        frame.add(sw)

        sw.add(self.tree)
        vbox.pack_start(frame)
        self.show_all()
        
    def _on_file_set(self, button):
        self.folder = button.get_current_folder()
        self.config.set_option('last_export_folder', self.folder)
        

    def _on_account_changed(self, *args):
        self.b_account = True
        self.account = self.account_cb.get_model()[self.account_cb.get_active()][0]
        self.tree.reload(self.account)
        self.export_button.set_sensitive(True)
        
    def process_result(self, widget=None, response = gtk.RESPONSE_ACCEPT):
        if response == gtk.RESPONSE_ACCEPT:
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
        self.model = gtk.ListStore(object, str, float, str, bool)
        self.set_model(self.model)
        
        column, cell = self.create_check_column('export?', self.EXPORT)
        cell.connect("toggled", self.on_toggled)
        column, cell = self.create_column('date', self.DATE)
        column.add_attribute(cell, 'foreground', 5)
        cell.set_property('foreground-set', True)
        column, cell = self.create_column('amount', self.AMOUNT, func=gui_utils.currency_format)
        column.add_attribute(cell, 'foreground', 5)
        cell.set_property('foreground-set', True)
        column, cell = self.create_column('description', self.DESC)
        column.add_attribute(cell, 'foreground', 5)
        cell.set_property('foreground-set', True)
        cell.props.wrap_mode = pango.WRAP_WORD
        cell.props.wrap_width = 300
        
    def getExportTransactions(self):
        erg = []
        for line in self.model:
            object = line[self.OBJECT]
            export = line[self.EXPORT]
            if export:
                erg.append(object)
        return erg
        
    def on_toggled(self, cellrenderertoggle, path):
        self.model[path][self.EXPORT] = not self.model[path][self.EXPORT] 
        
    def reload(self, account):
        self.clear()
        self.account = account
        model = self.get_model()
        for trans in account:
            model.append([trans, trans.date, trans.amount, trans.description, True])
        