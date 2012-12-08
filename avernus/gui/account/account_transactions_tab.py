#!/usr/bin/env python
from avernus import config
from avernus.config import avernusConfig
from avernus.controller import chart_controller
from avernus.gui import get_avernus_builder, gui_utils, common_dialogs, page, \
    charts
from avernus.gui.account import edit_transaction_dialog
from avernus.gui.portfolio import dividend_dialog
from avernus.objects import account
from gi.repository import Gdk, Gtk, GObject
import datetime
import logging

logger = logging.getLogger(__name__)


class AccountTransactionTab(page.Page):

    OBJECT = 0
    DESCRIPTION = 1
    AMOUNT = 2
    DATE = 4

    def __init__(self):
        page.Page.__init__(self)
        self.config = config.avernusConfig()

        self.searchstring = ''
        self.b_show_transfer = True
        self.b_show_uncategorized = True
        self.single_category = None
        self.range_start = None
        self.range_end = None
        self.context_menu_setup = False
        self.builder = get_avernus_builder()
        self.charts_notebook = None

        self.widget = self.builder.get_object("account_vbox")
        self.hpaned = self.builder.get_object("account_hpaned")
        self.category_tree = self.builder.get_object("category_tree")
        self.start_entry = self.builder.get_object("start_entry")
        self.end_entry = self.builder.get_object("end_entry")
        self.search_entry = self.builder.get_object("search_entry")
        self.category_actiongroup = self.builder.get_object("category_actiongroup")
        self.category_context_menu = self.builder.get_object("category_context_menu")

        self.widget.connect("draw", self.update_page)
        pre = self.config.get_option('account hpaned position', 'Gui')
        pos = pre or 600
        self.hpaned.set_position(int(pos))

        self._init_categories_tree()
        self._init_transactions_tree()

    def set_account(self, account):
        self.account = account
        self.model.clear()
        for ta in self.account:
            self.model.append(self.get_item_to_insert(ta))
        self.signal_id = self.account.connect('transaction_added', self.on_transaction_added)
        self.update_page()

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

    def close(self):
        if self.account:
            self.account.disconnect(self.signal_id)
        self.model.clear()

    def _init_categories_tree(self):
        # load categories
        def insert_recursive(cat, parent):
            new_iter = model.append(parent, [cat, cat.name])
            for child_cat in cat.children:
                insert_recursive(child_cat, new_iter)
        model = self.category_tree.get_model()
        root_categories = account.get_root_categories()
        for cat in root_categories:
            insert_recursive(cat, None)
        self.category_tree.expand_all()

    def _init_transactions_tree(self):
        self.transactions_tree = self.builder.get_object("account_transactions_tree")
        self.modelfilter = self.builder.get_object("treemodelfilter1")
        self.model = self.modelfilter.get_model()
        self.modelfilter.set_visible_func(self.visible_cb, None)
        sorter = self.builder.get_object("treemodelsort1")
        sorter.set_sort_func(self.DATE, gui_utils.sort_by_datetime, self.DATE)
        self.model.set_sort_func(self.DATE, gui_utils.sort_by_datetime, self.DATE)

        if self.config.get_option('transactionGrid', 'Account') == 'True':
            self.transactions_tree.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)

        # date format
        cell = self.builder.get_object("cellrenderertext3")
        column = self.builder.get_object("treeviewcolumn4")
        column.set_cell_data_func(cell, gui_utils.date_to_string, self.DATE)
        # amount format
        cell = self.builder.get_object("cellrenderertext4")
        column = self.builder.get_object("treeviewcolumn5")
        column.set_cell_data_func(cell, gui_utils.currency_format, self.AMOUNT)
        # description format
        cell = self.builder.get_object("cellrenderertext2")
        column = self.builder.get_object("treeviewcolumn2")
        column.set_cell_data_func(cell, gui_utils.transaction_desc_markup, self.DESCRIPTION)
        column.set_expand(True)

    def on_row_changed(self, model, path, iterator):
        value = model[iterator][0]
        parent_iter = model.iter_parent(iterator)
        if parent_iter:
            parent = model[parent_iter][0]
        else:
            parent = None
        value.parent = parent

    def on_category_edited(self, cellrenderertext, path, new_text):
        model = self.category_tree.get_model()
        model[path][0].name = model[path][1] = unicode(new_text)

    def on_edit_category(self, widget):
        cat, selection_iter = self.get_selected_category()
        model = self.category_tree.get_model()
        self.category_tree.set_cursor(model.get_path(selection_iter),
                                      self.category_tree.get_column(0),
                                      start_editing=True)

    def on_category_cursor_changed(self, widget):
        cat, iterator = self.get_selected_category()
        if cat:
            self.on_select_category(cat)
        else:
            self.on_unselect_category()

    def on_category_tree_button_press(self, widget, event):
        if event.button == 3:
            self.category_context_menu.popup(None, None, None, None, event.button, event.time)
        else:
            if not widget.get_path_at_pos(int(event.x), int(event.y)):
                self.on_unselect_category()
        return False

    def on_acc_transaction_button_press(self, widget, event):
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            self.on_edit_transaction(widget)
            return False
        elif event.button == 3:
            self.show_transaction_context_menu(event)
            self.update_ui()

    def show_transaction_context_menu(self, event):
        def insert_recursive(cat, menu):
            item = Gtk.MenuItem(label=cat.name)
            menu.append(item)
            if len(cat.children) > 0:
                new_menu = Gtk.Menu()
                item.set_submenu(new_menu)
                item = Gtk.MenuItem(label=cat.name)
                new_menu.append(item)
                item.connect('activate', self.on_set_transaction_category, cat)
                new_menu.append(Gtk.SeparatorMenuItem())
                for child_cat in cat.children:
                    insert_recursive(child_cat, new_menu)
            else:
                item.connect('activate', self.on_set_transaction_category, cat)
        context_menu = self.builder.get_object("acc_transaction_contextmenu")
        if not self.context_menu_setup:
            self.context_menu_setup = True
            root_categories = account.get_root_categories()
            if root_categories:
                item = Gtk.MenuItem(label="Move to category")
                context_menu.add(item)
                category_menu = Gtk.Menu()
                item.set_submenu(category_menu)
                for cat in root_categories:
                    insert_recursive(cat, category_menu)
        context_menu.show_all()
        context_menu.popup(None, None, None, None, event.button, event.time)

    def on_add_category(self, widget):
        parent, selection_iter = self.get_selected_category()
        cat = account.AccountCategory(name='new category', parent=parent)
        model = self.category_tree.get_model()
        iterator = model.append(selection_iter, [cat, cat.name])
        if selection_iter:
            self.category_tree.expand_row(model.get_path(selection_iter), True)
        self.category_tree.set_cursor(model.get_path(iterator), start_editing=True)

    def on_remove_category(self, widget):
        obj, iterator = self.get_selected_category()
        if not obj:
            return False
        dlg = Gtk.MessageDialog(None,
             Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.QUESTION,
             Gtk.ButtonsType.OK_CANCEL)
        msg = _("Permanently delete category <b>") + GObject.markup_escape_text(obj.name) + '</b>?'
        model = self.category_tree.get_model()
        if model.iter_has_child(iterator):
            msg += _("\nWill also delete subcategories")
        dlg.set_markup(_(msg))
        response = dlg.run()
        dlg.destroy()
        if response == Gtk.ResponseType.OK:
            queue = [(iterator, obj)]
            remove_queue = []
            while len(queue) > 0:
                curr_iter, curr_obj = queue.pop()
                curr_obj.delete()
                if model.iter_has_child(curr_iter):
                    for i in range(0, model.iter_n_children(curr_iter)):
                        new_iter = model.iter_nth_child(curr_iter, i)
                        queue.append((new_iter, model[new_iter][0]))
                remove_queue.insert(0, curr_iter)
            for to_remove in remove_queue:
                model.remove(to_remove)
            self.on_unselect_category()

    def on_category_tree_key_press(self, widget, event):
        if Gdk.keyval_name(event.keyval) == 'Delete':
            self.on_remove_category(widget)
            return True
        return False

    def on_account_transactions_tree_key_press(self, widget, event):
        if Gdk.keyval_name(event.keyval) == 'Delete':
            self.on_remove_transaction(widget)
            return True
        return False

    def on_unselect_category(self, widget=None, data=None):
        selection = self.category_tree.get_selection()
        if selection:
            self.on_category_update(None)
            selection.unselect_all()
            self.category_actiongroup.set_sensitive(False)

    def on_select_category(self, obj):
        self.on_category_update(obj)
        self.category_actiongroup.set_sensitive(True)

    def on_category_update(self, category):
        if category != self.single_category:
            self.single_category = category
            self.update_ui()

    def on_expander_toggled(self, expander, *args):
        if (not expander.get_expanded()):
            start = self.range_start
            if not start:
                start = self.account.birthday
            end = self.range_end
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
        dialog = common_dialogs.CalendarDialog(self.range_start,
                                        parent=self.widget.get_toplevel())
        if dialog.date:
            self.range_start = dialog.date
            self.update_ui()
            self.start_entry.set_text(gui_utils.get_date_string(self.range_start))

    def on_pick_end(self, entry, *args):
        dialog = common_dialogs.CalendarDialog(self.range_end,
                                        parent=self.widget.get_toplevel())
        if dialog.date:
            self.range_end = dialog.date
            self.update_ui()
            self.end_entry.set_text(gui_utils.get_date_string(self.range_end))

    def on_transaction_added(self, account, transaction, *args):
        self.model.append(self.get_item_to_insert(transaction))

    def on_clear_search(self, entry, icon_pos, event):
        self.search_entry.set_text('')

    def get_selected_category(self):
        selection = self.category_tree.get_selection()
        if selection:
            # Get the selection iter
            model, selection_iter = selection.get_selected()
            if selection_iter and model:
                return model[selection_iter][0], selection_iter
        return None, None

    def get_selected_transaction(self):
        selection = self.transactions_tree.get_selection()
        if selection:
            model, selection_iter = selection.get_selected()
            if selection_iter and model:
                return model[selection_iter][0], selection_iter
        return None, None

    def get_info(self):
        transaction_sum = sum([row[0].amount for row in self.modelfilter])
        return [('# transactions', len(self.modelfilter)),
                ('Sum', gui_utils.get_currency_format_from_float(transaction_sum))]

    def on_unrealize(self, widget):
        self.config.set_option('account hpaned position', self.hpaned.get_position(), 'Gui')

    def update_ui(self, *args):
        self.modelfilter.refilter()
        model = self.transactions_tree.get_model()
        transactions = [row[0] for row in model]
        date_range = (self.range_start, self.range_end)
        if self.charts_notebook:
            for chart in self.charts_notebook.charts:
                chart.update(transactions, date_range)
        self.update_page()

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

    def _get_child_iter(self, iterator):
        child_iter = self.transactions_tree.get_model().convert_iter_to_child_iter(iterator)
        return self.modelfilter.convert_iter_to_child_iter(child_iter)

    def on_toggle_uncategorized(self, button):
        self.b_show_uncategorized = button.get_active()
        self.update_ui()

    def on_toggle_transfer(self, button):
        self.b_show_transfer = button.get_active()
        self.update_ui()

    def on_search_entry_changed(self, editable):
        self.searchstring = editable.get_text().lower()
        self.update_ui()

    def on_edit_transaction(self, widget):
        transaction, iterator = self.get_selected_transaction()
        old_amount = transaction.amount
        dlg = edit_transaction_dialog.EditTransactionDialog(self.account, transaction, parent=self.widget.get_toplevel())
        b_change, transaction = dlg.start()
        if b_change:
            self.account.balance = self.account.balance - old_amount + transaction.amount
            child_iter = self._get_child_iter(iterator)
            self.model.remove(child_iter)
            self.insert_transaction(transaction)

    def on_remove_transaction(self, widget):
        trans, iterator = self.get_selected_transaction()
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

    def on_dividend_from_transaction(self, widget):
        trans, iterator = self.get_selected_transaction()
        dividend_dialog.DividendDialog(date=trans.date, price=trans.amount, parent=self.get_toplevel())

    def on_add_acc_transaction(self, widget):
        dlg = edit_transaction_dialog.EditTransactionDialog(self.account, parent=self.get_toplevel())
        dlg.start()

    def on_remove_transaction_category(self, widget):
        trans, iterator = self.get_selected_transaction()
        if trans.category:
            trans.category = None
            self.model[self._get_child_iter(iterator)][3] = ""

    def on_set_transaction_category(self, widget, category):
        trans, iterator = self.get_selected_transaction()
        if trans.category != category:
            trans.category = category
            self.model[self._get_child_iter(iterator)][3] = category.name


class AccountChartsNotebook(Gtk.Notebook):

    def __init__(self, account, date_range):
        Gtk.Notebook.__init__(self)
        self.account = account
        self.date_range = date_range
        self.charts = []
        self.set_property('tab_pos', Gtk.PositionType.LEFT)
        self.init_charts()

    def init_charts(self):
        if self.account.transactions:
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
