# -*- coding: utf-8 -*-
import sys
import gtk
from stocktracker.gui import gui_utils
from stocktracker import logger

           
class PrefDialog(gtk.Dialog):
    
    def __init__(self, pengine, dsm):
        gtk.Dialog.__init__(self, "Preferences", None,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT),
                            )
        logger.logger.debug("PrefDialog started")
        vbox = self.get_content_area()
        notebook = gtk.Notebook()
        vbox.pack_start(notebook)
        notebook.append_page(PluginManager(pengine), gtk.Label('Plugins'))
        dsp = DataSourcePriorities(dsm)
        notebook.append_page(dsp, gtk.Label('Sources'))
        self.show_all()
        self.run()
        dsp.on_close()  
        self.destroy()
        logger.logger.debug("PrefDialog destroyed")

      
class DataSourcePriorities(gtk.VBox):
    
    def __init__(self, dsm):
        gtk.VBox.__init__(self)
        self.dsm = dsm
        label = gtk.Label('Define priorities by reordering the sources')
        self.pack_start(label)
        
        self.tree = gui_utils.Tree()
        self.model = gtk.ListStore(str, str, str, str)
        self.tree.set_model(self.model)
        col, cell = self.tree.create_column('Source', 0)
        col.set_reorderable(False)
        self.tree.create_icon_column('Search', 1)
        self.tree.create_icon_column('Update', 2)
        self.tree.create_icon_column('Historical data', 3)
        self.tree.set_reorderable(True)
        self.pack_start(self.tree)
        self.connect('expose-event', self.show)
    
    def _get_icon_name(self, ):
        if store.get_value(iter, user_data):
            return 'gtk-apply'
        return 'gtk-cancel'
    
    def show(self, *args):
        icons = {True:'gtk-apply', False:'gtk-cancel'}
        self.tree.clear()
        for name in self.dsm.queue:
            self.model.append([name, icons[getattr(self.dsm.sources[name], 'search', None) is not None]\
                              , icons[getattr(self.dsm.sources[name], 'update_stocks', None) is not None]\
                              , icons[getattr(self.dsm.sources[name], 'update_historical_prices', None) is not None]])

    def on_close(self):
        model = self.tree.get_model()
        self.dsm.queue = [item[0] for item in model]


class PluginManager(gtk.VBox):
    
    def __init__(self, pengine):
        gtk.VBox.__init__(self)
        
        self.pengine = pengine
        self.plugins = pengine.plugins
        
        self.tree = gui_utils.Tree()
        self.tree.set_model(gtk.ListStore(object, bool, str, str, bool))
        self.tree.set_rules_hint(True)
        
        cell = gtk.CellRendererToggle()
        cell.connect("toggled", self.on_toggled)
        column = gtk.TreeViewColumn(None,cell, activatable=4) 
        column.add_attribute(cell, "active", 1)
        self.tree.append_column(column)
        
        self.tree.create_icon_text_column('', 2,3, self._plugin_markup, self._plugin_markup)
        
        self.tree.set_headers_visible(False)
        self.tree.connect('cursor-changed', self.on_cursor_changed)
        self.pack_start(self.tree, expand = False)
        self._insert_plugins()
        
        buttonbox = gtk.HButtonBox()
        buttonbox.set_layout(gtk.BUTTONBOX_END)
        self.pack_start(buttonbox) 
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

    def _plugin_markup(self, column, cell, store, iter, user_data):
        cell.set_property('sensitive', store.get_value(iter,4))        
        
    def _insert_plugins(self):
        self.tree.clear()
        m = self.tree.get_model()
        for name, plugin in self.plugins.items():
            text = '<b>'+plugin.name+'</b>\n'+plugin.description
            if plugin.error:
                text+='\nMissing dependencies: ' +\
                "<small><b>%s</b></small>" % ', '.join(plugin.missing_modules)
            iter = m.append([plugin, plugin.enabled, plugin.icon, text, not plugin.error])   
    
    def on_prefs_clicked(self, *args, **kwargs):
        self.selected_obj.instance.configure()            
    
    def on_about_clicked(self, *args, **kwargs):
        pl = self.selected_obj
        d = gtk.AboutDialog()
        d.set_name(pl.name)
        d.set_version(pl.version)
        #d.set_copyright()
        d.set_logo_icon_name(pl.icon)
        description = pl.description
        if pl.error:
            description += '\n\nMissing dependencies: '+', '.join(pl.missing_modules)
        d.set_comments(description)
        #d.set_license()
        d.set_authors([pl.authors])
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
