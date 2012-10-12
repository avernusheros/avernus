from avernus.controller import categorization_controller
from avernus.gui import gui_utils
from avernus.objects import account
from gi.repository import Gtk, Pango


class CategorizationRulesDialog(Gtk.Dialog):

    def __init__(self, parent=None):
        Gtk.Dialog.__init__(self, _("Categorization rules"), parent
                            , Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                     (Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        self.set_size_request(800, 600)
        self._init_widgets()
        self.show_all()
        self.run()
        self.destroy()

    def _init_widgets(self):
        vpaned = Gtk.VPaned()
        self.get_content_area().pack_start(vpaned, True, True, 0)
        vbox = Gtk.VBox()

        sw = Gtk.ScrolledWindow()
        sw.set_size_request(800, 300)
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.rules_tree = RulesTree()
        sw.add(self.rules_tree)
        vbox.pack_start(sw, True, True, 0)

        actiongroup = Gtk.ActionGroup('categorization rules')
        actiongroup.add_actions([
                ('add', Gtk.STOCK_ADD, 'new categorization rule', None, _('Add new categorization rule'), self.rules_tree.on_add),
                ('remove', Gtk.STOCK_DELETE, 'remove categorization rule', None, _('Remove selected categorization rule'), self.rules_tree.on_remove),
                ('refresh', Gtk.STOCK_REFRESH, 'reload preview tree', None, _('Reload preview tree'), self.refresh_preview),
                ('reset', Gtk.STOCK_CLEAR, 'reset preview tree', None, _('Reset the preview tree'), self.reset_preview),
                     ])
        toolbar = Gtk.Toolbar()
        toolbar.insert(actiongroup.get_action('add').create_tool_item(), -1)
        toolbar.insert(actiongroup.get_action('remove').create_tool_item(), -1)
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        toolbar.insert(actiongroup.get_action('refresh').create_tool_item(), -1)
        toolbar.insert(actiongroup.get_action('reset').create_tool_item(), -1)
        vbox.pack_start(toolbar, False, True, 0)

        vpaned.add1(vbox)

        frame = Gtk.Frame()
        frame.set_label(_('Preview'))
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.preview_tree = PreviewTree()
        frame.add(sw)
        sw.add(self.preview_tree)
        vpaned.add2(frame)

    def refresh_preview(self, widget):
        # get the active rule and refresh the preview tree with it
        active_rule = self.rules_tree.get_active_rule()
        if active_rule:
            self.preview_tree.on_refresh(active_rule)

    def reset_preview(self, widget):
        self.preview_tree.reset()


class PreviewTree(gui_utils.Tree):
    OBJECT = 0
    DESCRIPTION = 1
    AMOUNT = 2
    CATEGORY = 3
    DATE = 4
    ACCOUNT = 5

    def __init__(self):
        gui_utils.Tree.__init__(self)
        self.set_size_request(800, 300)
        self.model = Gtk.ListStore(object, str, float, str, object, str)
        self.modelfilter = self.model.filter_new(None)
        sorter = Gtk.TreeModelSort(model=self.modelfilter)
        self.set_model(sorter)
        self.modelfilter.set_visible_func(self.visible_cb, None)
        self.create_column(_('Date'), self.DATE, func=gui_utils.date_to_string, expand=False)
        sorter.set_sort_func(self.DATE, gui_utils.sort_by_time, self.DATE)
        col, cell = self.create_column(_('Description'), self.DESCRIPTION, func=gui_utils.transaction_desc_markup)
        cell.props.wrap_mode = Pango.WrapMode.WORD
        cell.props.wrap_width = 300
        self.create_column(_('Amount'), self.AMOUNT, func=gui_utils.currency_format, expand=False)
        self.create_column(_('Category'), self.CATEGORY, expand=False)
        self.create_column(_('Account'), self.ACCOUNT, expand=False)
        self.set_rules_hint(True)

        self.active_rule = None
        self.load_all()

    def visible_cb(self, model, iterator, user_data):
        transaction = model[iterator][self.OBJECT]
        if transaction and transaction.transfer:
            return False
        if self.active_rule:
            return categorization_controller.match_transaction(self.active_rule, transaction)
        return True

    def load_all(self):
        for trans in account.get_all_transactions():
            if trans.category:
                cat = trans.category.name
            else:
                cat = ''
            self.model.append([trans, trans.description, trans.amount, cat, trans.date, trans.account.name])

    def on_refresh(self, assigner):
        self.active_rule = assigner
        self.modelfilter.refilter()

    def reset(self):
        self.active_rule = None
        self.modelfilter.refilter()


class RulesTree(gui_utils.Tree):
    OBJECT = 0
    ACTIVE = 1
    PRIORITY = 2
    RULE_STR = 3
    CATEGORY = 4
    CATEGORY_STR = 5

    def __init__(self):
        gui_utils.Tree.__init__(self)
        self.set_size_request(800, 300)
        self.model = Gtk.ListStore(object, bool, int, str, object, str)
        self.set_model(self.model)

        column, cell = self.create_check_column(_('Active'), self.ACTIVE)
        cell.connect("toggled", self.on_toggled)

        cell = Gtk.CellRendererSpin()
        adjustment = Gtk.Adjustment(1, 1, 100, 1, 10, 0)
        cell.set_property("editable", True)
        cell.set_property("adjustment", adjustment)
        cell.connect("edited", self.on_spin_edited)
        column = Gtk.TreeViewColumn(_('Priority'), cell, text=self.PRIORITY)
        self.append_column(column)

        col, cell = self.create_column(_('Rule'), self.RULE_STR, expand=True)
        cell.set_property('editable', True)
        cell.connect('edited', self.on_cell_edited)

        cell = Gtk.CellRendererCombo()
        cell.connect('changed', self.on_category_changed)
        self.cb_model = Gtk.ListStore(object, str)
        self.categories = account.get_all_categories()
        for category in self.categories:
            self.cb_model.append([category, category.name])
        cell.set_property('model', self.cb_model)
        cell.set_property('text-column', 1)
        cell.set_property('editable', True)
        column = Gtk.TreeViewColumn(_('Category'), cell, text=self.CATEGORY_STR)
        self.append_column(column)

        self.load_rules()

    def get_active_rule(self):
        item, iterator = self.get_selected_item()
        return item

    def load_rules(self):
        for rule in categorization_controller.get_all_rules():
            self.insert_rule(rule)

    def on_category_changed(self, cellrenderertext, path, new_iter):
        category = self.cb_model[new_iter][0]
        self.model[path][self.CATEGORY_STR] = category.name
        self.model[path][self.OBJECT].category = category

    def on_spin_edited(self, cell, path, new_text):
        try:
            new_val = int(new_text)
        except:
            #no integer value
            return
        self.model[path][self.PRIORITY] = self.model[path][self.OBJECT].priority = new_val

    def on_cell_edited(self, cellrenderertext, path, new_text):
        self.model[path][self.RULE_STR] = self.model[path][self.OBJECT].rule = unicode(new_text)

    def on_toggled(self, cellrenderertoggle, path):
        active = not self.model[path][self.ACTIVE]
        self.model[path][self.ACTIVE] = active
        self.model[path][self.OBJECT].active = active

    def on_add(self, widget, user_data=None):
        rule = categorization_controller.create("new categorization rule - click to edit", self.categories[0], False)
        iterator = self.insert_rule(rule)
        self.scroll_to_cell(self.model.get_path(iterator))

    def on_remove(self, widget, user_data=None):
        item, iterator = self.get_selected_item()
        if item is not None:
            item.delete()
            self.model.remove(iterator)

    def insert_rule(self, rule):
        return self.model.append([rule, rule.active, rule.priority, rule.rule, rule.category, rule.category.name])
