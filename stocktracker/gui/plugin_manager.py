# -*- coding: utf-8 -*-

import sys
import gtk
from stocktracker.gui import gui_utils

class PluginManager(gtk.Dialog):
    
    def __init__(self, main_window, pengine):
        gtk.Dialog.__init__(self, _("Plugin Manager"), None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        
        self.pengine = pengine
        self.plugins = pengine.plugins
        self.main_window = main_window
        
        vbox = self.get_content_area()
        hbox = gtk.HBox()
        hbox.set_resizable(False)
        vbox.pack_start(hbox)
        
        self.tree = gui_utils.Tree()
        self.tree.set_model(gtk.TreeStore(object, bool, str,str,bool))
        
        cell = gtk.CellRendererToggle()
        cell.connect("toggled", self.on_toggled)
        column = gtk.TreeViewColumn(None,cell, activatable=4) 
        column.add_attribute(cell, "active", 1)
        self.tree.append_column(column)
        
        col, cell = self.tree.create_column('Name', 2)
        col.set_cell_data_func(cell, self._plugin_markup)
        col, cell = self.tree.create_column('Version', 3)
        col.set_cell_data_func(cell, self._plugin_markup)
        self.tree.set_headers_visible(False)
        self.tree.connect('cursor-changed', self.on_cursor_changed)
        hbox.pack_start(self.tree)
        self._insert_plugins()
        
        self.info_label = gtk.Label()
        self.info_label.set_line_wrap(True)
        hbox.pack_start(self.info_label)
        
        path = 0
        self.tree.set_cursor(path)
        self.on_selection(self.tree.get_model()[path][0])
        
        self.show_all()
        self.run()
        self.destroy()
    
    def _plugin_markup(self, column, cell, store, iter):
        cell.set_property('sensitive', store.get_value(iter,4))        
        
    def _insert_plugins(self):
        self.tree.clear()
        m = self.tree.get_model()
        for name, plugin in self.plugins.items():
            iter = m.append(None, [plugin, plugin.enabled, plugin.name, plugin.version, not plugin.error])   
                
    def on_toggled(self, cell, path):
        row = self.tree.get_model()[path]
        plugin = row[0]
        if not plugin.error:
            row[1] = not row[1]
            if row[1]:
                plugin.enabled = True
                self.pengine.activate_plugins([plugin])
            else:
                plugin.enabled = False
                self.pengine.deactivate_plugins([plugin])
    
    def on_cursor_changed(self, widget):
        selection = self.tree.get_selection()
        # Get the selection iter
        treestore, selection_iter = selection.get_selected()
        if (selection_iter and treestore):
            #Something is selected so get the object
            obj = treestore.get_value(selection_iter, 0)
            self.on_selection(obj)
    
    def on_selection(self, obj):
        text = '<span size="x-large">' +obj.name+'</span>'+\
                '<b>\n\nDescription\n</b>'+obj.description+\
                '<b>\n\nAuthor(s)\n</b>'+obj.authors+\
                '<b>\n\nVersion\n</b>'+obj.version
        if obj.error:
            text+='<b>\n\nThe plugin can not be loaded.\n</b>'+\
            'Missing dependencies: '
            text+="<small><b>%s</b></small>" % ', '.join(obj.missing_modules)
        self.info_label.set_markup(text)
