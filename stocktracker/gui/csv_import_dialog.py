#!/usr/bin/env python

import gtk
from stocktracker.gui.gui_utils import Tree
from stocktracker import csvimporter

PROFILE =  {
            'linesToSkip':13, 
            'encoding':'iso-8859-15',
            'delimiter':';',
            'amountColumn':8,
            'decimalSeparator':',',
            'descriptionColumn':6,
            'dateColumn':1,
            'dateFormat':'%d.%m.%Y',
            'saldoIndicator':9,
            'negativeSaldo':'S',
            'receiver':3,
            'sender':2,
            }

class CSVImportDialog(gtk.Dialog):
    
    def __init__(self, *args):
        gtk.Dialog.__init__(self, _("Import CSV"), None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        
        self._init_widgets()
        self.importer = csvimporter.CsvImporter()
        
        response = self.run()  
        self.process_result(response = response)

    def _init_widgets(self):
        vbox = self.get_content_area()
        table = gtk.Table()
        vbox.pack_start(table)
        
        table.attach(gtk.Label('File to import'),0,1,0,1)
        fcbutton = gtk.FileChooserButton('File to import')
        self.file = None
        fcbutton.connect('file-set', self._on_file_set)
        table.attach(fcbutton, 1,2,0,1)
        
        table.attach(gtk.HSeparator(), 0,2,1,2)
        button = gtk.Button(stock='refresh')
        button.connect('clicked', self._on_refresh)
        table.attach(button, 0,1,2,3)
        self.sw = gtk.ScrolledWindow()
        table.attach(self.sw, 0,2,3,4)
        self.show_all()

    def process_result(self, widget=None, response = gtk.RESPONSE_ACCEPT):
        if response == gtk.RESPONSE_ACCEPT:
            print "do import"
        self.destroy()  

    def _on_refresh(self, *args):
        transactions = self.importer.getTransactionsFromFile(self.file, PROFILE)
        print transactions
        self.sw.add(PreviewTree(transactions))

    def _on_file_set(self, button):
        self.file = button.get_filename()
        

class PreviewTree(Tree):
    
    def __init__(self, transactions):
        Tree.__init__(self)
        cols = len(max(transactions, key=len))
        
        temp = [str]*cols
        model = gtk.ListStore(*temp)
        self.set_model(model)
        
        for i in range(cols):
            column = gtk.TreeViewColumn()
            column.set_widget(self._get_combobox())
            self.append_column(column)
            cell = gtk.CellRendererText()
            column.pack_start(cell, expand = True)
            column.add_attribute(cell, "text", i)
            
        for t in transactions:
            item = [str(c) for c in t]
            while len(item) < cols:
                item.append('')
            model.append(item)
        
        self.show_all()

    def _get_combobox(self):
        cb = gtk.combo_box_new_text()
        for str in ['date', 'description', 'amount', 'ignore', 'category']:
            cb.append_text(str)
            cb.show()
        return cb

