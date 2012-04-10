#!/usr/bin/env python

from gi.repository import Gtk
from avernus.gui.gui_utils import Tree, get_name_string
from avernus.controller import controller, portfolio_controller
from avernus.gui import gui_utils, page
from avernus.gui.portfolio import dialogs


class DividendsTab(Gtk.VBox, page.Page):

    def __init__(self, portfolio):
        Gtk.VBox.__init__(self)
        self.portfolio = portfolio
        self._init_widgets()
        self.show_all()

    def _init_widgets(self):
        actiongroup = Gtk.ActionGroup('dividend_tab')
        self.tree = DividendsTree(self.portfolio, actiongroup)

        actiongroup.add_actions([
                ('add', Gtk.STOCK_ADD, 'add', None, _('Add new dividend'), self.on_add),
                ('remove', Gtk.STOCK_DELETE, 'remove', None, _('Delete selected dividend'), self.tree.on_remove),
                ('edit', Gtk.STOCK_EDIT, 'remove', None, _('Edit selected dividend'), self.tree.on_edit),
                 ])
        actiongroup.get_action('remove').set_sensitive(False)
        actiongroup.get_action('edit').set_sensitive(False)
        #self.set_property('hscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        #self.set_property('vscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        tb = Gtk.Toolbar()
        for action in actiongroup.list_actions():
            button = action.create_tool_item()
            tb.insert(button, -1)

        sw = Gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        sw.set_property('vscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        sw.add(self.tree)
        self.pack_start(tb, False, False, 0)
        self.pack_start(sw, True, True, 0)

    def on_add(self, widget=None, data=None):
        dialogs.DividendDialog(self.portfolio, tree=self.tree, parent=self.get_toplevel())
        self.update_page()

    def show(self):
        self.tree.load_dividends()
        self.update_page()

    def get_info(self):
        return [('# dividends', portfolio_controller.get_dividends_count(self.portfolio)),
                ('Sum', gui_utils.get_currency_format_from_float(portfolio_controller.get_dividends_sum(self.portfolio))),
                ('Last dividend', gui_utils.get_date_string(portfolio_controller.get_date_of_last_dividend(self.portfolio)))]


class DividendsTree(Tree):

    POSITION = 1
    DATE = 2
    AMOUNT = 3
    TA_COSTS = 4
    TOTAL = 5

    def __init__(self, portfolio, actiongroup):
        self.portfolio = portfolio
        self.actiongroup = actiongroup
        self.selected_item = None
        Tree.__init__(self)
        self._init_widgets()
        self.load_dividends()
        self.connect('cursor_changed', self.on_cursor_changed)

    def _init_widgets(self):
        self.set_model(Gtk.TreeStore(object, str, object, float, float, float))
        self.create_column(_('Position'), self.POSITION)
        self.create_column(_('Date'), self.DATE, func=gui_utils.date_to_string)
        self.create_column(_('Amount'), self.AMOUNT, func=gui_utils.currency_format)
        self.create_column(_('Transaction costs'), self.TA_COSTS, func=gui_utils.currency_format)
        self.create_column(_('Total'), self.TOTAL, func=gui_utils.currency_format)
        self.get_model().set_sort_func(self.DATE, gui_utils.sort_by_time, self.DATE)

    def on_cursor_changed(self, widget):
        obj, iterator = self.get_selected_item()
        if obj.__class__.__name__ == "Dividend":
            self.actiongroup.get_action('remove').set_sensitive(True)
            self.actiongroup.get_action('edit').set_sensitive(True)
            return
        self.actiongroup.get_action('remove').set_sensitive(False)
        self.actiongroup.get_action('edit').set_sensitive(False)

    def load_dividends(self):
        self.clear()
        for pos in self.portfolio:
            for div in pos.dividends:
                self.insert_dividend(div)

    def insert_dividend(self, div):
        model = self.get_model()
        parent_row = self.find_item(div.position)
        if parent_row is None:
            parent = model.append(None, [div.position,
                            get_name_string(div.position.stock),
                            None,
                            div.price,
                            div.costs,
                            div.total])
        else:
            parent_row[self.AMOUNT] += div.price
            parent_row[self.TA_COSTS] += div.costs
            parent_row[self.TOTAL] += div.total
            parent = parent_row.iter
        model.append(parent,
                [div,
                get_name_string(div.position.stock),
                div.date,
                div.price,
                div.costs,
                div.total])

    def on_edit(self, widget, data=None):
        obj, iterator = self.get_selected_item()
        if obj:
            dialogs.DividendDialog(self.portfolio, tree=self, dividend=obj, parent=self.get_toplevel())

    def on_remove(self, widget=None, data=None):
        obj, iterator = self.get_selected_item()
        if obj is None:
            return
        dlg = Gtk.MessageDialog(None,
             Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.QUESTION,
             Gtk.ButtonsType.OK_CANCEL,
             _("Permanently delete dividend?"))
        response = dlg.run()
        dlg.destroy()
        if response == Gtk.ResponseType.OK:
            obj.delete()
            self.get_model().remove(iterator)
            self.actiongroup.get_action('remove').set_sensitive(False)
