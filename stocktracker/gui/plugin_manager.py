# -*- coding: utf-8 -*-

import sys
import gtk
from stocktracker.gui import gui_utils

class PluginManager(gtk.Dialog):
    
    def __init__(self, main_window, pengine, plugin_apis=None):
        gtk.Dialog.__init__(self, _("Plugin Manager"), None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        
        self.pengine = pengine
        self.plugins = pengine.plugins
        self.main_window = main_window
        self.plugin_apis = plugin_apis
        
        vbox = self.get_content_area()
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        
        self.tree = gui_utils.Tree()
        self.tree.set_model(gtk.TreeStore(object, bool, str,str))
        
        column = gtk.TreeViewColumn()
        column.set_resizable(False)
        self.tree.append_column(column)
        cell = gtk.CellRendererToggle()
        column.pack_start(cell, expand = False)
        column.add_attribute(cell, "active", 1)
        cell.connect("toggled", self.on_toggled)
        
        self.tree.create_column('Name', 2)
        self.tree.create_column('Version', 3)
        self.tree.set_headers_visible(False)
        self.tree.connect('cursor-changed', self.on_cursor_changed)
        hbox.pack_start(self.tree)
        self._insert_plugins()
        
        self.info_label = gtk.Label()
        hbox.pack_start(self.info_label)
        
        path = 0
        self.tree.set_cursor(path)
        self.on_selection(self.tree.get_model()[path][0])
        
        self.show_all()
        self.run()
        self.destroy()
        
    def _insert_plugins(self):
        self.tree.clear()
        m = self.tree.get_model()
        for name, plugin in self.plugins.items():
            m.append(None, [plugin, plugin.enabled, plugin.name, plugin.version])

    def on_toggled(self, cell, path):
        row = self.tree.get_model()[path]
        plugin = row[0]
        row[1] = not row[1]
        if row[1]:
            plugin.enabled = True
            self.pengine.activate_plugins([plugin], self.main_window.api)
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
    
    def on_selection(self, obj):
        text = '<span size="x-large">' +obj.name+'</span>'+\
                '<b>\n\nDescription\n</b>'+obj.description+\
                '<b>\n\nAuthor(s)\n</b>'+obj.authors+\
                '<b>\n\nVersion\n</b>'+obj.version
        self.info_label.set_markup(text)
