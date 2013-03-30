#!/usr/bin/env python
from avernus.gui import gui_utils, progress_manager, get_avernus_builder
from avernus.gui.page import Page
from avernus.objects import account, container
from gi.repository import GObject, Gtk, Pango


class Sidebar(GObject.GObject):

    __gsignals__ = {
        'select': (GObject.SIGNAL_RUN_FIRST, None,
                      (object,)),
        'unselect': (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    def __init__(self):
        GObject.GObject.__init__(self)
        self.builder = get_avernus_builder()
        self.tree = self.builder.get_object("sidebar_tree")
        column = self.builder.get_object("sidebar_column1")
        # I don't know how to do this in glade
        column.set_expand(True)
        self.infobox = InfoBox(self.builder.get_object("infobox"))
        progress_manager.box = self.builder.get_object("progress_box")

        self.selected_item = None

        self.insert_categories()
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
        self.tree.expand_all()

    def on_sidebar_button_press(self, widget, event):
        if event.button == 3:
            if isinstance(self.selected_item[0], str):
                popup = self.builder.get_object("sidebar_category_contextmenu")
            else:
                popup = self.builder.get_object("sidebar_contextmenu")
            popup.popup(None, None, None, None, event.button, event.time)
            return True

    def insert_categories(self):
        model = self.tree.get_model()
        self.pf_iter = model.append(None,
                                    ['Category Portfolios',
                                      None,
                                     "<b>" + _('Portfolios') + "</b>",
                                      '',
                                     False, False])
        self.wl_iter = model.append(None, ['Category Watchlists',
                                            None,
                                           "<b>" + _('Watchlists') + "</b>",
                                            '',
                                             False, False])
        self.accounts_iter = model.append(None, ['Category Accounts', None,
                                     "<b>" + _('Accounts') + "</b>", '',
                                      False, False])
        self.report_iter = model.append(None, ['Category Reports', None,
                                     "<b>" + _('Reports') + "</b>", '',
                                      False, False])

    def insert_report(self, key, name):
        return self.tree.get_model().append(self.report_iter, [key, 'report', name, '', False, False])

    def insert_watchlist(self, item):
        return self.tree.get_model().append(self.wl_iter, [item, 'watchlist', item.name, '', True, True])

    def insert_account(self, account):
        new_iter = self.tree.get_model().append(self.accounts_iter, [account, 'account', account.name, gui_utils.get_currency_format_from_float(account.balance), True, True])
        account.connect("balance_changed", self.on_balance_changed, new_iter)
        return new_iter

    def insert_portfolio(self, item):
        new_iter = self.tree.get_model().append(self.pf_iter,
                                        [item, 'portfolio',
                                         item.name,
                                         gui_utils.get_currency_format_from_float(item.get_current_value()),
                                         True,
                                         True])
        item.connect("positions_changed", self.on_container_updated, new_iter)
        item.connect("updated", self.on_container_updated, new_iter)
        return new_iter

    def on_sidebar_remove(self, widget):
        if self.selected_item is None:
            return
        obj, iterator = self.selected_item
        if not isinstance(obj, str):
            dlg = Gtk.MessageDialog(None,
                 Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.QUESTION,
                 Gtk.ButtonsType.OK_CANCEL)
            dlg.set_markup(_("Permanently delete") + " <b>" + obj.name + '</b>?')
            response = dlg.run()
            dlg.destroy()
            if response == Gtk.ResponseType.OK:
                obj.delete()
                self.tree.get_model().remove(iterator)
                self.selected_item = None
                self.emit("unselect")

    def on_balance_changed(self, item, balance, iterator):
        self.tree.get_model()[iterator][3] = gui_utils.get_currency_format_from_float(balance)

    def on_container_updated(self, item, iterator):
        self.tree.get_model()[iterator][3] = gui_utils.get_currency_format_from_float(item.get_current_value())

    def on_updated(self, item):
        iterator = self.selected_item[1]
        row = self.tree.get_model()[iterator]
        if row:
            # row[1] = item
            row[2] = item.name
            row[3] = gui_utils.get_currency_format_from_float(item.balance)

    def on_sidebar_cursor_changed(self, treeview):
        # Get the current selection in the Gtk.TreeView
        selection = treeview.get_selection()
        # Get the selection iter
        if selection:
            treestore, selection_iter = selection.get_selected()
            if (selection_iter and treestore):
                # Something is selected so get the object
                obj = treestore.get_value(selection_iter, 0)
                if not self.selected_item or self.selected_item[0] != obj:
                    self.selected_item = obj, selection_iter
                    self.infobox.on_maintree_select()
                    self.emit("select", obj)
                return
        self.selected_item = None
        self.emit("unselect")

    def on_sidebar_edit(self, treeview):
        if self.selected_item is None:
            return
        obj, row = self.selected_item
        # all portfolio and all account are not editable
        objtype = type(obj)
        if objtype == 'Category' or objtype == "AllPortfolio" or objtype == 'AllAccount':
            return
        if obj.__class__.__name__ == 'Account':
            from avernus.gui.account.edit_account_dialog import EditAccountDialog
            EditAccountDialog(obj, self)
            # set possible new name
            self.tree.get_model()[row][2] = obj.name
        else:
            obj, iterator = self.selected_item
            self.tree.set_cursor(path=self.tree.get_model().get_path(iterator),
                                 column=self.tree.get_column(0),
                                 start_editing=True)

    def on_sidebar_cell_edited(self, cellrenderertext, path, new_text):
        model = self.tree.get_model()
        model[path][0].name = model[path][2] = unicode(new_text)

    def on_sidebar_add(self, widget):
        obj_string = self.selected_item[0]
        if not isinstance(obj_string, str):
            obj_string = obj_string.__class__.__name__
        if "Portfolio" in obj_string:
            inserter = self.insert_portfolio
            item = container.Portfolio(name=_('new portfolio'))
        elif "Watchlist" in obj_string:
            inserter = self.insert_watchlist
            item = container.Watchlist(name=_('new watchlist'))
        elif "Account" in obj_string:
            inserter = self.insert_account
            item = account.Account(name=_('new account'), balance=0.0, type=1)
        else:
            return
        iterator = inserter(item)
        self.tree.set_cursor(path=self.tree.get_model().get_path(iterator),
                             column=self.tree.get_column(0),
                             start_editing=True)

GObject.type_register(Sidebar)


class InfoBox(object):

    def __init__(self, grid):
        self.line_count = 0
        self.grid = grid
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

        self.grid.attach(label, 0, self.line_count, 1, 1)
        self.grid.attach(info, 1, self.line_count, 1, 1)

        self.line_count += 1

    def clear(self):
        for child in self.grid:
            self.grid.remove(child)
        self.line_count = 0

    def on_update_page(self, page, initiator):
        self.clear()
        for label, info in page.get_info():
            self.add_line(label, info)
        self.grid.show_all()
        # returning False removes the hook
        return True

    def on_maintree_select(self, *args):
        self.clear()
