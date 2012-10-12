#!/usr/bin/env python
from avernus import config
from avernus.config import avernusConfig
from avernus.controller import chart_controller
from avernus.gui import get_ui_file, gui_utils, common_dialogs, page, charts
from avernus.gui.account import edit_transaction_dialog, categories_tree
from avernus.gui.portfolio import dividend_dialog
from avernus.objects import account
from gi.repository import Gdk, Gtk, Pango
import datetime
import logging


logger = logging.getLogger(__name__)


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

        self.category_tree = categories_tree.CategoriesTree(self.transactions_tree.on_category_update, builder)
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
                start = self.account.birthday
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
        date_range = (self.transactions_tree.range_start, self.transactions_tree.range_end)
        if (not self.charts_notebook == None):
            for chart in self.charts_notebook.charts:
                chart.update(transactions, date_range)
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

        controller = chart_controller.AccountBalanceController(self.account, self.date_range)
        chart = charts.SimpleLineChart(controller, 300)
        self.charts.append(chart)
        label = Gtk.Label(label=_('Account balance'))
        label.set_tooltip_text(_('Account balance over the given time period.'))
        self.append_page(chart, label)

        ta_value_controller = chart_controller.TransactionValueChartController(self.account.transactions)
        categoryChart = charts.BarChart(ta_value_controller, 300)
        self.charts.append(categoryChart)
        label = Gtk.Label(label=_('Transaction value'))
        label.set_tooltip_text(_('Transaction value'))
        self.append_page(categoryChart, label)

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

        #FIXME
        #controller = chart_controller.EarningsVsSpendingsController(self.account.transactions, self.date_range)
        #chart = charts.BarChart(controller, 400)
        #self.charts.append(chart)
        #label = Gtk.Label(label=_('Earnings vs Spendings'))
        #label.set_tooltip_text(_('Earnings vs spendings in given time period.'))
        #self.append_page(chart, label)


class TransactionsTree(gui_utils.Tree):

    OBJECT = 0
    DESCRIPTION = 1
    AMOUNT = 2
    CATEGORY = 3
    DATE = 4
    ICON = 5

    def __init__(self, acc, updater):
        gui_utils.Tree.__init__(self)
        self.account = acc
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
        self.categories = account.get_all_categories()
        for category in self.categories:
            cb_model.append([category, category.name])
        cell.set_property('model', cb_model)
        cell.set_property('text-column', 1)
        cell.set_property('editable', True)
        column = Gtk.TreeViewColumn(_('Category'), cell, text=self.CATEGORY)
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
                ('edit', Gtk.STOCK_EDIT, 'edit transaction', None, _('Edit selected transaction'), self.on_edit),
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

    def visible_cb(self, model, iterator, userdata):
        transaction = model[iterator][0]
        if transaction:
            # check settings
            if not self.b_show_transfer and transaction.transfer:
                return False
            if not self.b_show_uncategorized and not transaction.category:
                return False

            # check categoriess
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
                        parents = transaction.category.get_parent_categories()
                        if not self.single_category in parents:
                            # the selected category is also not one of the parents
                            return False
                    else:
                        # recursive is deactivated, wrong category
                        return False

            # check daterange
            if self.range_start and transaction.date < self.range_start \
                    or self.range_end and transaction.date > self.range_end:
                return False

            # check searchstring
            if not self.searchstring:
                return True
            if self.searchstring in transaction.description.lower() \
                    or self.searchstring in str(transaction.amount) \
                    or transaction.category and self.searchstring in transaction.category.name.lower():
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
        ret = 0
        for row in self.modelfilter:
            ret += row[self.AMOUNT]
        return ret

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
        dlg = edit_transaction_dialog.EditTransactionDialog(self.account, parent=self.get_toplevel())
        dlg.start()

    def on_edit(self, widget=None, data=None):
        transaction, iterator = self._get_selected_transaction()
        old_amount = transaction.amount
        dlg = edit_transaction_dialog.EditTransactionDialog(self.account, transaction, parent=self.get_toplevel())
        b_change, transaction = dlg.start()
        if b_change:
            self.account.balance = self.account.balance - old_amount + transaction.amount
            child_iter = self._get_child_iter(iterator)
            self.model.remove(child_iter)
            self.insert_transaction(transaction)

    def on_dividend(self, widget=None, data=None):
        trans, iterator = self._get_selected_transaction()
        dividend_dialog.DividendDialog(date=trans.date, price=trans.amount, parent=self.get_toplevel())

    def on_remove(self, widget=None, data=None):
        trans, iterator = self._get_selected_transaction()
        dlg = Gtk.MessageDialog(None,
                 Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.QUESTION,
                    Gtk.ButtonsType.OK_CANCEL, _("Permanently delete transaction?"))
        response = dlg.run()
        dlg.destroy()
        if response == Gtk.ResponseType.OK:
            trans.account.balance -= trans.amount
            trans.delete()
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
            root_categories = account.get_root_categories()
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
