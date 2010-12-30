#!/usr/bin/env python

import gtk
from datetime import datetime
from avernus import pubsub
from avernus.gui import gui_utils, dialogs, progress_manager
from avernus.objects import controller


class Category(object):
    __name__ = 'Category'
    def __init__(self, name):
        self.name = name


class MainTreeBox(gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self)
        actiongroup = gtk.ActionGroup('left_pane')

        main_tree = MainTree(actiongroup)
        self.pack_start(main_tree)

        actiongroup.add_actions([
                ('add',    gtk.STOCK_ADD,    'new container',    None, _('Add new portfolio or watchlist'),         main_tree.on_add),
                ('edit' ,  gtk.STOCK_EDIT,   'edit container',   None, _('Edit selected portfolio or watchlist'),   main_tree.on_edit),
                ('remove', gtk.STOCK_DELETE, 'remove container', None, _('Delete selected portfolio or watchlist'), main_tree.on_remove)
                                ])

        main_tree_toolbar = gtk.Toolbar()
        self.conditioned = ['remove', 'edit']

        for action in ['add', 'remove', 'edit']:
            button = actiongroup.get_action(action).create_tool_item()
            main_tree_toolbar.insert(button, -1)
        self.pack_start(main_tree_toolbar, expand=False, fill=False)

        vbox = gtk.VBox()
        self.pack_start(vbox, expand=False, fill=False)
        progress_manager.box = vbox


class MainTree(gui_utils.Tree):
    def __init__(self, actiongroup):
        gui_utils.Tree.__init__(self)
        self.actiongroup = actiongroup
        self.selected_item = None
        
        self._init_widgets()
        self.insert_categories()
        self._subscribe()
        self._load_items()

    def _load_items(self):
        #loading portfolios...
        for pf in controller.getAllPortfolio():
            self.insert_portfolio(pf)
        for wl in controller.getAllWatchlist():
            self.insert_watchlist(wl)
        for tag in controller.getAllTag():
            self.insert_tag(tag)
        for account in controller.getAllAccount():
            self.insert_account(account)
        self.expand_all()

    def _subscribe(self):
        self.connect('button-press-event', self.on_button_press_event)
        self.connect('key-press-event', self.on_key_press)
        self.connect('cursor_changed', self.on_cursor_changed)
        self.subscriptions = (
                    ("container.edited", self.on_updated),
                    ("tag.created", self.insert_tag),
                    ("tag.updated", self.on_updated),
                    ('account.updated', self.on_account_updated)
                )
        for topic, callback in self.subscriptions:
            pubsub.subscribe(topic, callback)

    def _init_widgets(self):
        #object, icon, name
        self.set_model(gtk.TreeStore(object,str, str, str))
        self.set_headers_visible(False)
        col, cell = self.create_icon_text_column('', 1,2)
        cell.set_property('editable', True)
        cell.connect('edited', self.on_cell_edited)
        self.create_column('', 3)
        
    def on_button_press_event(self, widget, event):
        target = self.get_path_at_pos(int(event.x), int(event.y))
        if target and event.type == gtk.gdk.BUTTON_PRESS:
            obj = self.get_model()[target[0]][0]
            if event.button == 3 and not isinstance(obj, Category):
                ContainerContextMenu(obj, self.actiongroup).show(event)
            elif self.get_selection().path_is_selected(target[0]) and isinstance(obj, Category):
                #disable editing of categories
                return True

    def on_key_press(self, widget, event):
        if gtk.gdk.keyval_name(event.keyval) == 'Delete':
            self.on_remove()
            return True
        return False

    def insert_categories(self):
        self.pf_iter = self.get_model().append(None, [Category('Portfolios'),'portfolios', _("<b>Portfolios</b>"),''])
        self.wl_iter = self.get_model().append(None, [Category('Watchlists'),'watchlists', _("<b>Watchlists</b>"),''])
        self.tag_iter = self.get_model().append(None, [Category('Tags'),'tags', _("<b>Tags</b>"),None])
        self.accounts_iter = self.get_model().append(None, [Category('Accounts'),'accounts', _("<b>Accounts</b>"),''])
        #self.index_iter = self.get_model().append(None, [Category('Indices'),'indices', _("<b>Indices</b>"),''])

    def insert_watchlist(self, item):
        self.get_model().append(self.wl_iter, [item, 'watchlist', item.name, ''])
    
    def insert_account(self, item):
        self.get_model().append(self.accounts_iter, [item, 'account', item.name, gui_utils.get_currency_format_from_float(item.amount)])
    
    def insert_portfolio(self, item):
        self.get_model().append(self.pf_iter, [item, 'portfolio', item.name, gui_utils.get_currency_format_from_float(item.cvalue)])

    def insert_tag(self, item):
        self.get_model().append(self.tag_iter, [item, 'tag', item.name, ''])

    def on_remove(self, widget=None):
        if self.selected_item is None:
            return
        obj, iter = self.selected_item
        if not isinstance(obj, Category):
            dlg = gtk.MessageDialog(None,
                 gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION,
                 gtk.BUTTONS_OK_CANCEL,
                 _("Permanently delete ")+obj.name+'?')
            response = dlg.run()
            dlg.destroy()
            if response == gtk.RESPONSE_OK:
                obj.delete()
                self.get_model().remove(iter)
                self.selected_item = None
                pubsub.publish('maintree.unselect')

    def on_account_updated(self, account):
        row = self.find_item(account)
        if row:
            self.find_item(account)[3] = gui_utils.get_currency_format_from_float(account.amount)
        
    def on_updated(self, item):
        obj, iter = self.selected_item
        row = self.get_model()[iter]
        if row:
            #row[1] = item
            row[2] = item.name
            row[3] = gui_utils.get_currency_format_from_float(item.amount)
        

    def on_cursor_changed(self, widget):
        #Get the current selection in the gtk.TreeView
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
        for action in ['remove', 'edit', 'add']:
            self.actiongroup.get_action(action).set_sensitive(False)

    def on_select(self, obj):
        if isinstance(obj, Category):
            self.on_unselect()
            #if obj.name == 'Portfolios': self.selected_type = 'portfolio'
            #elif obj.name == 'Watchlists': self.selected_type = 'watchlist'
            #elif obj.name == 'Accounts': self.selected_type = 'account'   
            if not obj.name in ['Portfolios', 'Watchlists', 'Accounts']:
                return
            self.actiongroup.get_action('add').set_sensitive(True)
        else:
            for action in ['remove', 'edit']:
                self.actiongroup.get_action(action).set_sensitive(True)

    def on_edit(self, treeview=None, iter=None, path=None):
        if self.selected_item is None:
            return
        obj, row = self.selected_item
        if obj.__name__ == 'Portfolio':
            EditPortfolio(obj)
        elif obj.__name__ == 'Watchlist':
            EditWatchlist(obj)
        elif obj.__name__ == 'Account':
            EditAccount(obj)

    def on_cell_edited(self,  cellrenderertext, path, new_text):
        m = self.get_model()
        m[path][0].name = m[path][2] = new_text

    def on_add(self, widget=None):
        obj, row = self.selected_item
        model = self.get_model()
        if obj.name == 'Portfolios':
            cat_type = 'portfolio'
            parent_iter = self.pf_iter
            item = controller.newPortfolio('new '+cat_type)
        elif obj.name == 'Watchlists':
            cat_type = 'watchlist'
            parent_iter = self.wl_iter
            item = controller.newWatchlist('new '+cat_type)
        elif obj.name == 'Accounts':
            cat_type = 'account'
            parent_iter = self.accounts_iter
            item = controller.newAccount('new '+cat_type)
        iterator = model.append(parent_iter, [item, cat_type, item.name, ''])
        self.expand_row( model.get_path(parent_iter), True)
        self.set_cursor(model.get_path(iterator), focus_column = self.get_column(0), start_editing=True)


class EditWatchlist(gtk.Dialog):
    def __init__(self, wl):
        gtk.Dialog.__init__(self, _("Edit..."), None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        self.wl = wl
        vbox = self.get_content_area()

        #name entry
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        label = gtk.Label(_('Name:'))
        hbox.pack_start(label)
        self.name_entry = gtk.Entry()
        self.name_entry.set_text(wl.name)
        hbox.pack_start(self.name_entry)

        self.show_all()
        self.name_entry.connect("activate", self.process_result)
        response = self.run()
        self.process_result(response = response)

    def process_result(self, widget=None, response = gtk.RESPONSE_ACCEPT):
        if response == gtk.RESPONSE_ACCEPT:
            self.wl.name = self.name_entry.get_text()
            pubsub.publish("container.edited", self.wl)
        self.destroy()
        
class EditAccount(gtk.Dialog):
    
    def __init__(self, acc):
        gtk.Dialog.__init__(self, _("Edit Account"), None,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        
        self.acc = acc
        vbox = self.get_content_area()
        table = gtk.Table()
        vbox.pack_start(table)
        
        label = gtk.Label(_("Name:"))
        table.attach(label, 0,1,0,1)
        self.name_entry = gtk.Entry()
        self.name_entry.set_text(acc.name)
        table.attach(self.name_entry, 1,2,0,1)
        
        #cash entry
        label = gtk.Label(_('Current balance:'))
        table.attach(label, 0,1,1,2)
        self.cash_entry = gtk.SpinButton(gtk.Adjustment(lower=-999999999, upper=999999999,step_incr=10, value = acc.amount), digits=2)
        table.attach(self.cash_entry,1,2,1,2)
        
        self.show_all()
        
        self.name_entry.connect("activate", self.process_result)
        response = self.run()
        self.process_result(response = response)

    def process_result(self, widget=None, response = gtk.RESPONSE_ACCEPT):
        if response == gtk.RESPONSE_ACCEPT:
            self.acc.name = self.name_entry.get_text()
            self.acc.amount = self.cash_entry.get_value()
            pubsub.publish("container.edited", self.acc)
        self.destroy()


class EditPortfolio(gtk.Dialog):
    def __init__(self, pf):
        gtk.Dialog.__init__(self, _("Edit..."), None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        self.pf = pf
        vbox = self.get_content_area()
        table = gtk.Table()
        vbox.pack_start(table)

        #name entry
        label = gtk.Label(_('Name:'))
        table.attach(label, 0,1,0,1)
        self.name_entry = gtk.Entry()
        self.name_entry.set_text(pf.name)
        table.attach(self.name_entry,1,2,0,1)

        #cash entry
        label = gtk.Label(_('Cash:'))
        table.attach(label, 0,1,1,2)
        self.cash_entry = gtk.SpinButton(gtk.Adjustment(lower=-999999999, upper=999999999,step_incr=10, value = pf.cash), digits=2)
        table.attach(self.cash_entry,1,2,1,2)

        self.show_all()
        self.name_entry.connect("activate", self.process_result)
        response = self.run()
        self.process_result(response = response)

    def process_result(self, widget=None, response = gtk.RESPONSE_ACCEPT):
        if response == gtk.RESPONSE_ACCEPT:
            self.pf.name = self.name_entry.get_text()
            self.pf.cash = self.cash_entry.get_value()
            pubsub.publish("container.edited", self.pf)
        self.destroy()


class ContainerContextMenu(gui_utils.ContextMenu):
    def __init__(self, container, actiongroup):
        gui_utils.ContextMenu.__init__(self)

        for action in ['edit', 'remove']:
            self.add(actiongroup.get_action(action).create_menu_item())

        self.add(gtk.SeparatorMenuItem())

        if container.__name__ == 'Portfolio':
            self.add_item(_('Deposit cash'),  lambda x: dialogs.CashDialog(container, 0) , 'gtk-add')
            self.add_item(_('Withdraw cash'),  lambda x: dialogs.CashDialog(container, 1) , 'gtk-remove')
