from avernus.controller import controller, filterController
from avernus.gui import gui_utils
import gtk
import pango


class FilterDialog(gtk.Dialog):

    def __init__(self, *args, **kwargs):
        gtk.Dialog.__init__(self, _("Account Category Filters"), None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self.set_size_request(800, 500)
        self._init_widgets()
        self.show_all()
        self.run()
        self.destroy()

    def _init_widgets(self):
        vpaned = gtk.VPaned()
        self.get_content_area().pack_start(vpaned)
        vbox = gtk.VBox()

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
        self.filter_tree = FilterTree()
        sw.add(self.filter_tree)
        vbox.pack_start(sw)

        actiongroup = gtk.ActionGroup('filter')
        actiongroup.add_actions([
                ('add',     gtk.STOCK_ADD,    'new transaction filter',    None, _('Add new transaction filter'), self.filter_tree.on_add),
                ('remove',  gtk.STOCK_DELETE, 'remove transaction filter', None, _('Remove selected transaction filter'), self.filter_tree.on_remove),
                ('refresh', gtk.STOCK_REFRESH,'reload preview tree',       None, _('Reload preview tree'), self.refresh_preview),
                ('reset',   gtk.STOCK_CLEAR,  'reset preview tree',        None, _('Reset the preview tree'), self.reset_preview),
                     ])
        toolbar = gtk.Toolbar()
        toolbar.insert(actiongroup.get_action('add').create_tool_item(), -1)
        toolbar.insert(actiongroup.get_action('remove').create_tool_item(), -1)
        toolbar.insert(gtk.SeparatorToolItem(), -1)
        toolbar.insert(actiongroup.get_action('refresh').create_tool_item(), -1)
        toolbar.insert(actiongroup.get_action('reset').create_tool_item(), -1)
        vbox.pack_start(toolbar, expand=False, fill=True)

        vpaned.add1(vbox)

        frame = gtk.Frame('Preview')
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
        self.preview_tree = PreviewTree()
        frame.add(sw)
        sw.add(self.preview_tree)
        vpaned.add2(frame)

    def refresh_preview(self, widget):
        # get the active rule and refresh the preview tree with it
        active_rule = self.filter_tree.get_active_filter()
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
        self.model = gtk.ListStore(object, str, float, str, object, str)
        self.modelfilter = self.model.filter_new()
        sorter = gtk.TreeModelSort(self.modelfilter)
        self.set_model(sorter)
        self.modelfilter.set_visible_func(self.visible_cb)
        self.create_column(_('Date'), self.DATE, func=gui_utils.date_to_string, expand=False)
        col, cell = self.create_column(_('Description'), self.DESCRIPTION, func=gui_utils.transaction_desc_markup)
        cell.props.wrap_mode = pango.WRAP_WORD
        cell.props.wrap_width = 300
        self.create_column(_('Amount'), self.AMOUNT, func=gui_utils.currency_format, expand=False)
        self.create_column(_('Category'), self.CATEGORY, expand=False)
        self.create_column(_('Account'), self.ACCOUNT, expand=False)
        self.set_rules_hint(True)

        self.active_filter = None
        self.load_all()

    def visible_cb(self, model, iter):
        transaction = model[iter][self.OBJECT]
        if transaction and transaction.is_transfer():
            return False
        if self.active_filter:
            return filterController.match_transaction(self.active_filter, transaction)
        return True

    def load_all(self):
        for trans in controller.getAllAccountTransactions():
            if trans.category:
                cat = trans.category.name
            else:
                cat = ''
            self.model.append([trans, trans.description, trans.amount, cat, trans.date, trans.account.name])

    def on_refresh(self, filter):
        self.active_filter = filter
        self.modelfilter.refilter()

    def reset(self):
        self.active_filter = None
        self.modelfilter.refilter()


class FilterTree(gui_utils.Tree):
    OBJECT = 0
    ACTIVE = 1
    PRIORITY = 2
    FILTER_STR = 3
    CATEGORY = 4
    CATEGORY_STR = 5

    def __init__(self):
        gui_utils.Tree.__init__(self)
        self.model = gtk.ListStore(object, bool, int, str, object, str)
        self.set_model(self.model)

        column, cell = self.create_check_column(_('Active'), self.ACTIVE)
        cell.connect("toggled", self.on_toggled)

        cell = gtk.CellRendererSpin()
        adjustment = gtk.Adjustment(1, 1, 100, 1, 10, 0)
        cell.set_property("editable", True)
        cell.set_property("adjustment", adjustment)
        cell.connect("edited", self.on_spin_edited)
        column = gtk.TreeViewColumn(_('Priority'), cell, text=self.PRIORITY)
        self.append_column(column)

        col, cell = self.create_column(_('Filter'), self.FILTER_STR, expand = True)
        cell.set_property('editable', True)
        cell.connect('edited', self.on_cell_edited)

        cell = gtk.CellRendererCombo()
        cell.connect('changed', self.on_category_changed)
        self.cb_model = gtk.ListStore(object, str)
        self.categories = sorted(controller.getAllAccountCategories())
        for category in self.categories:
            self.cb_model.append([category, category.name])
        cell.set_property('model', self.cb_model)
        cell.set_property('text-column', 1)
        cell.set_property('editable', True)
        column = gtk.TreeViewColumn(_('Category'), cell, text = self.CATEGORY_STR)
        self.append_column(column)

        self.load_rules()

    def get_active_filter(self):
        item, iter = self.get_selected_item()
        return item

    def load_rules(self):
        for rule in filterController.get_all():
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
        self.model[path][self.FILTER_STR] = self.model[path][self.OBJECT].rule = new_text

    def on_toggled(self, cellrenderertoggle, path):
        active = not self.model[path][self.ACTIVE]
        self.model[path][self.ACTIVE] = active
        self.model[path][self.OBJECT].active = active

    def on_add(self, widget):
        rule = filterController.create("new filter - click to edit", self.categories[0], False)
        iter = self.insert_rule(rule)
        self.scroll_to_cell(self.model.get_path(iter))

    def on_remove(self, widget):
        item, iter = self.get_selected_item()
        if item is not None:
            item.delete()
            self.model.remove(iter)

    def insert_rule(self, rule):
        return self.model.append([rule, rule.active, rule.priority, rule.rule, rule.category, rule.category.name])
