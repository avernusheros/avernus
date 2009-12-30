import gtk

class ContextMenu(gtk.Menu):
    def __init__(self):
        gtk.Menu.__init__(self)
    
    def show(self, event):
        print "show"
        self.show_all()
        self.popup(None, None, None, event.button, event.get_time())

