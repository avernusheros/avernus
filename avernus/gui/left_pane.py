#!/usr/bin/env python

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Pango
from avernus import pubsub
from avernus.gui import gui_utils, progress_manager
from avernus.gui.account.csv_import_dialog import CSVImportDialog
from avernus.controller import controller
from avernus.controller import portfolio_controller as pfctlr


from avernus.objects.container import AllPortfolio
from avernus.objects.account import AllAccount


UI_INFO = """
<ui>
  <popup name='Popup'>
    <menuitem action='add' />
    <separator />
    <menuitem action='edit' />
    <menuitem action='remove' />
  </popup>
  <popup name='CategoryPopup'>
    <menuitem action='add' />
  </popup>
</ui>
"""


class Category(object):
    __name__ = 'Category'

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
        self.uimanager.add_ui_from_string(UI_INFO)
        # Add the accelerator group to the toplevel window
        accelgroup = self.uimanager.get_accel_group()
        #FIXME add accelgroup to toplevel window for keyboard shortcuts
        #self.get_toplevel().add_accel_group(accelgroup)

        self._init_widgets()
        self.insert_categories()
        self._subscribe()
        self._load_items()

    def _load_items(self):
        portfolios = pfctlr.getAllPortfolio()
        if len(portfolios) > 1:
            all_pf = AllPortfolio()
            all_pf.controller = pfctlr
            all_pf.name = "<i>%s</i>" % (_('All'),)
            self.insert_portfolio(all_pf)
        for pf in portfolios:
            self.insert_portfolio(pf)
        for wl in pfctlr.getAllWatchlist():
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
            if self.get_selection().path_is_selected(target[0]) and obj.__name__ == 'Category' :
                #disable editing of categories
                return True

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
        parent = self.get_toplevel()
        if obj.__name__ == 'Account':
            EditAccount(obj, parent)
        else:
            obj, selection_iter = self.selected_item
            self.set_cursor(self.get_model().get_path(selection_iter), focus_column=self.get_column(0), start_editing=True)

    def on_cell_edited(self, cellrenderertext, path, new_text):
        m = self.get_model()
        m[path][0].name = m[path][2] = new_text

    def on_add(self, widget=None, data=None):
        obj, row = self.selected_item
        model = self.get_model()

        if obj.__name__ == 'Portfolio' or obj.name == 'Portfolios':
            parent_iter = self.pf_iter
            cat_type = "portfolio"
            item = pfctlr.newPortfolio(_('new portfolio'))
        elif obj.__name__ == 'Watchlist' or obj.name == 'Watchlists':
            parent_iter = self.wl_iter
            cat_type = "watchlist"
            item = pfctlr.newWatchlist(_('new watchlist'))
        elif obj.__name__ == 'Account' or obj.name == 'Accounts':
            parent_iter = self.accounts_iter
            cat_type = "account"
            item = controller.newAccount(_('new account'))
        iterator = model.append(parent_iter, [item, cat_type, item.name, ''])
        self.expand_row(model.get_path(parent_iter), True)
        self.set_cursor(model.get_path(iterator), focus_column=self.get_column(0), start_editing=True)


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

