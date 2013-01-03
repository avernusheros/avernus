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
        self.preview_sw = builder.get_object("preview_sw")

        self.active_rule = None
        self.preview_active = None

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

    def _init_preview(self):
        self.preview_tree = PreviewTree()
        self.preview_sw.add(self.preview_tree)
        self.preview_tree.show()

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
        # insert None category
        treestore.append(None, [None, "None"])
        for cat in root_categories:
            insert_recursive(cat, None)

    def get_active_rule(self):
        item = self.rules_tree.get_selected_item()
        if item:
            return item[0]
        else:
            return None

    def save_active_rule(self):
        if self.active_rule:
            self.active_rule.rule = unicode(self.searchstring_entry.get_text())
            self.active_rule.priority = self.priority_entry.get_value()
            active_iter = self.category_combobox.get_active_iter()
            model = self.category_combobox.get_model()
            self.active_rule.category = model[active_iter][0]

    def on_searchstring_changed(self, searchstring_entry):
        model = self.rules_tree.get_model()
        new_text = unicode(searchstring_entry.get_text())
        model[self.rules_tree.get_selected_item()[1]][2] = new_text
        if self.preview_active:
            self.active_rule.rule = new_text
            self.preview_tree.refresh(self.active_rule)

    def on_active_toggled(self, cellrenderertoggle, path):
        model = self.rules_tree.get_model()
        active = not model[path][1]
        model[path][1] = active
        model[path][0].active = active

    def on_cursor_changed(self, widget):
        self.save_active_rule()
        self.active_rule = self.get_active_rule()
        if self.active_rule:
            self.set_sensitive(True)
            self.searchstring_entry.set_text(self.active_rule.rule)
            self.priority_entry.set_value(self.active_rule.priority)
            if self.active_rule.category:
                active_iter = self.categories[self.active_rule.category.id]
                self.category_combobox.set_active_iter(active_iter)
            else:
                # select None category
                self.category_combobox.set_active(0)
        else:
            self.set_sensitive(False)

    def set_sensitive(self, status):
        self.searchstring_entry.set_sensitive(status)
        self.priority_entry.set_sensitive(status)
        self.category_combobox.set_sensitive(status)

    def on_add(self, widget, user_data=None):
        rule = account.CategoryFilter(rule=_("insert searchstring"), priority=1, active=True)
        model = self.rules_tree.get_model()
        iterator = model.append([rule, rule.active, rule.rule])
        self.rules_tree.scroll_to_cell(model.get_path(iterator))

    def on_delete(self, widget, user_data=None):
        item, iterator = self.rules_tree.get_selected_item()
        if item is not None:
            item.delete()
            model = self.rules_tree.get_model()
            model.remove(iterator)

    def on_toggle_preview(self, widget):
        if self.preview_active == None:
            self._init_preview()
            self.preview_active = True
        else:
            self.preview_active = not self.preview_active
        if self.preview_active:
            self.preview_tree.refresh(self.active_rule)


class PreviewTree(gui_utils.Tree):
    OBJECT = 0
    DESCRIPTION = 1
    AMOUNT = 2
    DATE = 3
    ACCOUNT = 4

    def __init__(self):
        gui_utils.Tree.__init__(self)
        self.set_size_request(800, 300)
        self.model = Gtk.ListStore(object, str, float, object, str)
        self.modelfilter = self.model.filter_new(None)
        sorter = Gtk.TreeModelSort(model=self.modelfilter)
        self.set_model(sorter)
        self.modelfilter.set_visible_func(self.visible_cb, None)
        self.create_column(_('Date'), self.DATE, func=gui_utils.date_to_string, expand=False)
        sorter.set_sort_func(self.DATE, gui_utils.sort_by_datetime, self.DATE)
        col, cell = self.create_column(_('Description'), self.DESCRIPTION, func=gui_utils.transaction_desc_markup)
        cell.props.wrap_mode = Pango.WrapMode.WORD
        cell.props.wrap_width = 300
        self.create_column(_('Amount'), self.AMOUNT, func=gui_utils.currency_format, expand=False)
        self.create_column(_('Account'), self.ACCOUNT, expand=False)
        self.set_rules_hint(True)

        self.active_rule = None
        self.load_all()

    def visible_cb(self, model, iterator, user_data):
        transaction = model[iterator][self.OBJECT]
        if self.active_rule:
            return categorization_controller.match_transaction(self.active_rule,
                                                               transaction)
        return True

    def load_all(self):
        for trans in account.get_all_transactions():
            if not trans.transfer:
                self.model.append([trans,
                               trans.description,
                               trans.amount,
                               trans.date,
                               trans.account.name])

    def refresh(self, rule):
        self.active_rule = rule
        self.modelfilter.refilter()
