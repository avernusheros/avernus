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

    def __init__(self):
        gtk.Dialog.__init__(self, "Preferences", None,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT),
                            )
        self.set_default_size(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)
        logger.debug("PrefDialog started")
        vbox = self.get_content_area()
        notebook = gtk.Notebook()
        vbox.pack_start(notebook)
        notebook.append_page(DimensionList(), gtk.Label('Dimensions'))
        notebook.append_page(AccountPreferences(), gtk.Label('Account'))

        self.show_all()
        self.run()
        self.destroy()
        logger.debug("PrefDialog destroyed")


class AccountPreferences(gtk.VBox):

    def __init__(self):
        gtk.VBox.__init__(self)
        self.configParser = avernusConfig()

        section = self._add_section('Charts')
        self._add_option(section, _('Include child categories'), 'categoryChildren')

        section = self._add_section('Category Assignments')
        self._add_option(section, _('Include already categorized transactions'), 'assignments categorized transactions')

    def _add_option(self, allignment, name, option):
        button = gtk.CheckButton(label = name)
        allignment.add(button)
        button.connect('toggled', self.on_toggled, option)
        pre = self.configParser.get_option(option, 'Account')
        pre = pre == "True"
        button.set_active(pre)

    def _add_section(self, name):
        frame = gtk.Frame()
        frame.set_shadow_type(gtk.SHADOW_NONE)
        label = gtk.Label()
        label.set_markup('<b>'+name+'</b>')
        frame.set_label_widget(label)
        self.pack_start(frame, expand=False, fill=False, padding=10)
        alignment = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=1.0, yscale=1.0)
        alignment.set_property("left-padding", 12)
        frame.add(alignment)
        return alignment

    def on_toggled(self, button, option):
        self.configParser.set_option(option, button.get_active(), 'Account')


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
