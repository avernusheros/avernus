#!/usr/bin/env pytho
from avernus import config
from avernus.config import avernusConfig
from avernus.gui import gui_utils, common_dialogs, page, charts
from avernus.gui import get_ui_file
from avernus.gui.portfolio import dialogs
from avernus.controller import chart_controller, account_controller, object_controller
from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import Gdk
from gi.repository import Pango
import datetime
import logging

logger = logging.getLogger(__name__)
builder = None


class AccountTransactionTab(page.Page):

    def __init__(self, account):
        page.Page.__init__(self)
        self.account = account
        self.config = config.avernusConfig()

        global builder
        builder = Gtk.Builder()
        builder.add_from_file(get_ui_file("account/account_transactions.glade"))

        vbox = builder.get_object("vbox")
        self.hpaned = builder.get_object("hpaned")
        category_sw = builder.get_object("category_sw")
        transactions_sw = builder.get_object("transactions_sw")
        self.start_entry = builder.get_object("start_entry")
        self.end_entry = builder.get_object("end_entry")
        self.search_entry = builder.get_object("search_entry")

        self.pack_start(vbox, True, True, 0)
        self.charts_notebook = None
        self.transactions_tree = TransactionsTree(account, self.update_ui)
        transactions_sw.add(self.transactions_tree)
        pre = self.config.get_option('account hpaned position', 'Gui')
        pos = pre or 600
        self.hpaned.set_position(int(pos))

        self.category_tree = CategoriesTree(self.transactions_tree.on_category_update)
        category_sw.add(self.category_tree)
        self.category_tree.on_unselect()

        self.transactions_tree.load_transactions()
        self.category_tree.load_categories()
        self.update_page()

        #connect signals
        self.connect("unrealize", self.on_unrealize)
        signals = {
                "on_category_add": self.category_tree.on_add,
                "on_category_edit": self.category_tree.on_edit,
                "on_category_remove": self.category_tree.on_remove,
                "on_category_unselect": self.category_tree.on_unselect,
                "on_expander_toggled": self.on_expander_toggled,
                "on_pick_start": self.on_pick_start,
                "on_pick_end": self.on_pick_end,
                "on_clear_search": self.on_clear_search,
                "on_toggle_uncategorized": self.transactions_tree.on_toggle_uncategorized,
                "on_toggle_transfer": self.transactions_tree.on_toggle_transfer,
                "on_search_entry_changed": self.transactions_tree.on_search_entry_changed
                  }
        builder.connect_signals(signals)
        self.show_all()

    def on_expander_toggled(self, expander, *args):
        if (not expander.get_expanded()):
            start = self.transactions_tree.range_start
            if start is None:
                start = account_controller.account_birthday(self.account)
            end = self.transactions_tree.range_end
            if end is None:
                end = datetime.date.today()
            self.charts_notebook = AccountChartsNotebook(self.account, (start, end))
            self.charts_notebook.show_all()
            expander.add(self.charts_notebook)
        else:
            expander.remove(self.charts_notebook)
            self.charts_notebook = None
        return True

    def on_toggled(self, widget, chart, setter):
        active = widget.get_active()
        setter(active)
        chart.draw_chart()

    def on_pick_start(self, entry, *args):
        dialog = common_dialogs.CalendarDialog(self.transactions_tree.range_start, parent=self.get_toplevel())
        if dialog.date:
            self.transactions_tree.range_start = dialog.date
            self.update_ui()
            self.start_entry.set_text(gui_utils.get_date_string(self.transactions_tree.range_start))

    def on_pick_end(self, entry, *args):
        dialog = common_dialogs.CalendarDialog(self.transactions_tree.range_end, parent=self.get_toplevel())
        if dialog.date:
            self.transactions_tree.range_end = dialog.date
            self.update_ui()
            self.end_entry.set_text(gui_utils.get_date_string(self.transactions_tree.range_end))

    def on_clear_search(self, entry, icon_pos, event):
        self.search_entry.set_text('')

    def get_info(self):
        return [('# transactions', len(self.transactions_tree.modelfilter)),
                ('Sum', gui_utils.get_currency_format_from_float(self.transactions_tree.get_filtered_transaction_value()))]

    def on_unrealize(self, widget):
        self.config.set_option('account hpaned position', self.hpaned.get_position(), 'Gui')

    def update_ui(self, *args):
        self.refilter()
        transactions = [row[0] for row in self.transactions_tree.modelfilter]
        if (not self.charts_notebook == None):
            for chart in self.charts_notebook.charts:
                chart.update(transactions, (self.transactions_tree.range_start, self.transactions_tree.range_end))
        self.update_page()

    def refilter(self):
        self.transactions_tree.modelfilter.refilter()
        count = len(self.transactions_tree.modelfilter)
        label = builder.get_object("no_transactions_label")
        scrolled_window = builder.get_object("transactions_sw")
        if count == 0:
            scrolled_window.hide()
            label.show()
        else:
            label.hide()
            scrolled_window.show()


class AccountChartsNotebook(Gtk.Notebook):

    def __init__(self, account, date_range):
        Gtk.Notebook.__init__(self)
        self.account = account
        self.date_range = date_range
        self.charts = []
        self.set_property('tab_pos', Gtk.PositionType.LEFT)
        self.init_charts()

    def init_charts(self):
        over_time_controller = chart_controller.TransactionValueOverTimeChartController(self.account.transactions, self.date_range)
        categoryChart = charts.TransactionChart(over_time_controller, 300)
        self.charts.append(categoryChart)
        label = Gtk.Label(label=_('Over Time'))
        #FIXME better tooltip
        label.set_tooltip_text(_('Account value over time.'))
        self.append_page(categoryChart, label)

        step_controller = chart_controller.TransactionStepValueChartController(self.account.transactions, self.date_range)
        valueChart = charts.TransactionChart(step_controller, 300)
        self.charts.append(valueChart)
        label = Gtk.Label(label=_('Step Value'))
        #FIXME better tooltip
        label.set_tooltip_text(_('step value.'))
        self.append_page(valueChart, label)

        controller = chart_controller.AccountBalanceOverTimeChartController(self.account, self.date_range)
        chart = charts.SimpleLineChart(controller, 300)
        self.charts.append(chart)
        label = Gtk.Label(label=_('Account balance'))
        label.set_tooltip_text(_('Account balance over the given time period.'))
        self.append_page(chart, label)

        table = Gtk.Table()
        controller = chart_controller.TransactionCategoryPieController(self.account.transactions, earnings=True)
        chart = charts.Pie(controller, 400)
        self.charts.append(chart)
        label = Gtk.Label()
        label.set_markup('<b>' + _('Earnings') + '</b>')
        label.set_tooltip_text(_('Categorization of earnings.'))
        table.attach(label, 0, 1, 0, 1, xoptions=Gtk.AttachOptions.FILL, yoptions=Gtk.AttachOptions.FILL)
        table.attach(chart, 0, 1, 1, 2)

        controller = chart_controller.TransactionCategoryPieController(self.account.transactions, earnings=False)
        chart = charts.Pie(controller, 400)
        self.charts.append(chart)
        label = Gtk.Label()
        label.set_markup('<b>' + _('Spendings') + '</b>')
        label.set_tooltip_text(_('Categorization of spendings.'))
        table.attach(label, 1, 2, 0, 1, xoptions=Gtk.AttachOptions.FILL, yoptions=Gtk.AttachOptions.FILL)
        table.attach(chart, 1, 2, 1, 2)

        label = Gtk.Label(label=_('Categories'))
        label.set_tooltip_text(_('Categorization of transactions.'))
        self.append_page(table, label)

        controller = chart_controller.EarningsVsSpendingsController(self.account.transactions, self.date_range)
        chart = charts.BarChart(controller, 400)
        self.charts.append(chart)
        label = Gtk.Label(label=_('Earnings vs Spendings'))
        label.set_tooltip_text(_('Earnings vs spendings in given time period.'))
        self.append_page(chart, label)


class TransactionsTree(gui_utils.Tree):

    OBJECT = 0
    DESCRIPTION = 1
    AMOUNT = 2
    CATEGORY = 3
    DATE = 4
    ICON = 5

    def __init__(self, account, updater):
        gui_utils.Tree.__init__(self)
        self.account = account
        self.updater = updater
        self.searchstring = ''
        self.b_show_transfer = True
        self.b_show_uncategorized = True
        self.range_start = None
        self.range_end = None

        self.model = Gtk.ListStore(object, str, float, str, object, str)
        self.modelfilter = self.model.filter_new(None)
        sorter = Gtk.TreeModelSort(model=self.modelfilter)
        self.set_model(sorter)
        self.modelfilter.set_visible_func(self.visible_cb, None)
        self.create_icon_column('', self.ICON)
        self.create_column(_('Date'), self.DATE, func=gui_utils.date_to_string)
        sorter.set_sort_func(self.DATE, gui_utils.sort_by_time, self.DATE)
        col, cell = self.create_column(_('Description'), self.DESCRIPTION, func=gui_utils.transaction_desc_markup)
        cell.props.wrap_mode = Pango.WrapMode.WORD
        cell.props.wrap_width = 400
        col.set_expand(True)
        self.create_column(_('Amount'), self.AMOUNT, func=gui_utils.currency_format)

        cell = Gtk.CellRendererCombo()
        cb_model = Gtk.ListStore(object, str)
        cell.connect('changed', self.on_category_changed, cb_model)
        self.categories = account_controller.get_all_categories()
        for category in self.categories:
            cb_model.append([category, category.name])
        cell.set_property('model', cb_model)
        cell.set_property('text-column', 1)
        cell.set_property('editable', True)
        column = Gtk.TreeViewColumn(_('Category'), cell, text = self.CATEGORY)
        self.append_column(column)

        self.set_rules_hint(True)
        sorter.set_sort_column_id(self.DATE, Gtk.SortType.DESCENDING)
        self.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)

        self.connect('button_press_event', self.on_button_press)
        self.connect('key_press_event', self.on_key_press)
        self.account.connect('transaction_added', self.on_transaction_added)

        # actions
        self.actiongroup = Gtk.ActionGroup('transactions')
        self.actiongroup.add_actions([
                ('add', Gtk.STOCK_ADD, 'new transaction', None, _('Add new transaction'), self.on_add),
                ('edit' , Gtk.STOCK_EDIT, 'edit transaction', None, _('Edit selected transaction'), self.on_edit),
                ('remove', Gtk.STOCK_DELETE, 'remove transaction', None, _('Remove selected transaction'), self.on_remove),
                ('dividend', Gtk.STOCK_CONVERT, 'dividend payment', None, _('Create dividend from transaction'), self.on_dividend)
                ])

        self.single_category = None
        self.columns_autosize()

    def on_category_changed(self, cellrendertext, path, new_iter, model):
        category = model[new_iter][0]
        self.on_set_transaction_category(category)

    def on_category_update(self, category):
        if category != self.single_category:
            self.single_category = category
            self.updater()

    def visible_cb(self, model, iter, userdata):
        transaction = model[iter][0]
        if transaction:
            if self.single_category:
                # return False if the category does not match, move on to the
                # other checks if it does
                if not transaction.category:
                    # if it does not have a category, it cannot be true
                    return False
                if not transaction.category == self.single_category:
                    # if the category does not match the selected there is still
                    # the chance that recursive is activated
                    config = avernusConfig()
                    pre = config.get_option('categoryChildren', 'Account')
                    pre = pre == "True"
                    if pre:
                        # recursive is activated
                        #print "second chance", transaction
                        parents = account_controller.get_parent_categories(transaction.category)
                        if not self.single_category in parents:
                            # the selected category is also not one of the parents
                            return False
                    else:
                        # recursive is deactivated, wrong category
                        return False
            if (
                self.searchstring in transaction.description.lower() \
                or self.searchstring in str(transaction.amount) \
                or (transaction.category and self.searchstring in transaction.category.name.lower())
                )\
                and (self.b_show_transfer or not transaction.transfer)\
                and (self.b_show_uncategorized or transaction.category):

                if (self.range_start is None or transaction.date >= self.range_start) \
                    and (self.range_end is None or transaction.date <= self.range_end):
                    return True
        return False

    def on_search_entry_changed(self, editable):
        self.searchstring = editable.get_text().lower()
        self.updater()

    def on_transaction_added(self, account, transaction, *args):
        self.insert_transaction(transaction)

    def find_transaction(self, transaction):
        for row in self.model:
            if row[0] == transaction:
                return row
        return None

    def get_item_to_insert(self, ta):
        if ta.category:
            cat = ta.category.name
        else:
            cat = ''
        if ta.transfer:
            icon = 'gtk-convert'
        else:
            icon = ''
        return [ta, ta.description, ta.amount, cat, ta.date, icon]

    def get_filtered_transaction_value(self):
        sum = 0
        for row in self.modelfilter:
            sum += row[self.AMOUNT]
        return sum

    def load_transactions(self):
        for ta in self.account:
            self.insert_transaction(ta)

    def insert_transaction(self, ta):
        self.model.append(self.get_item_to_insert(ta))

    def _get_selected_transaction(self):
        selection = self.get_selection()
        model, paths = selection.get_selected_rows()
        if len(paths) != 0:
            return self.get_model()[paths[0]][self.OBJECT], model.get_iter(paths[0])
        return None, None

    def on_add(self, widget=None, data=None):
        dlg = EditTransaction(self.account, parent=self.get_toplevel())
        dlg.start()

    def on_edit(self, widget=None, data=None):
        transaction, iterator = self._get_selected_transaction()
        old_amount = transaction.amount
        dlg = EditTransaction(self.account, transaction, parent=self.get_toplevel())
        b_change, transaction = dlg.start()
        if b_change:
            self.account.balance = self.account.balance - old_amount + transaction.amount
            child_iter = self._get_child_iter(iterator)
            self.model.remove(child_iter)
            self.insert_transaction(transaction)

    def on_dividend(self, widget=None, data=None):
        trans, iterator = self._get_selected_transaction()
        dialogs.DividendDialog(date=trans.date, price=trans.amount, parent=self.get_toplevel())

    def on_remove(self, widget=None, data=None):
        trans, iterator = self._get_selected_transaction()
        dlg = Gtk.MessageDialog(None,
                 Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.QUESTION,
                    Gtk.ButtonsType.OK_CANCEL, _("Permanently delete transaction?"))
        response = dlg.run()
        dlg.destroy()
        if response == Gtk.ResponseType.OK:
            trans.account.balance -= trans.amount
            object_controller.delete_object(trans)
            child_iter = self._get_child_iter(iterator)
            self.model.remove(child_iter)

    def _get_child_iter(self, iterator):
        child_iter = self.get_model().convert_iter_to_child_iter(iterator)
        return self.modelfilter.convert_iter_to_child_iter(child_iter)

    def on_set_transaction_category(self, category=None):
        trans, iterator = self._get_selected_transaction()
        trans.category = category
        if category:
            name = category.name
        else:
            name = ""
        self.model[self._get_child_iter(iterator)][self.CATEGORY] = name

    def show_context_menu(self, event):
        trans, iter = self._get_selected_transaction()
        self.context_menu = gui_utils.ContextMenu()
        if trans:
            for action in self.actiongroup.list_actions():
                self.context_menu.add(action.create_menu_item())
            if trans.category:
                self.context_menu.add_item('Remove category', lambda widget: self.on_set_transaction_category())

            def insert_recursive(cat, menu):
                item = Gtk.MenuItem(label=cat.name)
                menu.append(item)
                if len(cat.children) > 0:
                    new_menu = Gtk.Menu()
                    item.set_submenu(new_menu)
                    item = Gtk.MenuItem(label=cat.name)
                    new_menu.append(item)
                    item.connect('activate', lambda widget: self.on_set_transaction_category(cat))
                    new_menu.append(Gtk.SeparatorMenuItem())
                    for child_cat in cat.children:
                        insert_recursive(child_cat, new_menu)
                else:
                    item.connect('activate', lambda widget: self.on_set_transaction_category(cat))
            root_categories = account_controller.get_root_categories()
            if len(root_categories) > 0:
                item = Gtk.MenuItem(label="Move to category")
                self.context_menu.add(item)
                category_menu = Gtk.Menu()
                item.set_submenu(category_menu)
                for cat in root_categories:
                    insert_recursive(cat, category_menu)
        else:
            self.context_menu.add(self.actiongroup.get_action('add').create_menu_item())
        self.context_menu.show_all()
        self.context_menu.popup(None, None, None, None, event.button, event.time)

    def on_key_press(self, widget, event):
        if Gdk.keyval_name(event.keyval) == 'Delete':
            self.on_remove()
            return True
        return False

    def on_button_press(self, widget, event):
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            self.on_edit(widget)
            return False
        if event.button == 3:
            self.show_context_menu(event)

    def on_toggle_uncategorized(self, button):
        if button.get_active():
            self.b_show_uncategorized = True
        else:
            self.b_show_uncategorized = False
        self.updater()

    def on_toggle_transfer(self, button):
        if button.get_active():
            self.b_show_transfer = True
        else:
            self.b_show_transfer = False
        self.updater()


class CategoriesTree(gui_utils.Tree):

    def __init__(self, updater):
        gui_utils.Tree.__init__(self)
        self.updater = updater
        self.model = Gtk.TreeStore(object, str)
        self.set_model(self.model)
        col, self.cell = self.create_column(_('Categories'), 1)
        self.cell.set_property('editable', True)

        #drag n drop
        self.set_reorderable(True)

        #connect signals
        self.cell.connect('edited', self.on_cell_edited)
        self.connect('cursor_changed', self.on_cursor_changed)
        self.connect('button_press_event', self.on_button_press)
        #FIXME
        #self.connect('key_press_event', self.on_key_press)
        self.model.connect('row_changed', self.on_row_changed)

        # actions
        self.actiongroup1 = Gtk.ActionGroup('categories1')
        self.actiongroup1.add_actions([
                ('edit' , Gtk.STOCK_EDIT, 'rename category', None, _('Rename selected category'), self.on_edit),
                ('remove', Gtk.STOCK_DELETE, 'remove category', None, _('Remove selected category'), self.on_remove),
                ('unselect', Gtk.STOCK_CLEAR, 'unselect category', None, _('Unselect selected category'), self.on_unselect),
                     ])
        self.actiongroup2 = Gtk.ActionGroup('categories2')
        self.actiongroup2.add_actions([
                ('add', Gtk.STOCK_ADD, 'new category', None, _('Add new category'), self.on_add)
            ])
        # toolbar
        toolbar = builder.get_object("category_tb")
        toolbar.get_style_context().add_class("inline-toolbar")
        for action in self.actiongroup2.list_actions() + self.actiongroup1.list_actions():
            toolbar.insert(action.create_tool_item(), -1)

    def load_categories(self):
        def insert_recursive(cat, parent):
            new_iter = model.append(parent, [cat, cat.name])
            for child_cat in cat.children:
                insert_recursive(child_cat, new_iter)
        model = self.get_model()
        root_categories = account_controller.get_root_categories()
        for cat in root_categories:
            insert_recursive(cat, None)
        self.expand_all()

    def insert_item(self, cat, parent=None):
        return self.get_model().append(parent, [cat, cat.name])

    def on_add(self, widget=None, data=None):
        parent, selection_iter = self.get_selected_item()
        item = account_controller.new_account_category('new category', parent=parent)
        iterator = self.insert_item(item, parent=selection_iter)
        model = self.get_model()
        if selection_iter:
            self.expand_row(model.get_path(selection_iter), True)
        self.cell.set_property('editable', True)
        self.set_cursor(model.get_path(iterator), start_editing=True)

    def on_row_changed(self, model, path, iterator):
        value = self.model[iterator][0]
        parent_iter = self.model.iter_parent(iterator)
        if parent_iter:
            parent = self.model[parent_iter][0]
        else:
            parent = None
        value.parent = parent

    def on_edit(self, widget=None, data=None):
        cat, selection_iter = self.get_selected_item()
        self.cell.set_property('editable', True)
        self.set_cursor(self.get_model().get_path(selection_iter), self.get_column(0), start_editing=True)

    def on_remove(self, widget=None, data=None):
        obj, iterator = self.get_selected_item()
        if obj is None:
            return False
        dlg = Gtk.MessageDialog(None,
             Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.QUESTION,
             Gtk.ButtonsType.OK_CANCEL)
        msg = _("Permanently delete category <b>") + GObject.markup_escape_text(obj.name) + '</b>?'
        model = self.get_model()
        if model.iter_has_child(iterator):
            msg += _("\nWill also delete subcategories")
        dlg.set_markup(_(msg))
        response = dlg.run()
        dlg.destroy()
        if response == Gtk.ResponseType.OK:
            queue = [(iterator, obj)]
            removeQueue = []
            while len(queue) > 0:
                currIter, currObj = queue.pop()
                object_controller.delete_object(currObj)
                if model.iter_has_child(currIter):
                    for i in range(0, model.iter_n_children(currIter)):
                        newIter = model.iter_nth_child(currIter, i)
                        queue.append((newIter, model[newIter][0]))
                removeQueue.insert(0, currIter)
            for toRemove in removeQueue:
                model.remove(toRemove)
            self.on_unselect()

    def on_cell_edited(self, cellrenderertext, path, new_text):
        m = self.get_model()
        m[path][0].name = m[path][1] = unicode(new_text)
        cellrenderertext.set_property('editable', False)

    def show_context_menu(self, event):
        context_menu = Gtk.Menu()
        for action in self.actiongroup2.list_actions() + self.actiongroup1.list_actions():
            context_menu.add(action.create_menu_item())
        context_menu.popup(None, None, None, None, event.button, event.time)

    def on_button_press(self, widget, event):
        if event.button == 3:
            self.show_context_menu(event)
        else:
            if not self.get_path_at_pos(int(event.x), int(event.y)):
                self.on_unselect()
        return False

    def on_key_press(self, widget, event):
        if Gdk.keyval_name(event.keyval) == 'Delete':
            self.on_remove()
            return True
        return False

    def on_cursor_changed(self, widget):
        cat, iterator = self.get_selected_item()
        if cat is not None:
            self.on_select(cat)
        else:
            self.on_unselect()

    def on_unselect(self, widget=None, data=None):
        selection = self.get_selection()
        if selection != None:
            self.updater(None)
            selection.unselect_all()
            self.actiongroup1.set_sensitive(False)

    def on_select(self, obj):
        self.updater(obj)
        self.actiongroup1.set_sensitive(True)


class EditTransaction(Gtk.Dialog):

    def __init__(self, account, transaction=None, parent=None):
        Gtk.Dialog.__init__(self, _("Edit transaction"), parent
                            , Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                     (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                      Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        self.transaction = transaction
        vbox = self.get_content_area()

        if self.transaction is None:
            self.transaction = account_controller.new_account_transaction(account=account)

        #description
        frame = Gtk.Frame(label='Description')
        self.description_entry = Gtk.TextView()
        self.description_entry.set_wrap_mode(Gtk.WrapMode.WORD)
        entry_buffer = self.description_entry.get_buffer()
        entry_buffer.set_text(self.transaction.description)
        frame.add(self.description_entry)
        vbox.pack_start(frame, True, True, 0)

        #amount
        hbox = Gtk.HBox()
        label = Gtk.Label(label=_('Amount'))
        hbox.pack_start(label, False, False, 0)
        self.amount_entry = Gtk.SpinButton(adjustment=Gtk.Adjustment(lower= -999999999, upper=999999999, step_increment=10, value=self.transaction.amount), digits=2)
        hbox.pack_start(self.amount_entry, True, True, 0)
        vbox.pack_start(hbox, False, False, 0)

        #category
        hbox = Gtk.HBox()
        label = Gtk.Label(label=_('Category'))
        hbox.pack_start(label, False, False, 0)
        treestore = Gtk.TreeStore(object, str)
        self.combobox = Gtk.ComboBox(model=treestore)
        cell = Gtk.CellRendererText()
        self.combobox.pack_start(cell, False)
        self.combobox.add_attribute(cell, 'text', 1)

        def insert_recursive(cat, parent):
            new_iter = treestore.append(parent, [cat, cat.name])
            if cat == self.transaction.category:
                self.combobox.set_active_iter(new_iter)
            for child_cat in cat.children:
                insert_recursive(child_cat, new_iter)
        new_iter = treestore.append(None, [None, 'None'])
        self.combobox.set_active_iter(new_iter)
        root_categories = account_controller.get_root_categories()
        for cat in root_categories:
            insert_recursive(cat, None)

        hbox.pack_start(self.combobox, False, False, 0)
        vbox.pack_start(hbox, False, False, 0)

        #date
        self.calendar = Gtk.Calendar()
        self.calendar.select_month(self.transaction.date.month - 1, self.transaction.date.year)
        self.calendar.select_day(self.transaction.date.day)
        vbox.pack_start(self.calendar, False, False, 0)

        #transfer
        text = "Transfer: this transaction will not be shown in any of the graphs."
        self.transfer_button = Gtk.CheckButton(text)
        if self.transaction.transfer:
            self.transfer_button.set_active(True)
        vbox.pack_start(self.transfer_button, False, False, 0)

        self.matching_transactions_tree = gui_utils.Tree()
        model = Gtk.ListStore(object, str, str, object)
        self.matching_transactions_tree.set_model(model)
        self.matching_transactions_tree.create_column(_('Account'), 1)
        col, cell = self.matching_transactions_tree.create_column(_('Description'), 2)
        cell.props.wrap_width = 200
        cell.props.wrap_mode = Pango.WrapMode.WORD
        self.matching_transactions_tree.create_column(_('Date'), 3, func=gui_utils.date_to_string)
        vbox.pack_end(self.matching_transactions_tree, True, True, 0)
        self.no_matches_label = Gtk.Label(label='No matching transactions found. Continue only if you want to mark this as a tranfer anyway.')
        vbox.pack_end(self.no_matches_label, True, True, 0)

        #connect signals
        self.transfer_button.connect("toggled", self.on_transfer_toggled)
        self.matching_transactions_tree.connect('cursor_changed', self.on_transfer_transaction_selected)

    def start(self):
        self.show_all()
        self.matching_transactions_tree.hide()
        self.no_matches_label.hide()
        return self.process_result(self.run())

    def on_transfer_toggled(self, checkbutton):
        if checkbutton.get_active():
            found_one = False
            for ta in account_controller.yield_matching_transfer_transactions(self.transaction):
                if found_one == False:
                    self.matching_transactions_tree.clear()
                    self.matching_transactions_tree.show()
                    found_one = True
                self.matching_transactions_tree.get_model().append([ta, ta.account.name, ta.description, ta.date])
            self.transfer_transaction = self.transaction
            if not found_one:
                self.no_matches_label.show()
        else:
            self.matching_transactions_tree.hide()
            self.no_matches_label.hide()

    def on_transfer_transaction_selected(self, widget):
        selection = widget.get_selection()
        if selection:
            treestore, selection_iter = selection.get_selected()
            if (selection_iter and treestore):
                self.transfer_transaction = treestore.get_value(selection_iter, 0)

    def process_result(self, response):
        if response == Gtk.ResponseType.ACCEPT:
            buffer = self.description_entry.get_buffer()
            self.transaction.description = unicode(buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True), encoding="utf8")
            self.transaction.amount = self.amount_entry.get_value()
            year, month, day = self.calendar.get_date()
            self.transaction.date = datetime.date(year, month + 1, day)
            iter = self.combobox.get_active_iter()
            if iter is None:
                self.transaction.category = None
            else:
                self.transaction.category = self.combobox.get_model()[self.combobox.get_active_iter()][0]
            if self.transfer_button.get_active():
                self.transaction.transfer = self.transfer_transaction
                self.transfer_transaction.transfer = self.transaction
            elif self.transaction.transfer is not None:
                self.transaction.transfer.transfer = None
                self.transaction.transfer = None
        self.destroy()
        return response == Gtk.ResponseType.ACCEPT, self.transaction
