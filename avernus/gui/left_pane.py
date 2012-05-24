#!/usr/bin/env python

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Pango
from avernus import pubsub
from avernus.gui import gui_utils, progress_manager
from avernus.controller import account_controller
from avernus.controller import object_controller
from avernus.controller import portfolio_controller


class Category(object):

    def __init__(self, name):
        self.name = name


class MainTreeBox(Gtk.VBox):

    def __init__(self):
        super(Gtk.VBox, self).__init__()

        main_tree = MainTree()
        self.pack_start(main_tree, True, True, 0)

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

    def __init__(self):
        super(gui_utils.Tree, self).__init__()
        actiongroup = Gtk.ActionGroup('left_pane')
        self.selected_item = None

        actiongroup.add_actions([
            ('add', Gtk.STOCK_ADD, _('New'), "plus", _('New'), self.on_add),
            ('edit', Gtk.STOCK_EDIT, _('Edit'), "F2", _('Edit'), self.on_edit),
            ('remove', Gtk.STOCK_DELETE, _('Remove'), 'Delete', _('Delete'), self.on_remove)
        ])

        self.uimanager = Gtk.UIManager()
        self.uimanager.insert_action_group(actiongroup)
        self.uimanager.add_ui_from_file("ui/left_pane_popup.ui")
        # Add the accelerator group to the toplevel window
        accelgroup = self.uimanager.get_accel_group()
        #FIXME add accelgroup to toplevel window for keyboard shortcuts
        #self.get_toplevel().add_accel_group(accelgroup)

        self._init_widgets()
        self.insert_categories()
        self._subscribe()
        self._load_items()

    def _load_items(self):
        portfolios = portfolio_controller.get_all_portfolio()
        if len(portfolios) > 1:
            pass
            all_pf = portfolio_controller.AllPortfolio()
            all_pf.name = "<i>%s</i>" % (_('All'),)
            self.insert_portfolio(all_pf)
        for pf in portfolios:
            self.insert_portfolio(pf)
        for wl in portfolio_controller.get_all_watchlist():
            self.insert_watchlist(wl)

        accounts = account_controller.get_all_account()
        if len(accounts) > 1:
            all_account = account_controller.AllAccount()
            all_account.name = "<i>%s</i>" % (_('All'),)
            self.insert_account(all_account)
        for account in accounts:
            self.insert_account(account)
        self.expand_all()

    def _subscribe(self):
        self.connect('button-press-event', self.on_button_press_event)
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
        self.pf_iter = self.get_model().append(None, [Category('Portfolios'), 'portfolios', _("<b>Portfolios</b>"), ''])
        self.wl_iter = self.get_model().append(None, [Category('Watchlists'), 'watchlists', _("<b>Watchlists</b>"), ''])
        self.accounts_iter = self.get_model().append(None, [Category('Accounts'), 'accounts', _("<b>Accounts</b>"), ''])

    def insert_watchlist(self, item):
        self.get_model().append(self.wl_iter, [item, 'watchlist', item.name, ''])

    def insert_account(self, item):
        self.get_model().append(self.accounts_iter, [item, 'account', item.name, gui_utils.get_currency_format_from_float(item.balance)])

    def insert_portfolio(self, item):
        self.get_model().append(self.pf_iter, [item, 'portfolio', item.name, gui_utils.get_currency_format_from_float(portfolio_controller.get_current_value(item))])

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
                object_controller.delete_object(obj)
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
                    pubsub.publish('maintree.select', obj)
                return
        self.selected_item = None
        pubsub.publish('maintree.unselect')

    def on_edit(self, treeview=None, iter=None, path=None):
        if self.selected_item is None:
            return
        obj, row = self.selected_item
        #all portfolio and all account are not editable
        objtype = type(obj)
        if objtype == 'Category' or objtype == "AllPortfolio" or objtype == 'AllAccount':
            return
        if obj.__class__.__name__ == 'Account':
            self.edit_account(obj, row)
        else:
            obj, selection_iter = self.selected_item
            self.set_cursor(path=self.get_model().get_path(selection_iter), column=self.get_column(0), start_editing=True)

    def edit_account(self, acc, row):
        builder = Gtk.Builder()
        builder.add_from_file("ui/edit_account_dialog.glade")
        dlg = builder.get_object("dialog")
        dlg.set_transient_for(self.get_toplevel())
        name_entry = builder.get_object("name_entry")
        name_entry.set_text(acc.name)
        balance_entry = builder.get_object("balance_entry")
        adjustment = builder.get_object("adjustment1")
        adjustment.set_value(acc.balance)
        dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                      Gtk.STOCK_APPLY, Gtk.ResponseType.ACCEPT)

        def response_callback(widget, response):
            if response == Gtk.ResponseType.ACCEPT:
                acc.name = self.get_model()[row][2] = name_entry.get_text()
                acc.balance = balance_entry.get_value()
                self.get_model()[row][3] = gui_utils.get_currency_format_from_float(acc.balance)
            dlg.destroy()

        dlg.connect('response', response_callback)
        dlg.show()

    def on_cell_edited(self, cellrenderertext, path, new_text):
        m = self.get_model()
        m[path][0].name = m[path][2] = new_text

    def on_add(self, widget=None, data=None):
        obj, row = self.selected_item
        model = self.get_model()

        if obj.__class__.__name__ == 'Portfolio' or obj.name == 'Portfolios':
            parent_iter = self.pf_iter
            cat_type = "portfolio"
            item = portfolio_controller.new_portfolio(_('new portfolio'))
        elif obj.__class__.__name__ == 'Watchlist' or obj.name == 'Watchlists':
            parent_iter = self.wl_iter
            cat_type = "watchlist"
            item = portfolio_controller.new_watchlist(_('new watchlist'))
        elif obj.__class__.__name__ == 'Account' or obj.name == 'Accounts':
            parent_iter = self.accounts_iter
            cat_type = "account"
            item = account_controller.new_account(_('new account'))
        iterator = model.append(parent_iter, [item, cat_type, item.name, ''])
        self.expand_row(model.get_path(parent_iter), True)
        self.set_cursor(model.get_path(iterator), start_editing=True)
