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
        
        self.tree = gui_utils.Tree()
        self.tree.set_model(gtk.TreeStore(object, bool, str, bool))
        self.tree.set_rules_hint(True)
        
        cell = gtk.CellRendererToggle()
        cell.connect("toggled", self.on_toggled)
        column = gtk.TreeViewColumn(None,cell, activatable=3) 
        column.add_attribute(cell, "active", 1)
        self.tree.append_column(column)
        
        col, cell = self.tree.create_column('Name', 2)
        col.set_cell_data_func(cell, self._plugin_markup)
        self.tree.set_headers_visible(False)
        self.tree.connect('cursor-changed', self.on_cursor_changed)
        vbox.pack_start(self.tree, expand = False)
        self._insert_plugins()
        
        buttonbox = gtk.HButtonBox()
        buttonbox.set_layout(gtk.BUTTONBOX_END)
        vbox.pack_start(buttonbox) 
        button = gtk.Button('About')
        button.connect('clicked', self.on_about_clicked)
        buttonbox.add(button)
        self.pref_button = gtk.Button('Preferences')
        self.pref_button.connect('clicked', self.on_prefs_clicked)
        buttonbox.add(self.pref_button)

        path = 0
        self.tree.set_cursor(path)
        self.selected_obj = self.tree.get_model()[path][0]
        self.on_selection(self.selected_obj)        

        self.show_all()
        self.run()
        self.destroy()
    
    def _plugin_markup(self, column, cell, store, iter):
        cell.set_property('sensitive', store.get_value(iter,3))        
        
    def _insert_plugins(self):
        self.tree.clear()
        m = self.tree.get_model()
        for name, plugin in self.plugins.items():
            text = '<b>'+plugin.name+'</b>\n'+plugin.description
            if plugin.error:
                text+='\nMissing dependencies: ' +\
                "<small><b>%s</b></small>" % ', '.join(plugin.missing_modules)
            iter = m.append(None, [plugin, plugin.enabled, text, not plugin.error])   
    
    def on_prefs_clicked(self, *args, **kwargs):
        self.selected_obj.instance.configure()            
    
    def on_about_clicked(self, *args, **kwargs):
        pl = self.selected_obj
        d = gtk.AboutDialog()
        d.set_name(pl.name)
        d.set_version(pl.version)
        #d.set_copyright()
        description = pl.description
        if pl.error:
            description += '\n\nMissing dependencies: '+', '.join(pl.missing_modules)
        d.set_comments(description)
        #d.set_license()
        d.set_authors(pl.authors)
        #d.set_website(pl.url)
        #d.set_logo_icon_name('stocktracker')        
        d.run()
        d.hide()

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
            self.selected_obj = treestore.get_value(selection_iter, 0)
            self.on_selection(self.selected_obj)
            
    def on_selection(self, plugin):
        self.pref_button.set_sensitive(plugin.configurable)        
