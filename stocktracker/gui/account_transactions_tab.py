#!/usr/bin/env python

import gtk
from stocktracker import pubsub
from stocktracker.gui.gui_utils import Tree, get_datetime_string
import stocktracker.objects
from stocktracker.objects import controller
from stocktracker.gui.gui_utils import resize_wrap


class AccountTransactionTab(gtk.HPaned):
    def __init__(self, item):
        gtk.HPaned.__init__(self)
        
        sw = gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        self.transactions_tree = TransactionsTree(item)
        sw.add(self.transactions_tree)
        sw.connect_after('size-allocate', 
                         resize_wrap, 
                         self.transactions_tree, 
                         self.transactions_tree.dynamicWrapColumn, 
                         self.transactions_tree.dynamicWrapCell)
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

        #FIXME use something like 75% of available space
        self.set_position(400)
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
        
        col, cell = self.create_column(_('Description'), 1)
        cell.set_property('editable', True)
        cell.connect('edited', self.on_description_edited)
        self.dynamicWrapColumn = col
        self.dynamicWrapCell = cell
        cell.props.wrap_mode = gtk.WRAP_WORD
        
        self.create_column(_('Amount'), 2)
        self.create_column(_('Category'), 3)
        self.create_column(_('Date'), 4)
        
        self.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        #allows selecting multiple rows by dragging. does not work in 
        #combination with drag and drop
        #self.set_rubber_banding(True)
        
        self.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, 
                                      [ ( 'text/plain', 0, 80 )],
                                      gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_MOVE)
        self.connect("drag-data-get", self.on_drag_data_get)
        self.connect('drag-end', self.on_drag_end)
        self.connect('button_press_event', self.on_button_press)
        self.connect('button_release_event', self.on_button_release)

    def on_drag_data_get(self, treeview, context, selection, info, timestamp):
        treeselection = treeview.get_selection()
        model, paths = treeselection.get_selected_rows()
        iters = [model.get_iter(path) for path in paths]
        text = '\n'.join([str(model.get_value(iter, 0).id) for iter in iters])
        selection.set('text/plain', 8, text)
        return
    
    def on_drag_end(self,widget, drag_context):
        treeselection = self.get_selection()
        model, paths = treeselection.get_selected_rows()
        iters = [model.get_iter(path) for path in paths]
        for iter in iters:
            trans = model.get_value(iter, 0)
            model[iter] = self.get_item_to_insert(trans) 
        
    def on_description_edited(self, renderer, path, new_text):
        row = self.get_model()[path]
        row[0].description = new_text
        row[1] = new_text        
        
    def get_item_to_insert(self, ta):
        if ta.category:
            return [ta, ta.description, ta.amount, ta.category.name, str(ta.date)]
        else:    
            return [ta, ta.description, ta.amount, '', str(ta.date)]
        
    def load_transactions(self):
        for ta in controller.getTransactionsForAccount(self.account):
            self.insert_transaction(ta)
    
    def insert_transaction(self, ta):
        self.get_model().append(self.get_item_to_insert(ta))

    def on_button_press(self, widget, event):
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


class CategoriesTree(Tree):
    def __init__(self):
        Tree.__init__(self)
        #object, name, price, change
        self.set_model(gtk.TreeStore(object, str))
        self.set_reorderable(True)
        col, cell = self.create_column(_('Name'), 1)
        cell.set_property('editable', True)
        cell.connect('edited', self.on_cell_edited)        
        self.enable_model_drag_dest([ ( 'text/plain', 0, 80 )],
                                    gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_MOVE)
        self.connect("drag_data_received", self.on_drag_data_received)
        self.connect('cursor_changed', self.on_cursor_changed)
        
    def load_categories(self):
        for cat in controller.getAllAccountCategories():
            self.insert_item(cat)
    
    def insert_item(self, cat):
        return self.get_model().append(None, [cat, cat.name])

    def on_add(self, widget=None):
        item = controller.newAccountCategory('new category')
        iterator = self.insert_item(item)
        model = self.get_model()
        #self.expand_row( model.get_path(parent_iter), True)
        self.set_cursor(model.get_path(iterator), focus_column = self.get_column(0), start_editing=True)

    def on_edit(self, widget=None):
        selection = self.get_selection()
        treestore, selection_iter = selection.get_selected()
        model = self.get_model()
        self.set_cursor(model.get_path(selection_iter), focus_column = self.get_column(0), start_editing=True)
    
    def on_remove(self, widget=None):
        obj, iterator = self.selected_item
        dlg = gtk.MessageDialog(None,
             gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION,
             gtk.BUTTONS_OK_CANCEL)
        dlg.set_markup(_("Permanently delete category <b>")+obj.name+'</b>?')
        response = dlg.run()
        dlg.destroy()
        if response == gtk.RESPONSE_OK:
            obj.delete()
            self.get_model().remove(iterator)
    
    def on_cell_edited(self, cellrenderertext, path, new_text):
        m = self.get_model()
        m[path][0].name = m[path][1] = new_text

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

    def on_drag_data_received(self, widget, context, x, y, selection, target_type, time):
        drop_info = self.get_dest_row_at_pos(x, y)
        if drop_info is None:
            print "NO CATEGORY"
            return
        else:
            model = self.get_model()
            path, position = drop_info
            cat = self.get_model()[path[0]][0]
            for id in selection.data.split():
                transaction = controller.AccountTransaction.getByPrimaryKey(int(id))
                transaction.category = cat
