#!/usr/bin/env python

import gtk
from stocktracker.gui.gui_utils import Tree
from stocktracker import csvimporter
from stocktracker.objects import controller


class CSVImportDialog(gtk.Dialog):
    
    def __init__(self, *args):
        gtk.Dialog.__init__(self, _("Import CSV"), None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        
        self._init_widgets()
        self.importer = csvimporter.CsvImporter()
        self.profile = {}
        
        response = self.run()  
        self.process_result(response = response)

    def _init_widgets(self):
        vbox = self.get_content_area()
        table = gtk.Table()
        vbox.pack_start(table)
        
        table.attach(gtk.Label('File to import'),0,1,0,1, xoptions=0, yoptions=0)
        fcbutton = gtk.FileChooserButton('File to import')
        self.file = None
        fcbutton.connect('file-set', self._on_file_set)
        table.attach(fcbutton, 1,2,0,1, xoptions=0, yoptions=0)
        
        table.attach(gtk.Label('Target account'),0,1,1,2, xoptions=0, yoptions=0)
        self.account_cb = gtk.combo_box_new_text()
        for account in controller.getAllAccount():
            self.account_cb.append_text(account.name)
        table.attach(self.account_cb, 1,2,1,2, xoptions=0, yoptions=0)
        
        frame = gtk.Frame('Preview')
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
        frame.add(sw)
        self.tree = PreviewTree2()
        sw.add(self.tree)
        table.attach(frame, 0,3,2,3)
        self.show_all()

    def process_result(self, widget=None, response = gtk.RESPONSE_ACCEPT):
        if response == gtk.RESPONSE_ACCEPT:
            print "do import to account", self.account_cb.get_active_text()
        self.destroy()  

    def _on_refresh(self, *args):
        transactions = self.importer.get_transactions_from_csv(self.file)
        self.tree.reload(transactions)

    def _on_file_set(self, button):
        self.file = button.get_filename()
        self._on_refresh()
        

class PreviewTree2(Tree):
    
    def __init__(self):
        Tree.__init__(self)
        self.set_rules_hint(True)
        
        self.set_size_request(700,400)
        model = gtk.ListStore(str, str, float)
        self.set_model(model)
        
        self.create_column('date', 0)
        self.create_column('description', 1)
        self.create_column('amount', 2)
    
    def reload(self, transactions):
        self.clear()
        model = self.get_model()
        for trans in transactions:
            model.append(trans)
    

class PreviewTree(Tree):
    
    def __init__(self):
        Tree.__init__(self)
        self.set_rules_hint(True)
        
        self.set_size_request(700,400)
        self.cols = 20  
        temp = [str]*self.cols
        model = gtk.ListStore(*temp)
        self.set_model(model)
        
        for i in range(self.cols):
            column = gtk.TreeViewColumn()
            column.set_clickable(True)
            column.set_resizable(True)
            cb = self._get_combobox()
            column.set_widget(cb)
            self.append_column(column)
            #hack to make the comboboxes work
            button = cb.get_parent().get_parent().get_parent()
            button.connect('pressed', self.on_button_press_event, cb)
            
            cell = gtk.CellRendererText()
            column.pack_start(cell, expand = True)
            column.add_attribute(cell, "text", i)
    
    def reload(self, rows):
        self.clear()
        model = self.get_model()
        for row in rows:
            item = [str(c) for c in row]
            while len(item) < self.cols:
                item.append('')
            model.append(item)
    
    def on_button_press_event(self, button, cb):
        cb.popup()
        
    def _get_combobox(self):
        cb = gtk.combo_box_new_text()
        for str in ['ignore','date', 'description', 'amount',  'category']:
            cb.append_text(str)
        cb.set_active(0)
        cb.show()
        return cb
