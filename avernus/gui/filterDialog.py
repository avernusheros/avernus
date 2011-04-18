'''
Created on 18.04.2011

@author: bastian
'''
import gtk

class FilterDialog(gtk.Dialog):
    
    def __init__(self, *args, **kwargs):
        gtk.Dialog.__init__(self, _("Account Category Filters"), None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        vbox = self.get_content_area()
        
        response = self.run()
        self.process_result(response)
        self.destroy()
        
    def process_result(self, response):
        if response == gtk.RESPONSE_ACCEPT:
            print "D'accord"