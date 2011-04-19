from avernus.controller import controller, filterController
import gtk
from avernus.gui.gui_utils import Tree


class FilterDialog(gtk.Dialog):
    
    def __init__(self, *args, **kwargs):
        gtk.Dialog.__init__(self, _("Account Category Filters"), None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        self._init_widgets()
        self.show_all()
        response = self.run()
        self.process_result(response = response)
        self.destroy()
    
    def _init_widgets(self):
        vbox = self.get_content_area()

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
        self.filter_tree = FilterTree()
        vbox.pack_start(self.filter_tree) 
        
        actiongroup = gtk.ActionGroup('filter')
        actiongroup.add_actions([
                ('add',     gtk.STOCK_ADD,    'new transaction filter',      None, _('Add new transaction filter'), self.filter_tree.on_add),
                ('remove',  gtk.STOCK_DELETE, 'remove transaction filter',   None, _('Remove selected transaction filter'), self.filter_tree.on_remove)
                     ])
        toolbar = gtk.Toolbar()

        for action in actiongroup.list_actions():
            button = action.create_tool_item()
            toolbar.insert(button, -1)
        vbox.pack_start(toolbar, expand=False, fill=True)
        
        frame = gtk.Frame('Preview')
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
        #self.preview_tree = PreviewTree()
        frame.add(sw)
        #sw.add(self.preview_tree)
        vbox.pack_start(frame)
                
    def process_result(self, response):
        if response == gtk.RESPONSE_ACCEPT:
            print "D'accord"
            
            
class FilterTree(Tree):
    OBJECT = 0
    ACTIVE = 1
    FILTER_STR = 2
    CATEGORY = 3
    CATEGORY_STR = 4
    
    def __init__(self):
        Tree.__init__(self)
        self.model = gtk.ListStore(object, bool, str, object, str)
        self.set_model(self.model)

        column, cell = self.create_check_column(_('Active'), self.ACTIVE)
        cell.connect("toggled", self.on_toggled)
        col, cell = self.create_column(_('Filter'), self.FILTER_STR)
        cell.set_property('editable', True)
        cell.connect('edited', self.on_cell_edited)
        
        
        cell = gtk.CellRendererCombo()
        cell.connect('changed', self.on_category_changed)
        self.cb_model = gtk.ListStore(object, str)
        self.categories = controller.getAllAccountCategories()
        for category in self.categories:
            self.cb_model.append([category, category.name])
        cell.set_property('model', self.cb_model)
        cell.set_property('text-column', 1)
        cell.set_property('editable', True)
        column = gtk.TreeViewColumn(_('Category'), cell, text = self.CATEGORY_STR)
        column.pack_start(cell, expand = False)
        self.append_column(column)
        
        self.load_rules()
        
    def load_rules(self):
        for rule in filterController.get_all():
            self.insert_rule(rule)
    
    def on_category_changed(self, cellrenderertext, path, new_iter):
        category = self.cb_model[new_iter][0]
        self.model[path][self.CATEGORY_STR] = category.name
        self.model[path][self.OBJECT].category = category
    
    def on_cell_edited(self, cellrenderertext, path, new_text):
        self.model[path][self.FILTER_STR] = new_text 
        #FIXME vll erst bei ok saven
        self.model[path][self.OBJECT].rule = new_text
    
    def on_toggled(self, cellrenderertoggle, path):
        active = not self.model[path][self.ACTIVE]
        self.model[path][self.ACTIVE] = active
        self.model[path][self.OBJECT].active = active
      
    def on_add(self, widget):
        rule = filterController.create("new filter - click to edit", self.categories[0], False)
        self.insert_rule(rule)
        
    def on_remove(self, widget):
        item, iter = self.get_selected_item()
        if item is not None:
            item.delete()
            self.model.remove(iter)
    
    def insert_rule(self, rule):
        self.model.append([rule, rule.active, rule.rule, rule.category, rule.category.name])
