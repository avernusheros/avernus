# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
from avernus.config import avernusConfig
from avernus.gui import gui_utils
from avernus.controller import dimensions_controller
from avernus.controller import object_controller
from gi.repository import Gtk
import logging
logger = logging.getLogger(__name__)


class PrefDialog(Gtk.Dialog):

    DEFAULT_WIDTH = 400
    DEFAULT_HEIGHT = 500

    def __init__(self, parent=None):
        Gtk.Dialog.__init__(self, _("Preferences"), parent,
                            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                            (Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT),
                            )
        self.set_default_size(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)
        vbox = self.get_content_area()
        notebook = Gtk.Notebook()
        vbox.pack_start(notebook, True, True, 0)
        notebook.append_page(AccountPreferences(), Gtk.Label(label=_('Account')))
        notebook.append_page(PortfolioPreferences(), Gtk.Label(label=_('Portfolio')))
        notebook.append_page(ChartPreferences(), Gtk.Label(label=_('Chart')))
        notebook.append_page(DimensionList(), Gtk.Label(label=_('Dimensions')))

        self.show_all()
        self.run()
        self.destroy()


class PreferencesVBox(Gtk.VBox):

    def _add_section(self, name):
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.NONE)
        label = Gtk.Label()
        label.set_markup('<b>' + name + '</b>')
        frame.set_label_widget(label)
        vbox = Gtk.VBox()
        frame.add(vbox)
        self.pack_start(frame, False, False, 10)
        return vbox

    def _get_alignment(self):
        alignment = Gtk.Alignment.new(0.5, 0.5, 1.0, 1.0)
        alignment.set_property("left-padding", 12)
        return alignment

    def _add_option(self, vbox, name, option):
        alignment = self._get_alignment()
        vbox.add(alignment)
        button = Gtk.CheckButton(label=name)
        alignment.add(button)
        button.connect('toggled', self.on_toggled, option)
        pre = self.configParser.get_option(option, self.parser_section)
        pre = pre == "True"
        button.set_active(pre)

    def on_toggled(self, button, option):
        self.configParser.set_option(option, button.get_active(), self.parser_section)


class ChartPreferences(PreferencesVBox):

    parser_section = "Chart"

    def __init__(self):
        Gtk.VBox.__init__(self)
        self.configParser = avernusConfig()

        section = self._add_section(_('Axis'))
        self._add_option(section, _('Normalize Y Axis'), 'normalize_y_axis')


class PortfolioPreferences(PreferencesVBox):

    parser_section = "Portfolio"

    def __init__(self):
        Gtk.VBox.__init__(self)
        self.configParser = avernusConfig()

        section = self._add_section(_('Appearance'))
        self._add_option(section, _('Save vertical space'), 'smallPosition')


class AccountPreferences(PreferencesVBox):

    parser_section = "Account"

    def __init__(self):
        Gtk.VBox.__init__(self)
        self.configParser = avernusConfig()

        #FIXME tooltip
        section = self._add_section(_('Charts'))
        self._add_option(section, _('Include child categories'), 'categoryChildren')

        #FIXME tooltip
        section = self._add_section(_('Category Assignments'))
        self._add_option(section, _('Include already categorized transactions'), 'assignments categorized transactions')


class DimensionList(Gtk.VBox):

    OBJECT = 0
    NAME = 1

    def __init__(self):
        Gtk.VBox.__init__(self)
        text = _("Dimensions are used to categorize your assets. You can define dimensions and categories for those dimensions.")

        label = Gtk.Label(label=text)
        label.set_line_wrap(True)
        self.pack_start(label, False, False, 0)

        self.tree = gui_utils.Tree()
        self.tree.set_headers_visible(True)
        self.model = Gtk.TreeStore(object, str)
        self.tree.set_model(self.model)
        col, cell = self.tree.create_column(_('Dimensions'), self.NAME)
        cell.set_property('editable', True)
        cell.connect('edited', self.on_cell_edited)
        sw = Gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        sw.set_property('vscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        self.pack_start(sw, True, True, 0)
        sw.add(self.tree)
        for dim in sorted(dimensions_controller.get_all_dimensions()):
            iterator = self.model.append(None, [dim, dim.name])
            for val in sorted(dim.values):
                self.model.append(iterator, [val, val.name])

        actiongroup = Gtk.ActionGroup('dimensions')
        actiongroup.add_actions([
                ('add', Gtk.STOCK_ADD, 'new dimension', None, _('Add new dimension'), self.on_add),
                ('rename', Gtk.STOCK_EDIT, 'rename dimension', None, _('Rename selected dimension'), self.on_edit),
                ('remove', Gtk.STOCK_DELETE, 'remove dimension', None, _('Remove selected dimension'), self.on_remove)
                     ])
        toolbar = Gtk.Toolbar()
        toolbar.get_style_context().add_class("inline-toolbar")
        self.conditioned = ['rename', 'edit']

        for action in actiongroup.list_actions():
            button = action.create_tool_item()
            toolbar.insert(button, -1)
        self.pack_start(toolbar, False, True, 0)

    def on_add(self, widget, user_data=None):
        dimension = dimensions_controller.new_dimension(_('new dimension'))
        iterator = self.model.append(None, [dimension, dimension.name])
        #self.expand_row( model.get_path(parent_iter), True)
        self.tree.set_cursor(self.model.get_path(iterator), self.tree.get_column(0), True)

    def on_edit(self, widget, user_data=None):
        selection = self.tree.get_selection()
        model, selection_iter = selection.get_selected()
        if selection_iter:
            self.tree.set_cursor(model.get_path(selection_iter), self.tree.get_column(0), True)

    def on_remove(self, widget, user_data=None):
        selection = self.tree.get_selection()
        model, selection_iter = selection.get_selected()
        if selection_iter:
            object_controller.delete_object(model[selection_iter][self.OBJECT])
            self.model.remove(selection_iter)

    def on_cell_edited(self, cellrenderertext, path, new_text):
        self.model[path][self.OBJECT].name = self.model[path][self.NAME] = new_text
