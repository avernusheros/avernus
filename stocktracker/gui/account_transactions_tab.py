#!/usr/bin/env python

import gtk
from stocktracker import pubsub
from stocktracker.gui.gui_utils import Tree, get_datetime_string
import stocktracker.objects
from stocktracker.objects import controller


class AccountTransactionTab(gtk.HPaned):
    def __init__(self, item):
        gtk.HPaned.__init__(self)
        
        sw = gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        self.transactions_tree = TransactionsTree(item)
        sw.add(self.transactions_tree)
        self.pack1(sw)
        
        vbox = gtk.VBox()
        self.pack2(vbox)
        sw = gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        actiongroup = gtk.ActionGroup('categories')
        self.category_tree = CategoriesTree()
        actiongroup.add_actions([
                ('add',    gtk.STOCK_ADD,    'new category',    None, _('Add new category'), self.category_tree.on_add),      
                ('edit' ,  gtk.STOCK_EDIT,   'rename category',   None, _('Rename selected category'),   self.category_tree.on_edit),
                ('remove', gtk.STOCK_DELETE, 'remove category', None, _('Remove selected category'), self.category_tree.on_remove)
                                ])
        self.category_tree.actiongroup = actiongroup
        sw.add(self.category_tree)
        vbox.pack_start(sw)
        toolbar = gtk.Toolbar()
        self.conditioned = ['remove', 'edit']
        
        for action in ['add', 'remove', 'edit']:
            button = actiongroup.get_action(action).create_tool_item()
            toolbar.insert(button, -1)
        vbox.pack_start(toolbar, expand=False, fill=False)
                
        self.show_all()
    
    def show(self):
        self.transactions_tree.clear()
        self.transactions_tree.load_transactions()
        self.category_tree.clear()
        self.category_tree.load_categories()


class TransactionsTree(Tree):
    def __init__(self, account):
        self.account = account
        Tree.__init__(self)
        #object, name, price, change
        self.set_model(gtk.ListStore(object,str, int, str,str))
        
        self.create_column(_('Description'), 1)
        self.create_column(_('Amount'), 2)
        self.create_column(_('Category'), 3)
        self.create_column(_('Date'), 4)
        
        #pubsub.subscribe('transaction.added', self.on_transaction_created)
        
    def load_transactions(self):
        for ta in controller.getTransactionsForAccount(self.account):
            self.insert_transaction(ta)
    
    def insert_transaction(self, ta):
        print "INSERT", ta
        print ta.date
        if ta.category:
            self.get_model().append([ta, ta.description, ta.amount, ta.category.name, str(ta.date)])
        else:    
            self.get_model().append([ta, ta.description, ta.amount, '', str(ta.date)])


class CategoriesTree(Tree):
    def __init__(self):
        Tree.__init__(self)
        #object, name, price, change
        self.set_model(gtk.TreeStore(object, str))
        self.set_reorderable(True)
        self.create_column(_('Name'), 1)
                
    def load_categories(self):
        for cat in controller.getAllAccountCategories():
            self.insert_item(cat)
    
    def insert_item(self, cat):
        self.get_model().append(None, [cat, cat.name])

    def on_add(self, widget=None):
        new_cat = NewCategoryDialog().start()        
        if new_cat is not None:
            self.insert_item(new_cat)
    
    def on_edit(self, widget=None):
        pass
    
    def on_remove(self, widget=None):
        pass

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
                pubsub.publish('categorytree.select', obj)
            return 
        self.selected_item = None
        pubsub.publish('categorytree.unselect')
  
    def on_unselect(self):
        for action in ['remove', 'edit']:
            self.actiongroup.get_action(action).set_sensitive(False)       
        
    def on_select(self, obj):
        for action in ['remove', 'edit']:
            self.actiongroup.get_action(action).set_sensitive(True)


class NewCategoryDialog(gtk.Dialog):
    def __init__(self):
        gtk.Dialog.__init__(self, _("Create new category"), None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self.container_type = type
        vbox = self.get_content_area()
               
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        label = gtk.Label(_('Name:'))
        hbox.pack_start(label)
        self.name_entry = gtk.Entry()
        self.name_entry.set_text('unknown')
        self.name_entry.connect("activate", self.callback)
         
        hbox.pack_start(self.name_entry)

        self.show_all()
        
    def start(self):
        response = self.run()  
        res = self.process_result(response)
        self.destroy()
        return res
        
    def callback(self, widget):
        self.process_result(gtk.RESPONSE_ACCEPT)

    def process_result(self, response):
        if response == gtk.RESPONSE_ACCEPT:
            #grab the name
            name = self.name_entry.get_text()
            return controller.newAccountCategory(name)
        return None
