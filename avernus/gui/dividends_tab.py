#!/usr/bin/env python

import gtk
from datetime import datetime
from avernus.gui.gui_utils import Tree, get_name_string
from avernus.gui.dialogs import PosSelector
from avernus.objects import controller
from avernus.gui import gui_utils, dialogs


class DividendsTab(gtk.VBox):
    def __init__(self, item):
        gtk.VBox.__init__(self)
        actiongroup = gtk.ActionGroup('dividend_tab')
        tree = DividendsTree(item, actiongroup)
        actiongroup.add_actions([
                ('add',    gtk.STOCK_ADD,     'add',    None, _('Add new dividend'),         tree.on_add),
                ('remove', gtk.STOCK_DELETE,  'remove', None, _('Delete selected dividend'), tree.on_remove),
                ('edit', gtk.STOCK_EDIT,  'remove', None, _('Edit selected dividend'), tree.on_edit),
                 ])
        actiongroup.get_action('remove').set_sensitive(False)
        actiongroup.get_action('edit').set_sensitive(False)
        #self.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        #self.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        tb = gtk.Toolbar()
        for action in actiongroup.list_actions():
            button = action.create_tool_item()
            tb.insert(button, -1)
        
        sw = gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.add(tree)
        self.pack_start(tb, expand = False, fill = False)
        self.pack_start(sw)
        self.show_all()


class DividendsTree(Tree):
    def __init__(self, portfolio, actiongroup):
        self.portfolio = portfolio
        self.actiongroup = actiongroup
        self.selected_item = None
        Tree.__init__(self)
        self._init_widgets()
        self.load_dividends()
        self.connect('cursor_changed', self.on_cursor_changed)

    def _init_widgets(self):
        self.set_model(gtk.ListStore(object, str, object, float, float, float))
        self.create_column(_('Position'), 1)
        self.create_column(_('Date'), 2, func=gui_utils.date_to_string)
        self.create_column(_('Amount'), 3, func=gui_utils.currency_format)
        self.create_column(_('Transaction costs'), 4, func=gui_utils.currency_format)
        self.create_column(_('Total'), 5, func = gui_utils.currency_format)

    def on_cursor_changed(self, widget):
        obj, iterator = self.get_selected_item()
        if isinstance(obj, controller.Dividend):
            self.actiongroup.get_action('remove').set_sensitive(True)
            self.actiongroup.get_action('edit').set_sensitive(True)
            return
        self.actiongroup.get_action('remove').set_sensitive(False)
        self.actiongroup.get_action('edit').set_sensitive(False)

    def load_dividends(self):
        for pos in self.portfolio:
            for div in pos.dividends:
                self.insert_dividend(div)

    def insert_dividend(self, div):
        self.get_model().append([
                div,
                get_name_string(div.position.stock),
                div.date,
                div.price,
                div.costs,
                div.total])

    def on_add(self, widget=None):
        dialogs.DividendDialog(self.portfolio, tree = self)
    
    def on_edit(self, widget):
        obj, iterator = self.get_selected_item()
        if obj:
            dialogs.DividendDialog(self.portfolio, tree = self, dividend=obj)

    def on_remove(self, widget=None):
        obj, iterator = self.get_selected_item()
        if obj is None:
            return
        dlg = gtk.MessageDialog(None,
             gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION,
             gtk.BUTTONS_OK_CANCEL,
             _("Permanently delete dividend?"))
        response = dlg.run()
        dlg.destroy()
        if response == gtk.RESPONSE_OK:
            obj.delete()
            self.get_model().remove(iterator)
            self.actiongroup.get_action('remove').set_sensitive(False)
