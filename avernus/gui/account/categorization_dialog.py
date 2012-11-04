from avernus.controller import categorization_controller
from avernus.gui import gui_utils
from avernus.gui import get_ui_file
from avernus.objects import account
from gi.repository import Gtk, Pango


class CategorizationRulesDialog:

    def __init__(self, parent=None):
        builder = Gtk.Builder()
        builder.add_from_file(get_ui_file("account/category_assignments_dialog.glade"))
        builder.connect_signals(self)

        # get gui objects
        sw = builder.get_object("scrolledwindow")
        dlg = builder.get_object("dialog")
        self.searchstring_entry = builder.get_object("searchstring_entry")
        self.priority_entry = builder.get_object("priority_entry")
        self.category_combobox = builder.get_object("category_combobox")

        self.active_rule = None

        # create gui elements
        self._init_tree()
        self._init_combobox()
        sw.add(self.rules_tree)

        # setup and show dialog
        dlg.set_transient_for(parent)
        dlg.add_buttons(Gtk.STOCK_CLOSE, Gtk.ResponseType.ACCEPT)
        dlg.show_all()
        dlg.run()
        dlg.destroy()

    def _init_tree(self):
        self.rules_tree = gui_utils.Tree()
        model = Gtk.ListStore(object, bool, str)
        self.rules_tree.set_model(model)

        col, cell = self.rules_tree.create_check_column(_('Active'), 1)
        cell.connect("toggled", self.on_active_toggled)
        self.rules_tree.create_column(_('Rule'), 2, expand=True)

        # load rules
        for rule in categorization_controller.get_all_rules():
            model.append([rule, rule.active, rule.rule])

        self.rules_tree.connect('cursor_changed', self.on_cursor_changed)

    def _init_combobox(self):
        def insert_recursive(cat, parent):
            new_iter = treestore.append(parent, [cat, cat.name])
            self.categories[cat.id] = new_iter
            for child_cat in cat.children:
                insert_recursive(child_cat, new_iter)
        self.categories = {}
        root_categories = account.get_root_categories()
        treestore = self.category_combobox.get_model()
        for cat in root_categories:
            insert_recursive(cat, None)

    def get_active_rule(self):
        return self.rules_tree.get_selected_item()[0]

    def save_active_rule(self):
        if self.active_rule:
            self.active_rule.rule = self.searchstring_entry.get_text()
            self.active_rule.priority = self.priority_entry.get_value()
            active_iter = self.category_combobox.get_active_iter()
            model = self.category_combobox.get_model()
            self.active_rule.category = model[active_iter][0]

    def on_searchstring_changed(self, searchstring_entry):
        model = self.rules_tree.get_model()
        new_text = searchstring_entry.get_text()
        model[self.rules_tree.get_selected_item()[1]][2] = new_text

    def on_active_toggled(self, cellrenderertoggle, path):
        model = self.rules_tree.get_model()
        active = not model[path][1]
        model[path][1] = active
        model[path][0].active = active

    def on_cursor_changed(self, widget):
        self.save_active_rule()
        self.active_rule = self.get_active_rule()
        if self.active_rule:
            self.searchstring_entry.set_text(self.active_rule.rule)
            self.priority_entry.set_value(self.active_rule.priority)
            active_iter = self.categories[self.active_rule.category.id]
            self.category_combobox.set_active_iter(active_iter)

    def on_add(self, widget, user_data=None):
        rule = account.CategoryFilter(rule="", priority=1, active=True)
        model = self.rules_tree.get_model()
        iterator = model.append([rule, rule.active, rule.rule])
        self.rules_tree.scroll_to_cell(model.get_path(iterator))

    def on_delete(self, widget, user_data=None):
        item, iterator = self.rules_tree.get_selected_item()
        if item is not None:
            item.delete()
            model = self.rules_tree.get_model()
            model.remove(iterator)

    def _init_widgets(self):
        # unused

        actiongroup.add_actions([
                ('refresh', Gtk.STOCK_REFRESH, 'reload preview tree', None, _('Reload preview tree'), self.refresh_preview),
                ('reset', Gtk.STOCK_CLEAR, 'reset preview tree', None, _('Reset the preview tree'), self.reset_preview),
                     ])
        toolbar.insert(actiongroup.get_action('refresh').create_tool_item(), -1)
        toolbar.insert(actiongroup.get_action('reset').create_tool_item(), -1)

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

