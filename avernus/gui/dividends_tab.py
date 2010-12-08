#!/usr/bin/env python

import gtk
from datetime import datetime
from avernus.gui.gui_utils import Tree, get_datetime_string, get_name_string,float_to_string
from avernus.gui.dialogs import PosSelector
from avernus.objects import controller


class DividendsTab(gtk.VBox):
    def __init__(self, item):
        gtk.VBox.__init__(self)
        actiongroup = gtk.ActionGroup('dividend_tab')
        tree = DividendsTree(item, actiongroup)
        actiongroup.add_actions([
                ('add',    gtk.STOCK_ADD,     'add',    None, _('Add new dividend'),         tree.on_add),      
                ('remove', gtk.STOCK_DELETE,  'remove', None, _('Delete selected dividend'), tree.on_remove),
                 ])
        actiongroup.get_action('remove').set_sensitive(False)                       
        #self.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        #self.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        tb = gtk.Toolbar()
        for action in actiongroup.list_actions():
            button = action.create_tool_item()
            tb.insert(button, -1)         
        
        self.pack_start(tb, expand = False, fill = False)
        self.pack_start(tree)
        self.show_all()


class DividendsTree(Tree):
    def __init__(self, portfolio, actiongroup):
        self.portfolio = portfolio
        self.actiongroup = actiongroup
        self.selected_item = None        
        Tree.__init__(self)        
        self._init_widgets()
        self.load_dividends()
        self.connect('cursor_changed', self.on_cursor_changed)        
               
    def _init_widgets(self):    
        self.set_model(gtk.TreeStore(object, str, str, float, float))
        self.create_column(_('Position'), 1)
        self.create_column(_('Date'), 2)
        self.create_column(_('Amount'), 3, func=float_to_string)
        self.create_column(_('Transaction costs'), 4, func=float_to_string)
        
    def on_cursor_changed(self, widget):
        obj, iterator = self.get_selected_item()
        if isinstance(obj, controller.Dividend):
            self.actiongroup.get_action('remove').set_sensitive(True)
            return
        self.actiongroup.get_action('remove').set_sensitive(False)
        
    def load_dividends(self):
        for pos in self.portfolio:
            for div in pos.dividends:
                self.insert_dividend(div)
    
    def insert_dividend(self, div):
        self.get_model().append(None, [div, get_name_string(div.position.stock), get_datetime_string(div.date), div.price, div.costs])

    def on_add(self, widget=None):
        AddDividendDialog(self.portfolio, self)

    def on_remove(self, widget=None):
        obj, iterator = self.get_selected_item()
        if obj is None:
            return
        dlg = gtk.MessageDialog(None, 
             gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION, 
             gtk.BUTTONS_OK_CANCEL, 
             _("Permanently delete dividend?"))
        response = dlg.run()
        dlg.destroy()
        if response == gtk.RESPONSE_OK:
            obj.delete()
            self.get_model().remove(iterator) 
            self.actiongroup.get_action('remove').set_sensitive(False)


class AddDividendDialog(gtk.Dialog):
    def __init__(self, pf, tree):
        gtk.Dialog.__init__(self, _("Add dividend"), None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      'Add', gtk.RESPONSE_ACCEPT))
        self.pf = pf
        self.tree = tree
        vbox = self.get_content_area()
        table = gtk.Table()
        vbox.pack_start(table)
        
        table.attach(gtk.Label(_('Position: ')),0,1,0,1)
        self.pos_selector = PosSelector()
        self.pos_selector.on_pf_selection(pf)
        self.pos_selector.connect('changed', self.changed_pos)
        table.attach(self.pos_selector,1,2,0,1)
                
        self.selected_pos = None
        
        table.attach(gtk.Label(_('Amount: ')),0,1,1,2)
        self.value_entry = gtk.SpinButton(gtk.Adjustment(lower=0, upper=100000,step_incr=0.1, value = 1.0), digits=2)
        table.attach(self.value_entry, 1,2,1,2)
        
        table.attach(gtk.Label(_('Transaction costs: ')),0,1,2,3)
        self.tacosts_entry = gtk.SpinButton(gtk.Adjustment(lower=0, upper=100000,step_incr=0.1, value = 0.0), digits=2)
        table.attach(self.tacosts_entry, 1,2,2,3)
        
        self.calendar = gtk.Calendar()
        table.attach(self.calendar, 0,2,3,4)
        
        self.set_response_sensitive(gtk.RESPONSE_ACCEPT, False)
        self.show_all()
        response = self.run()  
        self.process_result(response)
        self.destroy()
    
    def changed_pos(self, combobox):
        model = combobox.get_model()
        index = combobox.get_active()
        if index:
            self.selected_pos = model[index][0]
            self.set_response_sensitive(gtk.RESPONSE_ACCEPT, True)
        else:
            self.selected_pos = None
            self.set_response_sensitive(gtk.RESPONSE_ACCEPT, False)
            
    def process_result(self, response):
        if response == gtk.RESPONSE_ACCEPT:
            year, month, day = self.calendar.get_date()
            date = datetime(year, month+1, day)
            value = self.value_entry.get_value()
            ta_costs = self.tacosts_entry.get_value()
            div = controller.newDividend(price=value, date=date, costs=ta_costs, position=self.selected_pos, shares=self.selected_pos.quantity)
            self.tree.insert_dividend(div)
