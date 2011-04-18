'''
Created on 18.04.2011

@author: bastian
'''
from avernus.controller import controller
import gtk

class FilterDialog(gtk.Dialog):
    
    priorities = [1,2,3]
    
    def __init__(self, *args, **kwargs):
        gtk.Dialog.__init__(self, _("Account Category Filters"), None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        
        self.toDelete = []
        self.toAdd = []
        self.categories = controller.getAllAccountCategories()
        
        vbox = self.get_content_area()
        frame = gtk.Frame(label=_('Create New'))
        vbox.pack_start(frame, fill=False, expand =False)
        self.category_cb = gtk.combo_box_new_text()
        self.category_cb.set_tooltip_text(_('Category'))
        for category in self.categories:
            self.category_cb.append_text(category.name)
        hbox = gtk.HBox()
        hbox.pack_start(self.category_cb, expand=False,fill=False)
        self.active_check = gtk.CheckButton(label=_('active'))
        hbox.pack_start(self.active_check)
        self.priority_cb = gtk.combo_box_new_text()
        self.priority_cb.set_tooltip_text(_('Priority'))
        for prio in self.priorities:
            self.priority_cb.append_text(str(prio))
        hbox.pack_start(self.priority_cb)
        self.ruleEntry = gtk.Entry()
        self.ruleEntry.set_tooltip_text(_('Rule'))
        self.ruleEntry.set_width_chars(50)
        hbox.pack_start(self.ruleEntry)
        self.addBtn = gtk.Button(stock=gtk.STOCK_ADD)
        self.addBtn.connect('clicked', self.on_add)
        self.addBtn.set_tooltip_text(_('Add'))
        hbox.pack_start(self.addBtn)
        frame.add(hbox)
                
        self.show_all()
        response = self.run()
        self.process_result(response)
        self.destroy()
        
    def on_add(self, btn):
        print btn
        
    def process_result(self, response):
        if response == gtk.RESPONSE_ACCEPT:
            print "D'accord"