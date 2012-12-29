#!/usr/bin/env python
from avernus.controller import datasource_controller
from avernus.gui import gui_utils, threads, common_dialogs
from avernus.gui.portfolio import dialogs
from avernus.objects import asset, position, portfolio_transaction
from gi.repository import Gtk
import datetime
import logging


logger = logging.getLogger(__name__)


class PositionDialog(Gtk.Dialog):

    WIDTH = 600
    HEIGHT = 400

    def __init__(self, pos, parent=None):
        Gtk.Dialog.__init__(self, _("Edit position - ") + pos.asset.name, parent
                            , Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                     (Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        vbox = self.get_content_area()
        notebook = Gtk.Notebook()
        vbox.pack_start(notebook, True, True, 0)
        self.position_table = EditPositionTable(pos)
        self.quotation_table = QuotationTable(pos.asset)
        if isinstance(pos, position.PortfolioPosition):
            transactions_table = TransactionsTab(pos)
            notebook.append_page(transactions_table, Gtk.Label(label=_('Transactions')))
        self.asset_table = dialogs.EditAssetTable(pos.asset, self)
        notebook.append_page(self.position_table, Gtk.Label(label=_('Position')))
        notebook.append_page(self.asset_table, Gtk.Label(label=_('Asset')))
        notebook.append_page(self.quotation_table, Gtk.Label(label=_('Quotations')))

        self.previous_page = 0

        self.set_size_request(self.WIDTH, self.HEIGHT)
        self.show_all()
        notebook.connect("switch-page", self.on_switch_page)
        self.run()
        self.process_result()

    def on_switch_page(self, notebook, page, page_num):
        # previous was the position tab
        if self.previous_page == 0:
            self.position_table.process_result()
        self.previous_page = page_num

    def process_result(self, widget=None):
        self.position_table.process_result()
        self.asset_table.process_result()
        self.destroy()


class QuotationTable(Gtk.Table):

    def __init__(self, asset):
        Gtk.Table.__init__(self)
        self.asset = asset

        self.attach(Gtk.Label(label=_('First quotation')), 0, 1, 0, 1, yoptions=Gtk.AttachOptions.FILL)
        self.first_label = Gtk.Label()
        self.attach(self.first_label, 1, 2, 0, 1, yoptions=Gtk.AttachOptions.FILL)
        self.attach(Gtk.Label(label=_('Last quotation')), 0, 1, 1, 2, yoptions=Gtk.AttachOptions.FILL)
        self.last_label = Gtk.Label()
        self.attach(self.last_label, 1, 2, 1, 2, yoptions=Gtk.AttachOptions.FILL)
        self.attach(Gtk.Label(label=_('# quotations')), 0, 1, 2, 3, yoptions=Gtk.AttachOptions.FILL)
        self.count_label = Gtk.Label()
        self.attach(self.count_label, 1, 2, 2, 3, yoptions=Gtk.AttachOptions.FILL)

        button = Gtk.Button(_('Get quotations'))
        button.connect('clicked', self.on_get_button_clicked)
        self.attach(button, 0, 2, 4, 5, yoptions=Gtk.AttachOptions.FILL)

        button = Gtk.Button(_('Delete quotations'))
        button.connect('clicked', self.on_delete_button_clicked)
        self.attach(button, 0, 2, 5, 6, yoptions=Gtk.AttachOptions.FILL)

        button = Gtk.Button(_('Edit quotations'))
        button.connect('clicked', self.on_edit_button_clicked)
        self.attach(button, 0, 2, 6, 7, yoptions=Gtk.AttachOptions.FILL)

        self.update_labels()

    def on_edit_button_clicked(self, button):
        EditHistoricalQuotationsDialog(self.asset, parent=self.get_toplevel())
        self.update_labels()

    def on_delete_button_clicked(self, button):
        self.asset.delete_quotations()
        self.update_labels()

    def on_get_button_clicked(self, button):
        threads.GeneratorTask(datasource_controller.get_historical_prices, self.new_quotation_callback, complete_callback=self.update_labels, args=self.asset).start()

    def new_quotation_callback(self, qt):
        self.count += 1
        self.count_label.set_text(str(self.count))

    def update_labels(self):
        quotations = self.asset.quotations
        self.count = len(quotations)
        self.count_label.set_text(str(self.count))
        if self.count == 0:
            self.first_label.set_text('n/a')
            self.last_label.set_text('n/a')
        else:
            self.first_label.set_text(gui_utils.get_date_string(quotations[0].date))
            self.last_label.set_text(gui_utils.get_date_string(quotations[-1].date))


class TransactionsTab(Gtk.VBox):
    COL_DATE = 2
    COL_PRICE = 4
    COL_TOTAL = 6

    def __init__(self, pos):
        self.position = pos
        Gtk.VBox.__init__(self)

        # init wigets
        self.tree = gui_utils.Tree()
        sw = Gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        sw.set_property('vscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        self.pack_start(sw, True, True, 0)
        sw.add(self.tree)
        toolbar = Gtk.Toolbar()
        self.pack_start(toolbar, False, True, 0)

        # init tree
        self.model = Gtk.ListStore(object, str, object, float, float, float, float)
        self.tree.set_model(self.model)

        self.date_column, cell = self.tree.create_column(_('Date'), self.COL_DATE, func=gui_utils.date_to_string)
        self.tree.connect("row-activated", self.on_row_activated)
        self.model.set_sort_func(self.COL_DATE, gui_utils.sort_by_datetime, self.COL_DATE)
        self.tree.create_column(_('Type'), 1)

        cell = Gtk.CellRendererSpin()
        adjustment = Gtk.Adjustment(0.00, 0, 9999999, 0.01, 10, 0)
        cell.set_property("digits", 3)
        cell.set_property("editable", True)
        cell.set_property("adjustment", adjustment)
        cell.connect("edited", self.on_shares_edited, 3)
        self.shares_column = Gtk.TreeViewColumn(_('Shares'), cell, text=3)
        self.shares_column.set_cell_data_func(cell, gui_utils.float_format, 3)
        self.shares_column.set_resizable(True)
        self.tree.append_column(self.shares_column)

        cell = Gtk.CellRendererSpin()
        cell.set_property("digits", 2)
        self.price_column = Gtk.TreeViewColumn(_('Price'), cell, text=4)
        self.price_column.set_resizable(True)
        self.price_column.set_cell_data_func(cell, gui_utils.currency_format, 4)
        self.tree.append_column(self.price_column)

        cell = Gtk.CellRendererSpin()
        adjustment = Gtk.Adjustment(0.00, 0, 9999999, 0.01, 10, 0)
        cell.set_property("digits", 2)
        cell.set_property("editable", True)
        cell.set_property("adjustment", adjustment)
        cell.connect("edited", self.on_costs_edited, 5)
        self.costs_column = Gtk.TreeViewColumn(_('Transaction Costs'), cell, text=5)
        self.costs_column.set_resizable(True)
        self.costs_column.set_cell_data_func(cell, gui_utils.currency_format, 5)
        self.tree.append_column(self.costs_column)

        # total
        cell = Gtk.CellRendererSpin()
        adjustment = Gtk.Adjustment(0.00, 0, 9999999, 0.01, 10, 0)
        cell.set_property("digits", 2)
        cell.set_property("editable", True)
        cell.set_property("adjustment", adjustment)
        cell.connect("edited", self.on_total_edited, 6)
        self.total_column = Gtk.TreeViewColumn(_('Total'), cell, text=6)
        self.total_column.set_resizable(True)
        self.total_column.set_cell_data_func(cell, gui_utils.currency_format, 6)
        self.tree.append_column(self.total_column)

        self.tree.set_model(self.model)
        self.tree.get_model().set_sort_column_id(self.COL_DATE, Gtk.SortType.ASCENDING)

        # init toolbar
        actiongroup = Gtk.ActionGroup('transactionstab')
        actiongroup.add_actions([
                ('add', Gtk.STOCK_ADD, 'new quotation', None, _('Add new quotation'), self.on_add),
                ('remove', Gtk.STOCK_DELETE, 'remove quotation', None, _('Remove selected quotation'), self.on_remove)
            ])
        for action in actiongroup.list_actions():
            toolbar.insert(action.create_tool_item(), -1)

        # load values
        for ta in pos.transactions:
            self.insert_transaction(ta)

    def insert_transaction(self, ta):
        return self.model.append(
                [ta,
                str(ta),
                ta.date,
                ta.quantity,
                ta.price_per_share,
                ta.cost,
                ta.total
                ])

    def on_row_activated(self, treeview, path, view_column):
        if view_column == self.date_column:
            transaction = self.model[path][0]
            dlg = common_dialogs.CalendarDialog(transaction.date, parent=self.get_toplevel())
            if dlg.date:
                # be carefull, transactions have datetimes...
                transaction.date = transaction.date.replace(dlg.date.year, dlg.date.month, dlg.date.day)
                transaction.position.date = transaction.date
                self.model[path][self.COL_DATE] = transaction.date
                self.tree.scroll_to_cell(path)

    def on_add(self, button):
        last_transaction = list(self.position.transactions)[-1]
        transaction = portfolio_transaction.BuyTransaction(
                    date=datetime.date.today(),
                    quantity=last_transaction.quantity,
                    price=last_transaction.price,
                    cost=last_transaction.cost,
                    position=self.position)
        iterator = self.insert_transaction(transaction)
        self.tree.scroll_to_cell(self.model.get_path(iterator))

    def on_remove(self, button):
        selection = self.tree.get_selection()
        model, selection_iter = selection.get_selected()
        if selection_iter:
            dlg = Gtk.MessageDialog(None,
                     Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.QUESTION,
                     Gtk.ButtonsType.OK_CANCEL)
            dlg.set_markup(_("Permanently delete selected transaction?"))
            response = dlg.run()
            dlg.destroy()
            if response == Gtk.ResponseType.OK:
                # update position
                ta = model[selection_iter][0]
                ta.position.recalculate()
                # delete
                ta.delete()
                model.remove(selection_iter)

    def on_shares_edited(self, cellrenderertext, path, new_text, columnnumber):
        try:
            value = float(new_text.replace(",", "."))
            self.model[path][columnnumber] = value
            self.model[path][0].quantity = value
        except:
            logger.debug("entered value is not a float", new_text)

    def on_total_edited(self, cellrenderertext, path, new_text, columnnumber):
        try:
            value = float(new_text.replace(",", "."))
            ta = self.model[path][0]
            if ta.type == 'portfolio_sell_transaction':
                ta.price = value + ta.cost
            else:
                ta.price = abs(value) - ta.cost
            # update gui
            self.model[path][columnnumber] = value
            self.model[path][self.COL_PRICE] = ta.price_per_share
        except:
            logger.debug("entered value is not a float", new_text)

    def on_costs_edited(self, cellrenderertext, path, new_text, columnnumber):
        try:
            value = float(new_text.replace(",", "."))
            ta = self.model[path][0]
            ta.cost = value
            # update gui
            self.model[path][columnnumber] = value
            self.model[path][self.COL_PRICE] = ta.price_per_share
        except:
            logger.debug("entered value is not a float", new_text)


class EditHistoricalQuotationsDialog(Gtk.Dialog):

    def __init__(self, asset, parent=None):
        self.asset = asset

        Gtk.Dialog.__init__(self, _("Quotations") + " - " + asset.name, parent
                            , Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                     (Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        self.set_default_size(300, 300)

        # init wigets
        vbox = self.get_content_area()
        self.tree = gui_utils.Tree()
        sw = Gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        sw.set_property('vscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        vbox.pack_start(sw, True, True, 0)
        sw.add(self.tree)
        toolbar = Gtk.Toolbar()
        vbox.pack_start(toolbar, False, True, 0)

        # init tree
        self.model = Gtk.ListStore(object, object, float)
        self.tree.set_model(self.model)
        self.date_column, cell = self.tree.create_column(_('Date'), 1, func=gui_utils.date_to_string)
        self.tree.connect("row-activated", self.on_row_activated)

        cell = Gtk.CellRendererSpin()
        adjustment = Gtk.Adjustment(0.00, 0, 9999999, 0.01, 10, 0)
        cell.set_property("editable", True)
        cell.set_property("digits", 2)
        cell.set_property("adjustment", adjustment)
        cell.connect("edited", self.on_cell_edited)
        self.price_column = Gtk.TreeViewColumn(_('Price (close)'), cell, text=2)
        self.price_column.set_cell_data_func(cell, gui_utils.float_format, 2)
        self.tree.append_column(self.price_column)

        # init toolbar
        actiongroup = Gtk.ActionGroup('quotations')
        actiongroup.add_actions([
                ('add', Gtk.STOCK_ADD, 'new quotation', None, _('Add new quotation'), self.on_add),
                ('remove', Gtk.STOCK_DELETE, 'remove quotation', None, _('Remove selected quotation'), self.on_remove)
            ])
        for action in actiongroup.list_actions():
            toolbar.insert(action.create_tool_item(), -1)

        # load values
        for quotation in self.asset.quotations:
            self.model.append([quotation, quotation.date, quotation.close])

        # show dialog
        self.show_all()
        self.run()
        self.destroy()

    def on_row_activated(self, treeview, path, view_column):
        if view_column == self.date_column:
            quotation = self.model[path][0]
            dlg = common_dialogs.CalendarDialog(quotation.date, parent=self.get_toplevel())
            if dlg.date:
                quotation.date = self.model[path][1] = dlg.date

    def on_add(self, button):
        quotation = asset.Quotation(date=datetime.date.today(),
                                    asset=self.asset)
        iterator = self.model.append([quotation,
                                      quotation.date, quotation.close])
        path = self.model.get_path(iterator)
        self.tree.set_cursor(path, focus_column=self.price_column,
                             start_editing=True)

    def on_remove(self, button):
        selection = self.tree.get_selection()
        model, selection_iter = selection.get_selected()
        if selection_iter:
            model[selection_iter][0].delete()
            model.remove(selection_iter)

    def on_cell_edited(self, cellrenderertext, path, new_text):
        try:
            value = float(new_text.replace(",", "."))
            self.model[path][2] = self.model[path][0].close = value
        except:
            logger.debug("entered value is not a float", new_text)


class EditPositionTable(Gtk.Table):

    def __init__(self, pos):
        Gtk.Table.__init__(self)
        self.pos = pos

        self.attach(Gtk.Label(label=_('Shares')), 0, 1, 0, 1)
        adjustment = Gtk.Adjustment(lower=0, upper=100000, step_increment=1.0)
        self.shares_entry = Gtk.SpinButton(adjustment=adjustment, digits=2)
        self.attach(self.shares_entry, 1, 2, 0, 1)

        self.attach(Gtk.Label(label=_('Buy price')), 0, 1, 1, 2)
        adjustment = Gtk.Adjustment(lower=0, upper=100000, step_increment=0.1)
        self.price_entry = Gtk.SpinButton(adjustment=adjustment, digits=2)
        self.attach(self.price_entry, 1, 2, 1, 2)

        self.attach(Gtk.Label(label=_('Buy date')), 0, 1, 2, 3)
        self.calendar = Gtk.Calendar()

        self.attach(self.calendar, 1, 2, 2, 3)
        self.attach(Gtk.Label(label=_('Comment')), 0, 1, 3, 4)

        self.comment_entry = Gtk.TextView()
        self.comment_entry.set_wrap_mode(Gtk.WrapMode.WORD)
        self.comment_entry.set_size_request(50, 80)
        self.attach(self.comment_entry, 1, 2, 3, 4)

        self.update_values()

    def update_values(self, *args):
        self.price_entry.set_value(self.pos.price)
        self.shares_entry.set_value(self.pos.quantity)
        self.calendar.select_month(self.pos.date.month - 1, self.pos.date.year)
        self.calendar.select_day(self.pos.date.day)
        entry_buffer = self.comment_entry.get_buffer()
        entry_buffer.set_text(self.pos.comment)

    def process_result(self, widget=None):
        self.pos.quantity = self.shares_entry.get_value()
        self.pos.price = self.price_entry.get_value()
        year, month, day = self.calendar.get_date()
        self.pos.date = datetime.datetime(year, month + 1, day)
        b = self.comment_entry.get_buffer()
        self.pos.comment = unicode(b.get_text(b.get_start_iter(), b.get_end_iter(), True))
        if hasattr(self.pos, "buy_transaction"):
            ta = self.pos.buy_transaction
            if ta:
                ta.quantity = self.pos.quantity
                ta.price = self.pos.price
                ta.date = self.pos.date
