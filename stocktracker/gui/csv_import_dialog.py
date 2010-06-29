#!/usr/bin/env python

import gtk
from stocktracker.gui.gui_utils import Tree
from stocktracker import csvimporter


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
        
        table.attach(gtk.Label('Lines to skip'),0,1,1,2, xoptions=0, yoptions=0)
        self.lines_to_skip = gtk.SpinButton(gtk.Adjustment(lower=0, upper=100,step_incr=1, value = 1), digits=0)
        self.lines_to_skip.connect("value-changed", self._on_refresh)
        table.attach(self.lines_to_skip, 1,2,1,2)
        
        table.attach(gtk.HSeparator(), 0,3,2,3)
        frame = gtk.Frame('Preview')
        sw = gtk.ScrolledWindow()
        frame.add(sw)
        self.tree = PreviewTree()
        sw.add(self.tree)
        table.attach(frame, 0,3,4,5)
        self.show_all()

    def process_result(self, widget=None, response = gtk.RESPONSE_ACCEPT):
        if response == gtk.RESPONSE_ACCEPT:
            print "do import"
        self.destroy()  

    def _on_refresh(self, *args):
        self.profile['linesToSkip'] = int(self.lines_to_skip.get_value())
        transactions = self.importer.getRowsFromCSV(self.file, self.profile)
        self.tree.reload(transactions)

    def _on_file_set(self, button):
        self.file = button.get_filename()
        self._on_refresh()
        

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
            column.set_widget(self._get_combobox())
            self.append_column(column)
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
        
    def _get_combobox(self):
        cb = gtk.combo_box_new_text()
        for str in ['date', 'description', 'amount', 'ignore', 'category']:
            cb.append_text(str)
            cb.show()
        return cb
