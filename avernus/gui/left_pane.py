#!/usr/bin/env python

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Pango
from avernus import pubsub
from avernus.gui import gui_utils, progress_manager
from avernus.gui.account.csv_import_dialog import CSVImportDialog
from avernus.controller import controller

from avernus.objects.container import AllPortfolio
from avernus.objects.account import AllAccount


class Category(object):
    __name__ = 'Category'
    id = -1
    def __init__(self, name):
        self.name = name


class MainTreeBox(Gtk.VBox):

    def __init__(self):
        super(Gtk.VBox, self).__init__()
        actiongroup = Gtk.ActionGroup('left_pane')

        main_tree = MainTree(actiongroup)
        self.pack_start(main_tree, True, True, 0)

        actiongroup.add_actions([
                ('add', Gtk.STOCK_ADD, 'new container', None, _('Add new portfolio or watchlist'), main_tree.on_add),
                ('edit' , Gtk.STOCK_EDIT, 'edit container', None, _('Edit selected portfolio or watchlist'), main_tree.on_edit),
                ('remove', Gtk.STOCK_DELETE, 'remove container', None, _('Delete selected portfolio or watchlist'), main_tree.on_remove)
                                ])

        main_tree_toolbar = Gtk.Toolbar()
        self.conditioned = ['remove', 'edit']

        for action in actiongroup.list_actions():
            button = action.create_tool_item()
            main_tree_toolbar.insert(button, -1)
        self.pack_start(main_tree_toolbar, False, False, 0)

        vbox = Gtk.VBox()
        self.pack_start(vbox, False, False, 0)
        progress_manager.box = vbox

        self.pack_start(InfoBox(), False, False, 0)


class InfoBox(Gtk.Table):

    def __init__(self):
        super(Gtk.Table, self).__init__()
        self.line_count = 0

        self.set_col_spacings(6)
        self.set_homogeneous(False)
        self.set_border_width(6)

        pubsub.subscribe('update_page', self.on_update_page)
        pubsub.subscribe('maintree.select', self.on_maintree_select)

    def add_line(self, label_text, info_text):
        if not isinstance(info_text, str):
            info_text = str(info_text)
        label = Gtk.Label()
        info = Gtk.Label()
        info.set_markup(info_text)
        label.set_justify(Gtk.Justification.RIGHT)
        info.set_justify(Gtk.Justification.LEFT)
        label.set_markup("<span font_weight=\"bold\">" + label_text + ':' + "</span>")

        label.set_alignment(1, 0);
        info.set_alignment(0, 0);

        info.set_ellipsize(Pango.EllipsizeMode.END)
        info.set_selectable(True)

        self.attach(label, 0, 1, self.line_count, self.line_count + 1, xoptions=Gtk.AttachOptions.FILL, yoptions=Gtk.AttachOptions.FILL)
        self.attach(info, 1, 2, self.line_count, self.line_count + 1)

        self.line_count += 1

    def clear(self):
        for child in self:
            self.remove(child)
        self.line_count = 0

    def on_update_page(self, page):
        self.clear()
        for label, info in page.get_info():
            self.add_line(label, info)
        self.show_all()

    def on_maintree_select(self, obj):
        self.clear()


class MainTree(gui_utils.Tree):

    def __init__(self, actiongroup):
        super(gui_utils.Tree, self).__init__()
        self.actiongroup = actiongroup
        self.selected_item = None

        self._init_widgets()
        self.insert_categories()
        self._subscribe()
        self._load_items()

    def _load_items(self):
        portfolios = controller.getAllPortfolio()
        if len(portfolios) > 1:
            all_pf = AllPortfolio()
            all_pf.controller = controller
            all_pf.name = "<i>%s</i>" % (_('All'),)
            self.insert_portfolio(all_pf)
        for pf in portfolios:
            self.insert_portfolio(pf)
        for wl in controller.getAllWatchlist():
            self.insert_watchlist(wl)

        accounts = controller.getAllAccount()
        if len(accounts) > 1:
            all_account = AllAccount()
            all_account.controller = controller
            all_account.name = "<i>%s</i>" % (_('All'),)
            self.insert_account(all_account)
        for account in accounts:
            self.insert_account(account)
        self.expand_all()

    def _subscribe(self):
        self.connect('button-press-event', self.on_button_press_event)
        self.connect('key-press-event', self.on_key_press)
        self.connect('cursor_changed', self.on_cursor_changed)
        self.subscriptions = (
                    ("container.edited", self.on_updated),
                    ('account.updated', self.on_item_updated),
                    ('container.updated', self.on_item_updated)
                )
        for topic, callback in self.subscriptions:
            pubsub.subscribe(topic, callback)

    def _init_widgets(self):
        #object, icon, name
        self.set_model(Gtk.TreeStore(object, str, str, str))
        self.set_headers_visible(False)
        col, cell = self.create_icon_text_column('', 1, 2)
        cell.set_property('editable', True)
        cell.connect('edited', self.on_cell_edited)
        self.create_column('', 3)

    def on_button_press_event(self, widget, event):
        target = self.get_path_at_pos(int(event.x), int(event.y))
        if target and event.type == Gdk.EventType.BUTTON_PRESS:
            obj = self.get_model()[target[0]][0]
            if event.button == 3 and not isinstance(obj, Category):
                self.popup = ContainerContextMenu(obj, self.actiongroup)
                self.popup.popup(None, None, None, None, event.button, event.time)
                return True
            elif self.get_selection().path_is_selected(target[0]) and obj.id == -1 :
                #disable editing of categories
                return True

    def on_key_press(self, widget, event):
        if Gdk.keyval_name(event.keyval) == 'Delete':
            self.on_remove()
            return True
        return False

    def insert_categories(self):
        self.pf_iter = self.get_model().append(None, [Category('Portfolios'), 'portfolios', _("<b>Portfolios</b>"), ''])
        self.wl_iter = self.get_model().append(None, [Category('Watchlists'), 'watchlists', _("<b>Watchlists</b>"), ''])
        self.accounts_iter = self.get_model().append(None, [Category('Accounts'), 'accounts', _("<b>Accounts</b>"), ''])
        #self.index_iter = self.get_model().append(None, [Category('Indices'),'indices', _("<b>Indices</b>"),''])

    def insert_watchlist(self, item):
        self.get_model().append(self.wl_iter, [item, 'watchlist', item.name, ''])

    def insert_account(self, item):
        self.get_model().append(self.accounts_iter, [item, 'account', item.name, gui_utils.get_currency_format_from_float(item.amount)])

    def insert_portfolio(self, item):
        self.get_model().append(self.pf_iter, [item, 'portfolio', item.name, gui_utils.get_currency_format_from_float(item.cvalue)])

    def on_remove(self, widget=None, data=None):
        if self.selected_item is None:
            return
        obj, iterator = self.selected_item
        if not isinstance(obj, Category):
            dlg = Gtk.MessageDialog(None,
                 Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.QUESTION,
                 Gtk.ButtonsType.OK_CANCEL)
            dlg.set_markup(_("Permanently delete <b>") + obj.name + '</b>?')
            response = dlg.run()
            dlg.destroy()
            if response == Gtk.ResponseType.OK:
                obj.delete()
                self.get_model().remove(iterator)
                self.selected_item = None
                pubsub.publish('maintree.unselect')

    def on_item_updated(self, item):
        row = self.find_item(item)
        if row:
            row[3] = gui_utils.get_currency_format_from_float(item.amount)

    def on_updated(self, item):
        obj, iter = self.selected_item
        row = self.get_model()[iter]
        if row:
            #row[1] = item
            row[2] = item.name
            row[3] = gui_utils.get_currency_format_from_float(item.amount)

    def on_cursor_changed(self, widget):
        #Get the current selection in the Gtk.TreeView
        selection = widget.get_selection()
        # Get the selection iter
        treestore, selection_iter = selection.get_selected()
        if (selection_iter and treestore):
            #Something is selected so get the object
            obj = treestore.get_value(selection_iter, 0)
            if self.selected_item is None or self.selected_item[0] != obj:
                self.selected_item = obj, selection_iter
                self.on_select(obj)
                pubsub.publish('maintree.select', obj)
            return
        self.selected_item = None
        pubsub.publish('maintree.unselect')
        self.on_unselect()

    def on_unselect(self):
        for action in ['remove', 'edit']:
            self.actiongroup.get_action(action).set_sensitive(False)

    def on_select(self, obj):
        if isinstance(obj, Category):
            self.on_unselect()
        else:
            for action in ['remove', 'edit']:
                self.actiongroup.get_action(action).set_sensitive(True)

    def on_edit(self, treeview=None, iter=None, path=None):
        if self.selected_item is None:
            return
        obj, row = self.selected_item
        #all portfolio and all account are not editable
        if obj.id == -1:
            return
        parent = self.get_parent().get_parent().get_parent().get_parent()
        if obj.__name__ == 'Portfolio':
            EditPortfolio(obj, parent)
        elif obj.__name__ == 'Watchlist':
            EditWatchlist(obj, parent)
        elif obj.__name__ == 'Account':
            EditAccount(obj, parent)

    def on_cell_edited(self, cellrenderertext, path, new_text):
        m = self.get_model()
        m[path][0].name = m[path][2] = new_text

    def on_add(self, widget=None, data=None):
        #FIXME sehr unschoen
        obj, row = self.selected_item
        model = self.get_model()
        if isinstance(obj, Category):
            if obj.name == 'Portfolios':
                cat_type = 'portfolio'
            elif obj.name == 'Watchlists':
                cat_type = 'watchlist'
            elif obj.name == 'Accounts':
                cat_type = 'account'
        else:
            if obj.__name__ == 'Portfolio':
                cat_type = 'portfolio'
            elif obj.__name__ == 'Watchlist':
                cat_type = 'watchlist'
            elif obj.__name__ == 'Account':
                cat_type = 'account'
        if cat_type == 'portfolio':
            parent_iter = self.pf_iter
            item = controller.newPortfolio('new ' + cat_type)
        elif cat_type == 'watchlist':
            parent_iter = self.wl_iter
            item = controller.newWatchlist('new ' + cat_type)
        elif cat_type == 'account':
            parent_iter = self.accounts_iter
            item = controller.newAccount('new ' + cat_type)
        iterator = model.append(parent_iter, [item, cat_type, item.name, ''])
        self.expand_row(model.get_path(parent_iter), True)
        self.set_cursor(model.get_path(iterator), focus_column=self.get_column(0), start_editing=True)


class EditWatchlist(Gtk.Dialog):

    def __init__(self, wl, parent=None):
        Gtk.Dialog.__init__(self, _("Edit watchlist - ") + wl.name, parent
                            , Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                     (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                      Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        self.wl = wl
        vbox = self.get_content_area()

        #name entry
        hbox = Gtk.HBox()
        vbox.pack_start(hbox, True, True, 0)
        label = Gtk.Label(label=_('Name:'))
        hbox.pack_start(label, True, True, 0)
        self.name_entry = Gtk.Entry()
        self.name_entry.set_text(wl.name)
        hbox.pack_start(self.name_entry, True, True, 0)

        self.show_all()
        self.name_entry.connect("activate", self.process_result)
        response = self.run()
        self.process_result(response=response)

    def process_result(self, widget=None, response=Gtk.ResponseType.ACCEPT):
        if response == Gtk.ResponseType.ACCEPT:
            self.wl.name = self.name_entry.get_text()
            pubsub.publish("container.edited", self.wl)
        self.destroy()


class EditAccount(Gtk.Dialog):

    def __init__(self, acc, parent=None):
        Gtk.Dialog.__init__(self, _("Edit watchlist - ") + acc.name, parent
                            , Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                     (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                      Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        self.acc = acc
        vbox = self.get_content_area()
        table = Gtk.Table()
        vbox.pack_start(table, True, True, 0)

        label = Gtk.Label(label=_("Name:"))
        table.attach(label, 0, 1, 0, 1)
        self.name_entry = Gtk.Entry()
        self.name_entry.set_text(acc.name)
        table.attach(self.name_entry, 1, 2, 0, 1)

        #cash entry
        label = Gtk.Label(label=_('Current balance:'))
        table.attach(label, 0, 1, 1, 2)
        self.cash_entry = Gtk.SpinButton(adjustment=Gtk.Adjustment(lower= -999999999, upper=999999999, step_increment=10, value=acc.amount), digits=2)
        table.attach(self.cash_entry, 1, 2, 1, 2)

        self.show_all()

        self.name_entry.connect("activate", self.process_result)
        response = self.run()
        self.process_result(response=response)

    def process_result(self, widget=None, response=Gtk.ResponseType.ACCEPT):
        if response == Gtk.ResponseType.ACCEPT:
            self.acc.name = self.name_entry.get_text()
            self.acc.amount = self.cash_entry.get_value()
        self.destroy()


class EditPortfolio(Gtk.Dialog):

    def __init__(self, pf, parent=None):
        Gtk.Dialog.__init__(self, _("Edit watchlist - ") + pf.name, parent
                            , Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                     (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                      Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))

        self.pf = pf
        vbox = self.get_content_area()
        table = Gtk.Table()
        vbox.pack_start(table, True, True, 0)

        #name entry
        label = Gtk.Label(label=_('Name:'))
        table.attach(label, 0, 1, 0, 1)
        self.name_entry = Gtk.Entry()
        self.name_entry.set_text(pf.name)
        table.attach(self.name_entry, 1, 2, 0, 1)

        self.show_all()
        self.name_entry.connect("activate", self.process_result)
        response = self.run()
        self.process_result(response=response)

    def process_result(self, widget=None, response=Gtk.ResponseType.ACCEPT):
        if response == Gtk.ResponseType.ACCEPT:
            self.pf.name = self.name_entry.get_text()
            self.pf.cash = self.cash_entry.get_value()
            pubsub.publish("container.edited", self.pf)
        self.destroy()


class ContainerContextMenu(gui_utils.ContextMenu):

    def __init__(self, container, actiongroup):
        gui_utils.ContextMenu.__init__(self)

        for action in ['edit', 'remove']:
            self.append(actiongroup.get_action(action).create_menu_item())

        if container.__name__ == 'Account':
            self.append(Gtk.SeparatorMenuItem())
            self.add_item(_('Import transactions'), lambda x: CSVImportDialog(account=container) , 'gtk-add')
