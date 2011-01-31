#!/usr/bin/env python

import gtk, datetime, pango
from avernus.gui import gui_utils, dialogs
from avernus.objects import controller
from avernus import pubsub
from avernus import config

import logging

logger = logging.getLogger(__name__)

class AccountTransactionTab(gtk.VBox):

    BORDER_WIDTH = 5

    def __init__(self, item):
        gtk.VBox.__init__(self)
        self.config = config.avernusConfig()

        hbox = gtk.HBox()
        uncategorized_button = gtk.ToggleButton(_('uncategorized'))
        hbox.pack_start(uncategorized_button, expand=False, fill=False)

        transfer_button = gtk.ToggleButton()
        image = gtk.Image()
        image.set_from_stock('gtk-convert', gtk.ICON_SIZE_BUTTON)
        transfer_button.add(image)
        hbox.pack_start(transfer_button, expand=False, fill=False)

        self.search_entry = gtk.Entry()
        hbox.pack_start(self.search_entry)
        self.search_entry.set_icon_from_stock(1, gtk.STOCK_CLEAR)
        self.search_entry.set_property('secondary-icon-tooltip-text', 'Clear search')
        self.search_entry.connect('icon-press', self.on_clear_search)
        self.start_entry = gtk.Entry()
        self.end_entry = gtk.Entry()
        self.pick_start = datetime.datetime(2000,1,1)
        self.pick_end = datetime.datetime.today()
        self.start_entry.set_icon_from_stock(1, gtk.STOCK_SELECT_COLOR)
        self.start_entry.set_property("secondary-icon-tooltip-text","Pick date")
        self.start_entry.connect('icon-press', self.on_pick_start)
        self.end_entry.set_icon_from_stock(1, gtk.STOCK_SELECT_COLOR)
        self.end_entry.set_property("secondary-icon-tooltip-text","Pick date")
        self.end_entry.connect('icon-press', self.on_pick_end)
        hbox.pack_start(gtk.Label(_('Start')), expand=False, fill=False)
        hbox.pack_start(self.start_entry, expand=False, fill=False)
        hbox.pack_start(gtk.Label(_('End')), expand=False, fill=False)
        hbox.pack_start(self.end_entry, expand=False, fill=False)
        
        self.pack_start(hbox, expand=False, fill=False)

        self.hpaned = gtk.HPaned()
        self.pack_start(self.hpaned)
        self.hpaned.set_border_width(self.BORDER_WIDTH)
        sw = gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        actiongroup = gtk.ActionGroup('transactions')
        self.transactions_tree = TransactionsTree(item, actiongroup, self.search_entry)
        actiongroup.add_actions([
                ('add',    gtk.STOCK_ADD,    'new transaction',    None, _('Add new transaction'), self.transactions_tree.on_add),
                ('edit' ,  gtk.STOCK_EDIT,   'edit transaction',   None, _('Edit selected transaction'),   self.transactions_tree.on_edit),
                ('remove', gtk.STOCK_DELETE, 'remove transaction', None, _('Remove selected transaction'), self.transactions_tree.on_remove),
                ('dividend', gtk.STOCK_CONVERT, 'dividend payment', None, _('Create dividend from transaction'), self.transactions_tree.on_dividend)
                                ])
        sw.add(self.transactions_tree)
        sw.connect_after('size-allocate',
                         gui_utils.resize_wrap,
                         self.transactions_tree,
                         self.transactions_tree.dynamicWrapColumn,
                         self.transactions_tree.dynamicWrapCell)
        frame = gtk.Frame()
        frame.add(sw)
        frame.set_shadow_type(gtk.SHADOW_IN)
        self.hpaned.pack1(frame, shrink=True, resize=True)
        
        status_bar = gtk.HBox()
        self.transactionsCountLabel = gtk.Label('n/a')
        status_bar.pack_start(self.transactionsCountLabel, expand=False, fill=False)
        status_bar.pack_start(gtk.Label(_('Transactions')), expand=False, fill=False)
        self.transactionsSumLabel = gtk.Label('n/a')
        status_bar.pack_start(gtk.Label(_('Sum: ')), expand=False, fill=False)
        status_bar.pack_start(self.transactionsSumLabel, expand=False, fill=False)
        self.pack_start(status_bar, expand=False, fill=False)

        uncategorized_button.connect('toggled', self.transactions_tree.on_toggle_uncategorized)
        transfer_button.connect('toggled', self.transactions_tree.on_toggle_transfer)
        self.update_range()
                
        vbox = gtk.VBox()
        frame = gtk.Frame()
        frame.add(vbox)
        frame.set_shadow_type(gtk.SHADOW_IN)
        self.hpaned.pack2(frame, shrink=False, resize=True)
        pos = self.config.get_option('account hpaned position', 'Gui') or 600
        self.hpaned.set_position(int(pos))

        sw = gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        actiongroup = gtk.ActionGroup('categories')
        self.category_tree = CategoriesTree(actiongroup)
        actiongroup.add_actions([
                ('add',    gtk.STOCK_ADD,    'new category',    None, _('Add new category'), self.category_tree.on_add),
                ('edit' ,  gtk.STOCK_EDIT,   'rename category',   None, _('Rename selected category'),   self.category_tree.on_edit),
                ('remove', gtk.STOCK_DELETE, 'remove category', None, _('Remove selected category'), self.category_tree.on_remove)
                                ])
        self.category_tree.on_unselect()
        sw.add(self.category_tree)
        vbox.pack_start(sw)
        toolbar = gtk.Toolbar()
        self.conditioned = ['remove', 'edit']

        for action in ['add', 'remove', 'edit']:
            button = actiongroup.get_action(action).create_tool_item()
            toolbar.insert(button, -1)
        vbox.pack_start(toolbar, expand=False, fill=False)
        self.connect("destroy", self.on_destroy)
        self.show_all()
        
    def on_pick_start(self, entry, icon_pos, event):
        self.__on_pick(True)
            
    def __on_pick(self, start=False):
        dialog = dialogs.CalendarDialog()
        if dialog.selected_date:
            if start:
                self.pick_start = dialog.selected_date
            else:
                self.pick_end = dialog.selected_date
            self.update_range()
            self.update_status_bar()
        
    def on_pick_end(self, entry, icon_pos, event):
        self.__on_pick()

    def on_clear_search(self, entry, icon_pos, event):
        self.search_entry.set_text('')
        
    def update_range(self):
        self.start_entry.set_text(self.pick_start.strftime('%d.%m.%y'))
        self.end_entry.set_text(self.pick_end.strftime('%d.%m.%y'))
        self.transactions_tree.range_start = self.pick_start
        self.transactions_tree.range_end = self.pick_end
        self.transactions_tree.modelfilter.refilter()
        
    def update_status_bar(self):
        self.transactionsCountLabel.set_text(str(len(self.transactions_tree.modelfilter)) + " ")
        self.transactionsSumLabel.set_text(str(self.transactions_tree.get_filtered_transaction_value()))

    def show(self):
        self.transactions_tree.clear()
        self.transactions_tree.load_transactions()
        self.category_tree.clear()
        self.category_tree.load_categories()
        self.update_status_bar()

    def on_destroy(self, widget):
        self.config.set_option('account hpaned position', self.hpaned.get_position(), 'Gui')

def desc_markup(column, cell, model, iter, user_data):
    text = model.get_value(iter, user_data)
    markup =  '<span size="small">'+ text + '</span>'
    cell.set_property('markup', markup)


class TransactionsTree(gui_utils.Tree):

    OBJECT = 0
    DESCRIPTION = 1
    AMOUNT = 2
    CATEGORY = 3
    DATE = 4
    ICON = 5

    def __init__(self, account, actiongroup, search_entry):
        self.account = account
        self.actiongroup = actiongroup
        self.searchstring = ''
        self.only_transfer = False
        self.only_uncategorized = False
        self.range_start = datetime.datetime.min
        self.range_end = datetime.datetime.max
        gui_utils.Tree.__init__(self)
        
        self.model = gtk.ListStore(object, str, float, str, object, str)
        self.modelfilter = self.model.filter_new()
        sorter = gtk.TreeModelSort(self.modelfilter)
        self.set_model(sorter)
        self.modelfilter.set_visible_func(self.visible_cb)
        self.create_icon_column('', self.ICON)
        self.create_column(_('Date'), self.DATE, func=gui_utils.date_to_string)
        sorter.set_sort_func(self.DATE, gui_utils.sort_by_time, self.DATE)
        col, cell = self.create_column(_('Description'), self.DESCRIPTION, func=desc_markup)
        self.dynamicWrapColumn = col
        self.dynamicWrapCell = cell
        cell.props.wrap_mode = pango.WRAP_WORD
        self.create_column(_('Amount'), self.AMOUNT, func=gui_utils.currency_format)
        self.create_column(_('Category'), self.CATEGORY)
        self.set_rules_hint(True)
        sorter.set_sort_column_id(self.DATE, gtk.SORT_DESCENDING)
        self.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.enable_model_drag_source(gtk.gdk.BUTTON1_MASK,
                                      [ ( 'text/plain', 0, 80 )],
                                      gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_MOVE)
        self.connect("drag-data-get", self.on_drag_data_get)
        self.connect('drag-end', self.on_drag_end)
        self.connect('button_press_event', self.on_button_press)
        self.connect('button_release_event', self.on_button_release)
        self.connect('key_press_event', self.on_key_press)
        search_entry.connect('changed', self.on_search_entry_changed)
        pubsub.subscribe('accountTransaction.created', self.on_transaction_created)
        
        self.reset_filter_dates()

    def visible_cb(self, model, iter):
        #transaction = model[iter][0]
        transaction = model[iter][0]
        if transaction and (
                self.searchstring in transaction.description.lower() \
                or self.searchstring in str(transaction.amount) \
                or (transaction.category and self.searchstring in transaction.category.name.lower())
                )\
                and (not self.only_transfer or transaction.is_transfer())\
                and (not self.only_uncategorized or not transaction.has_category()):
            if transaction.date >= self.range_start.date() and transaction.date <= self.range_end.date():
                return True
        return False

    def on_search_entry_changed(self, editable):
        self.searchstring = editable.get_text().lower()
        self.modelfilter.refilter()

    def on_transaction_created(self, transaction):
        if transaction.account == self.account:
            self.insert_transaction(transaction)

    def on_drag_data_get(self, treeview, context, selection, info, timestamp):
        treeselection = treeview.get_selection()
        model, paths = treeselection.get_selected_rows()
        iters = [model.get_iter(path) for path in paths]
        text = '\n'.join([str(model.get_value(iter, self.OBJECT).id) for iter in iters])
        selection.set('text/plain', 8, text)
        return

    def on_drag_end(self,widget, drag_context):
        treeselection = self.get_selection()
        model, paths = treeselection.get_selected_rows()
        iters = [model.get_iter(path) for path in paths]
        for iter in iters:
            trans = model.get_value(iter, self.OBJECT)
            model[iter] = self.get_item_to_insert(trans)

    def get_item_to_insert(self, ta):
        if ta.category:
            cat = ta.category.name
        else:
            cat = ''
        if ta.is_transfer():
            icon = 'gtk-convert'
        else:
            icon = ''
        return [ta, ta.description, ta.amount, cat, ta.date, icon]
    
    def get_filtered_transaction_value(self):
        sum = 0
        for row in self.modelfilter:
            sum += row[0].amount
        return sum

    def load_transactions(self):
        for ta in controller.getTransactionsForAccount(self.account):
            self.insert_transaction(ta)

    def insert_transaction(self, ta):
        self.model.append(self.get_item_to_insert(ta))

    def _get_selected_transaction(self):
        selection = self.get_selection()
        model, paths = selection.get_selected_rows()
        if len(paths) != 0:
            return model[paths[0]][self.OBJECT], model.get_iter(paths[0])
        return None, None

    def on_add(self, widget=None):
        dlg = EditTransaction(self.account)
        b_change, transaction = dlg.start()
        self.account.amount += transaction.amount
        self.insert_transaction(transaction)

    def on_edit(self, widget=None):
        transaction, iterator = self._get_selected_transaction()
        old_amount = transaction.amount
        dlg = EditTransaction(self.account, transaction)
        b_change, transaction = dlg.start()
        if b_change:
            self.account.amount = self.account.amount - old_amount + transaction.amount
            self.get_model()[iterator] = self.get_item_to_insert(transaction)

    def on_dividend(self, widget=None):
        trans, iterator = self._get_selected_transaction()
        dlg = dialogs.DividendDialog(date=trans.date, price=trans.amount)

    def on_remove(self, widget=None):
        trans, iterator = self._get_selected_transaction()
        dlg = gtk.MessageDialog(None,
                 gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION,
                    gtk.BUTTONS_OK_CANCEL, _("Permanently delete transaction?"))
        response = dlg.run()
        dlg.destroy()
        if response == gtk.RESPONSE_OK:
            trans.account.amount -= trans.amount
            trans.delete()
            child_iter = self._get_child_iter(iterator)
            self.model.remove(child_iter)

    def _get_child_iter(self, iterator):
        child_iter = self.get_model().convert_iter_to_child_iter(None, iterator)
        return self.modelfilter.convert_iter_to_child_iter(child_iter)

    def on_set_transaction_category(self, category = None):
        trans, iterator = self._get_selected_transaction()
        trans.category = category
        self.get_model()[iterator] = self.get_item_to_insert(trans)
        self.model[iterator] = self.get_item_to_insert(trans)

    def show_context_menu(self, event):
        trans, iter = self._get_selected_transaction()
        context_menu = gui_utils.ContextMenu()
        if trans:
            for action in self.actiongroup.list_actions():
                context_menu.add(action.create_menu_item())
            if trans.category:
                context_menu.add_item('Remove category', lambda widget: self.on_set_transaction_category())
            hierarchy = controller.getAllAccountCategoriesHierarchical()

            def insert_recursive(cat, menu):
                item = gtk.MenuItem(cat.name)
                menu.append(item)
                if cat in hierarchy:
                    new_menu = gtk.Menu()
                    item.set_submenu(new_menu)
                    item = gtk.MenuItem(cat.name)
                    new_menu.append(item)
                    item.connect('activate', lambda widget: self.on_set_transaction_category(cat))
                    new_menu.append(gtk.SeparatorMenuItem())
                    for child_cat in sorted(hierarchy[cat]):
                        insert_recursive(child_cat, new_menu)
                else:
                    item.connect('activate', lambda widget: self.on_set_transaction_category(cat))

            if len(hierarchy[None]) > 0:
                item = gtk.MenuItem("Move to category")
                context_menu.add(item)
                category_menu = gtk.Menu()
                item.set_submenu(category_menu)
                for cat in sorted(hierarchy[None]):
                    insert_recursive(cat, category_menu)
        else:
            context_menu.add(self.actiongroup.get_action('add').create_menu_item())
        context_menu.show(event)

    def on_key_press(self, widget, event):
        if gtk.gdk.keyval_name(event.keyval) == 'Delete':
            self.on_remove()
            return True
        return False

    def on_button_press(self, widget, event):
        if event.button == 3:
            self.show_context_menu(event)
        else:
            #edit on doubleclick
            #if event.type == gtk.gdk._2BUTTON_PRESS: # 'double click'
            #    self.on_edit()
            #    return
            # Here we intercept mouse clicks on selected items so that we can
            # drag multiple items without the click selecting only one
            target = self.get_path_at_pos(int(event.x), int(event.y))
            if (target
               and event.type == gtk.gdk.BUTTON_PRESS
               and not (event.state & (gtk.gdk.CONTROL_MASK|gtk.gdk.SHIFT_MASK))
               and self.get_selection().path_is_selected(target[0])):
                   # disable selection
                   self.get_selection().set_select_function(lambda *ignore: False)

    def on_button_release(self, widget, event):
        # re-enable selection
        self.get_selection().set_select_function(lambda *ignore: True)

    def on_toggle_uncategorized(self, button):
        if button.get_active():
            self.only_uncategorized=True
        else:
            self.only_uncategorized=False
        self.modelfilter.refilter()

    def on_toggle_transfer(self, button):
        if button.get_active():
            self.only_transfer=True
        else:
            self.only_transfer=False
        self.modelfilter.refilter()
        
    def on_toggle_date(self, button, start, end):
        if button.get_active():
            self.start_filter = start
            self.end_filter = end
        else:
            self.reset_filter_dates()
        self.modelfilter.refilter()
        
    def reset_filter_dates(self):
        self.start_filter = datetime.datetime(datetime.MINYEAR,1,1)
        self.end_filter = datetime.datetime.now()

    def clear(self):
        self.model.clear()
        


class CategoriesTree(gui_utils.Tree):

    TARGETS = [('MY_TREE_MODEL_ROW', gtk.TARGET_SAME_WIDGET, 0),
               ('text/plain', 0, 80)]

    def __init__(self, actiongroup):
        gui_utils.Tree.__init__(self)
        self.actiongroup = actiongroup
        self.set_model(gtk.TreeStore(object, str))
        col, self.cell = self.create_column(_('Categories'), 1)
        self.get_model().set_sort_column_id(1, gtk.SORT_ASCENDING)
        # setting the cell editable interfers with drag and drop
        #self.cell.set_property('editable', True)
        self.cell.connect('edited', self.on_cell_edited)
        self.enable_model_drag_dest(self.TARGETS, gtk.gdk.ACTION_DEFAULT)
        # Allow enable drag and drop of rows including row move
        self.enable_model_drag_source( gtk.gdk.BUTTON1_MASK,
                                self.TARGETS,
                                gtk.gdk.ACTION_DEFAULT|gtk.gdk.ACTION_MOVE)

        self.connect('drag_data_received', self.on_drag_data_received)
        self.connect('cursor_changed', self.on_cursor_changed)
        self.connect('button_press_event', self.on_button_press)
        self.connect('key_press_event', self.on_key_press)

    def load_categories(self):
        def insert_recursive(cat, parent):
            new_iter = model.append(parent, [cat, cat.name])
            if cat in hierarchy:
                for child_cat in hierarchy[cat]:
                    insert_recursive(child_cat, new_iter)
        model = self.get_model()
        hierarchy = controller.getAllAccountCategoriesHierarchical()
        for cat in hierarchy[None]: #start with root categories
            insert_recursive(cat, None)

    def insert_item(self, cat, parent=None):
        return self.get_model().append(parent, [cat, cat.name])

    def show_context_menu(self, event):
        category, iter = self.get_selected_item()
        if category:
            context_menu = gui_utils.ContextMenu()
            for action in self.actiongroup.list_actions():
                context_menu.add(action.create_menu_item())
            context_menu.show(event)

    def on_add(self, widget=None):
        parent, selection_iter = self.get_selected_item()
        item = controller.newAccountCategory('new category', parent=parent)
        iterator = self.insert_item(item, parent = selection_iter)
        model = self.get_model()
        if selection_iter:
            self.expand_row( model.get_path(selection_iter), True)
        self.cell.set_property('editable', True)
        self.set_cursor(model.get_path(iterator), focus_column = self.get_column(0), start_editing=True)

    def on_edit(self, widget=None):
        cat, selection_iter = self.get_selected_item()
        self.cell.set_property('editable', True)
        self.set_cursor(self.get_model().get_path(selection_iter), focus_column = self.get_column(0), start_editing=True)

    def on_remove(self, widget=None):
        obj, iterator = self.get_selected_item()
        if obj is None:
            return False
        dlg = gtk.MessageDialog(None,
             gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION,
             gtk.BUTTONS_OK_CANCEL)
        msg = _("Permanently delete category <b>")+obj.name+'</b>?'
        model = self.get_model()
        if model.iter_has_child(iterator):
                msg += _("\nWill also delete subcategories")
        dlg.set_markup(_(msg))
        response = dlg.run()
        dlg.destroy()
        if response == gtk.RESPONSE_OK:
            queue = [(iterator, obj)]

            removeQueue = []
            while len(queue) > 0:
                print queue
                currIter, currObj = queue.pop()
                #print "deleting from model ", currObj
                currObj.delete()
                if model.iter_has_child(currIter):
                    for i in range(0,model.iter_n_children(currIter)):
                        newIter = model.iter_nth_child(currIter, i)
                        queue.append((newIter, model[newIter][0]))
                removeQueue.insert(0,currIter)
            for toRemove in removeQueue:
                #print "removing from tree ", currIter
                model.remove(toRemove)
            self.on_unselect()

    def on_cell_edited(self, cellrenderertext, path, new_text):
        m = self.get_model()
        m[path][0].name = m[path][1] = unicode(new_text)
        cellrenderertext.set_property('editable', False)

    def on_button_press(self, widget, event):
        if event.button == 3:
            self.show_context_menu(event)

    def on_key_press(self, widget, event):
        if gtk.gdk.keyval_name(event.keyval) == 'Delete':
            self.on_remove()
            return True
        return False

    def on_cursor_changed(self, widget):
        cat, iterator = self.get_selected_item()
        if cat is not None:
            self.on_select(cat)
        else:
            self.on_unselect()

    def on_unselect(self):
        for action in ['remove', 'edit']:
            self.actiongroup.get_action(action).set_sensitive(False)

    def on_select(self, obj):
        for action in ['remove', 'edit']:
            self.actiongroup.get_action(action).set_sensitive(True)

    def _move_row(self, source, target, drop_position):
        model = self.get_model()
        source_row = model[source]
        source_category = source_row[0]
        if drop_position is None:
            new_iter = model.append(None, row=source_row)
            source_category.parent = None
        else:
            target_category = model[target][0]
            if drop_position == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE:
                new_iter = model.prepend(parent=target, row=source_row)
                source_category.parent = target_category
                self.expand_row(model.get_path(target), False)
            elif drop_position == gtk.TREE_VIEW_DROP_INTO_OR_AFTER:
                new_iter = model.append(parent=target, row=source_row)
                source_category.parent = target_category
                self.expand_row(model.get_path(target), False)
            elif drop_position == gtk.TREE_VIEW_DROP_BEFORE:
                new_iter = model.insert_before(
                    parent=None, sibling=target, row=source_row)
                source_category.parent = target_category.parent
            elif drop_position == gtk.TREE_VIEW_DROP_AFTER:
                new_iter = model.insert_after(
                    parent=None, sibling=target, row=source_row)
                source_category.parent = target_category.parent
        # Copy any children of the source row.
        for n in range(model.iter_n_children(source)):
            child = model.iter_nth_child(source, n)
            self._move_row(child, new_iter, gtk.TREE_VIEW_DROP_INTO_OR_BEFORE)
        # If the source row is expanded, expand the newly copied row
        if self.row_expanded(model.get_path(source)):
            self.expand_row(model.get_path(new_iter), False)

    def on_drag_data_received(self, widget, context, x, y, selection, target_type, etime):
        drop_info = self.get_dest_row_at_pos(x, y)
        if 'MY_TREE_MODEL_ROW' in context.targets:
            model, source_iter = self.get_selection().get_selected()
            if drop_info:
                target_path, drop_position = drop_info
                target_iter = model.get_iter(target_path)
                #dont allow dragging cats on themselves
                if not model[target_iter][0].is_parent(model[source_iter][0]):
                    self._move_row(source_iter, target_iter, drop_position)
                    context.finish(True, True, etime)
            else:
                self._move_row(source_iter, None, None)
                context.finish(True, True, etime)
        else: #drop from other widget
            if drop_info:
                model = self.get_model()
                path, position = drop_info
                target_iter = model.get_iter(path)
                cat = model[target_iter][0]
                for id in selection.data.split():
                    transaction = controller.AccountTransaction.getByPrimaryKey(int(id))
                    transaction.category = cat
            else:
                logger.debug("NO CATEGORY")
        return


class EditTransaction(gtk.Dialog):
    def __init__(self, account, transaction = None):
        gtk.Dialog.__init__(self, _("Edit transaction"), None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self.transaction = transaction
        vbox = self.get_content_area()

        if self.transaction is None:
            self.transaction = controller.newAccountTransaction(account=account)

        #description
        frame = gtk.Frame('Description')
        self.description_entry = gtk.TextView()
        self.description_entry.set_wrap_mode(gtk.WRAP_WORD)
        entry_buffer = self.description_entry.get_buffer()
        entry_buffer.set_text(self.transaction.description)
        frame.add(self.description_entry)
        vbox.pack_start(frame)

        #amount
        hbox = gtk.HBox()
        label = gtk.Label(_('Amount'))
        hbox.pack_start(label)
        self.amount_entry = gtk.SpinButton(gtk.Adjustment(lower=-999999999, upper=999999999, step_incr=10, value = self.transaction.amount), digits=2)
        hbox.pack_start(self.amount_entry)
        vbox.pack_start(hbox)

        #category
        hbox = gtk.HBox()
        label = gtk.Label(_('Category'))
        hbox.pack_start(label)
        treestore = gtk.TreeStore(object, str)
        self.combobox = gtk.ComboBox(treestore)
        cell = gtk.CellRendererText()
        self.combobox.pack_start(cell, True)
        self.combobox.add_attribute(cell, 'text', 1)

        def insert_recursive(cat, parent):
            new_iter = treestore.append(parent, [cat, cat.name])
            if cat == self.transaction.category:
                self.combobox.set_active_iter(new_iter)
            if cat in hierarchy:
                for child_cat in hierarchy[cat]:
                    insert_recursive(child_cat, new_iter)
        new_iter = treestore.append(None, [None, 'None'])
        self.combobox.set_active_iter(new_iter)
        hierarchy = controller.getAllAccountCategoriesHierarchical()
        for cat in hierarchy[None]: #start with root categories
            insert_recursive(cat, None)

        hbox.pack_start(self.combobox)
        vbox.pack_start(hbox)

        #date
        self.calendar = gtk.Calendar()
        self.calendar.select_month(self.transaction.date.month-1, self.transaction.date.year)
        self.calendar.select_day(self.transaction.date.day)
        vbox.pack_start(self.calendar)

        #transfer
        text = "Transfer: this transaction will not be shown in any of the graphs."
        self.transfer_button = gtk.CheckButton(text)
        if self.transaction.transfer:
            self.transfer_button.set_active(True)
        vbox.pack_start(self.transfer_button)

        self.matching_transactions_tree = gui_utils.Tree()
        model = gtk.ListStore(object, str, str, object)
        self.matching_transactions_tree.set_model(model)
        self.matching_transactions_tree.create_column(_('Account'), 1)
        col, cell = self.matching_transactions_tree.create_column(_('Description'), 2)
        cell.props.wrap_width = 200
        cell.props.wrap_mode = pango.WRAP_WORD
        self.matching_transactions_tree.create_column(_('Date'), 3, func=gui_utils.date_to_string)
        vbox.pack_end(self.matching_transactions_tree)
        self.no_matches_label = gtk.Label('No matching transactions found. Continue only if you want to mark this as a tranfer anyway.')
        vbox.pack_end(self.no_matches_label)

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
            for ta in controller.yield_matching_transfer_tranactions(self.transaction):
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
        treestore, selection_iter = selection.get_selected()
        if (selection_iter and treestore):
            self.transfer_transaction = treestore.get_value(selection_iter, 0)

    def process_result(self, response):
        if response == gtk.RESPONSE_ACCEPT:
            buffer = self.description_entry.get_buffer()
            self.transaction.description = unicode(buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter()))
            self.transaction.amount = self.amount_entry.get_value()
            year, month, day = self.calendar.get_date()
            self.transaction.date = datetime.date(year, month+1, day)
            iter = self.combobox.get_active_iter()
            if iter is None:
                self.transaction.category = None
            else:
                self.transaction.category = self.combobox.get_model()[self.combobox.get_active_iter()][0]
            if self.transfer_button.get_active():
                self.transaction.transfer = self.transfer_transaction
                self.transfer_transaction.transfer = self.transaction
            else:
                if self.transaction.transfer is not None:
                    self.transaction.transfer.transfer = None
                    self.transaction.transfer = None
        self.destroy()
        return response == gtk.RESPONSE_ACCEPT, self.transaction
