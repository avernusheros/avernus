#!/usr/bin/env python
from avernus.gui import get_ui_file, gui_utils, progress_manager
from avernus.gui.page import Page
from avernus.objects import account, container
from gi.repository import GObject, Gdk, Gtk, Pango


class Category(object):

    def __init__(self, name):
        self.name = name


class MainTreeBox(Gtk.VBox):

    def __init__(self):
        Gtk.VBox.__init__(self)

        self.main_tree = MainTree()
        sw = Gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', Gtk.PolicyType.NEVER)
        sw.set_property('vscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        sw.set_shadow_type(Gtk.ShadowType.IN)
        sw.add(self.main_tree)

        self.pack_start(sw, True, True, 0)
        vbox = Gtk.VBox()
        self.pack_start(vbox, False, False, 0)
        progress_manager.box = vbox

        info_box = InfoBox()
        self.main_tree.connect('select', info_box.on_maintree_select)
        self.pack_start(info_box, False, False, 0)


class InfoBox(Gtk.Table):

    def __init__(self):
        super(Gtk.Table, self).__init__()
        self.line_count = 0

        self.set_col_spacings(6)
        self.set_homogeneous(False)
        self.set_border_width(6)
        GObject.add_emission_hook(Page, "update", self.on_update_page)

    def add_line(self, label_text, info_text):
        if not isinstance(info_text, str):
            info_text = str(info_text)
        label = Gtk.Label()
        info = Gtk.Label()
        info.set_markup(info_text)
        label.set_justify(Gtk.Justification.RIGHT)
        info.set_justify(Gtk.Justification.LEFT)
        label.set_markup("<span font_weight=\"bold\">"
                         + label_text + ':' + "</span>")

        label.set_alignment(1, 0)
        info.set_alignment(0, 0)

        info.set_ellipsize(Pango.EllipsizeMode.END)
        info.set_selectable(True)

        self.attach(label, 0, 1, self.line_count, self.line_count + 1,
                     xoptions=Gtk.AttachOptions.FILL,
                     yoptions=Gtk.AttachOptions.FILL)
        self.attach(info, 1, 2, self.line_count, self.line_count + 1)

        self.line_count += 1

    def clear(self):
        for child in self:
            self.remove(child)
        self.line_count = 0

    def on_update_page(self, page, initiator):
        self.clear()
        for label, info in page.get_info():
            self.add_line(label, info)
        self.show_all()
        # returning False removes the hook
        return True

    def on_maintree_select(self, *args):
        self.clear()


class MainTree(gui_utils.Tree, GObject.GObject):

    __gsignals__ = {
        'select': (GObject.SIGNAL_RUN_FIRST, None,
                      (object,)),
        'unselect': (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    def __init__(self):
        super(gui_utils.Tree, self).__init__()
        actiongroup = Gtk.ActionGroup('left_pane')
        self.selected_item = None

        actiongroup.add_actions([
            ('add', Gtk.STOCK_ADD, _('New'), "plus", _('New'), self.on_add),
            ('edit', Gtk.STOCK_EDIT, _('Edit'), "F2", _('Edit'), self.on_edit),
            ('remove', Gtk.STOCK_DELETE, _('Remove'), 'Delete', _('Delete'),
                                        self.on_remove)
        ])

        self.uimanager = Gtk.UIManager()
        self.uimanager.insert_action_group(actiongroup)
        self.uimanager.add_ui_from_file(get_ui_file("left_pane_popup.ui"))

        self._init_widgets()
        self.insert_categories()
        self.connect_signals()
        self._load_items()

    def _load_items(self):
        portfolios = container.get_all_portfolios()
        if len(portfolios) > 1:
            all_pf = container.AllPortfolio()
            all_pf.name = "<i>%s</i>" % (_('All'),)
            self.insert_portfolio(all_pf)
        for pf in portfolios:
            self.insert_portfolio(pf)
        for wl in container.get_all_watchlists():
            self.insert_watchlist(wl)

        accounts = account.get_all_accounts()
        if len(accounts) > 1:
            all_account = account.AllAccount()
            all_account.name = "<i>%s</i>" % (_('All'),)
            self.insert_account(all_account)
        for acc in accounts:
            self.insert_account(acc)
        self.expand_all()

    def connect_signals(self):
        self.connect('button-press-event', self.on_button_press_event)
        self.connect('cursor_changed', self.on_cursor_changed)

    def _init_widgets(self):
        #object, icon, name
        self.set_model(Gtk.TreeStore(object, str, str, str, bool))

        column = Gtk.TreeViewColumn('')
        self.append_column(column)
        cell1 = Gtk.CellRendererPixbuf()
        cell2 = Gtk.CellRendererText()
        column.pack_start(cell1, False)
        column.pack_start(cell2, True)
        column.add_attribute(cell1, "icon_name", 1)
        column.add_attribute(cell2, "markup", 2)
        column.set_sort_column_id(2)
        column.set_expand(True)
        cell2.set_property('editable', True)
        cell2.set_property("ellipsize-set", True)
        cell2.set_property("ellipsize", Pango.EllipsizeMode.END)
        cell2.connect('edited', self.on_cell_edited)
        column.set_cell_data_func(cell1, self.cell_data_func)

        self.create_column('', 3)

        self.set_headers_visible(False)
        self.set_property("show-expanders", False)
        self.set_property("level-indentation", 10)

    def cell_data_func(self, column, cell, model, iterator, *args):
        cell.set_property('visible', model[iterator][4])

    def on_button_press_event(self, widget, event):
        target = self.get_path_at_pos(int(event.x), int(event.y))
        if target and event.type == Gdk.EventType.BUTTON_PRESS:
            obj = self.get_model()[target[0]][0]

            if event.button == 3:
                if isinstance(obj, Category):
                    popup = self.uimanager.get_widget("/CategoryPopup")
                else:
                    popup = self.uimanager.get_widget("/Popup")
                popup.popup(None, None, None, None, event.button, event.time)
                return True
            if self.get_selection().path_is_selected(target[0]) and obj.__class__.__name__ in ['Category', 'AllAccount', 'AllPortfolio']:
                #disable editing of categories
                return True

    def insert_categories(self):
        self.pf_iter = self.get_model().append(None, [Category('Portfolios'), None, "<b>" + _('Portfolios') + "</b>", '', False])
        self.wl_iter = self.get_model().append(None, [Category('Watchlists'), None, "<b>" + _('Watchlists') + "</b>", '', False])
        self.accounts_iter = self.get_model().append(None, [Category('Accounts'), None, "<b>" + _('Accounts') + "</b>", '', False])

    def insert_watchlist(self, item):
        return self.get_model().append(self.wl_iter, [item, 'watchlist', item.name, '', True])

    def insert_account(self, account):
        new_iter = self.get_model().append(self.accounts_iter, [account, 'account', account.name, gui_utils.get_currency_format_from_float(account.balance), True])
        account.connect("balance_changed", self.on_balance_changed, new_iter)
        return new_iter

    def insert_portfolio(self, item):
        new_iter = self.get_model().append(self.pf_iter,
                                          [item, 'portfolio',
                                           item.name,
                                           gui_utils.get_currency_format_from_float(item.get_current_value()),
                                            True])
        item.connect("position_added", self.on_container_value_changed, new_iter)
        item.connect("updated", self.on_container_updated, new_iter)
        return new_iter

    def on_remove(self, widget=None, data=None):
        if self.selected_item is None:
            return
        obj, iterator = self.selected_item
        if not isinstance(obj, Category):
            dlg = Gtk.MessageDialog(None,
                 Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.QUESTION,
                 Gtk.ButtonsType.OK_CANCEL)
            dlg.set_markup(_("Permanently delete") + " <b>" + obj.name + '</b>?')
            response = dlg.run()
            dlg.destroy()
            if response == Gtk.ResponseType.OK:
                obj.delete()
                self.get_model().remove(iterator)
                self.selected_item = None
                self.emit("unselect")

    def on_balance_changed(self, item, balance, iterator):
        self.get_model()[iterator][3] = gui_utils.get_currency_format_from_float(balance)

    def on_container_updated(self, item, iterator):
        self.get_model()[iterator][3] = gui_utils.get_currency_format_from_float(item.get_current_value())

    def on_container_value_changed(self, item, new_position, iterator):
        self.get_model()[iterator][3] = gui_utils.get_currency_format_from_float(item.get_current_value())

    def on_updated(self, item):
        obj, iterator = self.selected_item
        row = self.get_model()[iterator]
        if row:
            #row[1] = item
            row[2] = item.name
            row[3] = gui_utils.get_currency_format_from_float(item.balance)

    def on_cursor_changed(self, widget):
        #Get the current selection in the Gtk.TreeView
        selection = widget.get_selection()
        # Get the selection iter
        if selection:
            treestore, selection_iter = selection.get_selected()
            if (selection_iter and treestore):
                #Something is selected so get the object
                obj = treestore.get_value(selection_iter, 0)
                if self.selected_item is None or self.selected_item[0] != obj:
                    self.selected_item = obj, selection_iter
                    self.emit("select", obj)
                return
        self.selected_item = None
        self.emit("unselect")

    def on_edit(self, treeview=None, iter=None, path=None):
        if self.selected_item is None:
            return
        obj, row = self.selected_item
        #all portfolio and all account are not editable
        objtype = type(obj)
        if objtype == 'Category' or objtype == "AllPortfolio" or objtype == 'AllAccount':
            return
        if obj.__class__.__name__ == 'Account':
            from avernus.gui.account.edit_account_dialog import EditAccountDialog
            EditAccountDialog(obj, self)
            # set possible new name
            self.get_model()[row][2] = obj.name
        else:
            obj, selection_iter = self.selected_item
            self.set_cursor(path=self.get_model().get_path(selection_iter), column=self.get_column(0), start_editing=True)

    def on_cell_edited(self, cellrenderertext, path, new_text):
        m = self.get_model()
        m[path][0].name = m[path][2] = new_text

    def on_add(self, widget=None, data=None):
        obj, row = self.selected_item

        if obj.__class__.__name__ == 'Portfolio' or obj.__class__.__name__ == 'AllPortfolio' or obj.name == 'Portfolios':
            inserter = self.insert_portfolio
            item = container.Portfolio(name=_('new portfolio'))
        elif obj.__class__.__name__ == 'Watchlist' or obj.name == 'Watchlists':
            inserter = self.insert_watchlist
            item = container.Watchlist(name=_('new watchlist'))
        elif obj.__class__.__name__ == 'Account' or obj.__class__.__name__ == 'AllAccount' or obj.name == 'Accounts':
            inserter = self.insert_account
            item = account.Account(name=_('new account'), balance=0.0)
        iterator = inserter(item)
        self.set_cursor(path=self.get_model().get_path(iterator), column=self.get_column(0), start_editing=True)
