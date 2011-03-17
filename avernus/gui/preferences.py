# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
from avernus.config import avernusConfig
from avernus.gui import gui_utils
from avernus.controller import controller
import gtk
import logging
import sys
logger = logging.getLogger(__name__)


class PrefDialog(gtk.Dialog):

    DEFAULT_WIDTH = 200
    DEFAULT_HEIGHT = 300

    def __init__(self, pengine):
        gtk.Dialog.__init__(self, "Preferences", None,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT),
                            )
        self.set_default_size(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)
        logger.debug("PrefDialog started")
        vbox = self.get_content_area()
        notebook = gtk.Notebook()
        vbox.pack_start(notebook)
        notebook.append_page(PluginManager(pengine), gtk.Label('Plugins'))
        notebook.append_page(DimensionList(), gtk.Label('Dimensions'))
        notebook.append_page(AccountPreferences(), gtk.Label('Account'))
        self.show_all()
        self.run()
        self.destroy()
        logger.debug("PrefDialog destroyed")
        
class AccountPreferences(gtk.VBox):
    
    def __init__(self):
        gtk.VBox.__init__(self)
        self.categoryChildrenButton = gtk.CheckButton(label=_('Include Child Categories'))
        self.pack_start(self.categoryChildrenButton, expand=False, fill=False)
        self.categoryChildrenButton.connect('toggled', self.onCategoryChildrenToggled)
        self.configParser = avernusConfig()
        pre = self.configParser.get_option('categoryChildren', 'Account')
        pre = pre == "True"
        self.categoryChildrenButton.set_active(pre)
        
    def onCategoryChildrenToggled(self, button):
        self.configParser.set_option('categoryChildren', self.categoryChildrenButton.get_active(), 
                                     'Account')
        
        


class DimensionList(gtk.VBox):

    OBJECT = 0
    NAME = 1

    def __init__(self):
        gtk.VBox.__init__(self)
        self.tree = gui_utils.Tree()
        self.tree.set_headers_visible(False)
        self.model = gtk.TreeStore(object, str)
        self.tree.set_model(self.model)
        col, cell = self.tree.create_column('Dimensions', self.NAME)
        cell.set_property('editable', True)
        cell.connect('edited', self.on_cell_edited)
        sw = gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        self.pack_start(sw, expand=True, fill=True)
        sw.add(self.tree)
        for dim in controller.getAllDimension():
            iterator = self.model.append(None, [dim, dim.name])
            for val in controller.getAllDimensionValueForDimension(dim):
                self.model.append(iterator, [val, val.name])
        actiongroup = gtk.ActionGroup('dimensions')
        actiongroup.add_actions([
                ('add',     gtk.STOCK_ADD,    'new dimension',      None, _('Add new dimension'), self.on_add),
                ('rename',  gtk.STOCK_EDIT,   'rename dimension',   None, _('Rename selected dimension'), self.on_edit),
                ('remove',  gtk.STOCK_DELETE, 'remove dimension',   None, _('Remove selected dimension'), self.on_remove)
                     ])
        toolbar = gtk.Toolbar()
        self.conditioned = ['rename', 'edit']

        for action in actiongroup.list_actions():
            button = action.create_tool_item()
            toolbar.insert(button, -1)
        self.pack_start(toolbar, expand=False, fill=True)

    def on_add(self, widget):
        dimension = controller.newDimension('new dimension')
        iterator = self.model.append(None, [dimension, dimension.name])
        #self.expand_row( model.get_path(parent_iter), True)
        self.tree.set_cursor(self.model.get_path(iterator), focus_column = self.tree.get_column(0), start_editing=True)

    def on_edit(self, widget):
        selection = self.tree.get_selection()
        model, selection_iter = selection.get_selected()
        if selection_iter:
            self.tree.set_cursor(model.get_path(selection_iter), focus_column = self.tree.get_column(0), start_editing=True)

    def on_remove(self, widget):
        selection = self.tree.get_selection()
        model, selection_iter = selection.get_selected()
        if selection_iter:
            model[selection_iter][self.OBJECT].delete()
            self.model.remove(selection_iter)

    def on_cell_edited(self, cellrenderertext, path, new_text):
        self.model[path][self.OBJECT].name = self.model[path][self.NAME] = new_text


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
        self.pack_start(self.tree, expand = True)
        self._insert_plugins()

        buttonbox = gtk.HButtonBox()
        buttonbox.set_layout(gtk.BUTTONBOX_END)
        self.pack_start(buttonbox, expand = False)
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
        #d.set_logo_icon_name('avernus')
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
