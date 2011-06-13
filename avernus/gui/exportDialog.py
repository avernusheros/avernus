'''
Created on 12 Jun 2011

@author: bastian
'''
from avernus import config
from avernus.controller import controller
from avernus.gui.csv_import_dialog import PreviewTree
import gtk
import os

class ExportDialog(gtk.Dialog):
    
    TITLE = _('Export Account Transactions')

    def __init__(self, widget=None, account=None):
        gtk.Dialog.__init__(self, self.TITLE, None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,))
        print "alive"
        self.account = account
        self.config = config.avernusConfig()
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
        self.tree = PreviewTree()
        frame.add(sw)

        sw.add(self.tree)
        vbox.pack_start(frame)
        self.show_all()
        
    def _on_file_set(self, button):
        self.file = button.get_filename()
        self.set_title(self.TITLE+' - '+os.path.basename(self.file))
        self.config.set_option('last_export_folder', button.get_current_folder())
        self.fcbutton.set_current_folder(button.get_current_folder())
        print button.get_current_folder()
        #self.tree.reload(self.importer.results)

    def _on_account_changed(self, *args):
        self.b_account = True
        self.account = self.account_cb.get_model()[self.account_cb.get_active()][0]
        
    def process_result(self, widget=None, response = gtk.RESPONSE_ACCEPT):
        if response == gtk.RESPONSE_ACCEPT:
            print "ACCEPT!!"
        self.destroy()
        