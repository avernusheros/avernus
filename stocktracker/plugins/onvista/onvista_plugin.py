# -*- coding: utf-8 -*-

import gtk

class OnvistaPlugin():
    
    def __init__(self):
        self.menu_item = gtk.MenuItem("Onvista")
        self.menu_item.connect('activate', self.on_menu_clicked)

    def activate(self):
        print "activate..:"
        self.api.add_menu_item(self.menu_item, 'Tools')
                
    def deactivate(self):
        self.api.remove_menu_item(self.menu_item)
        
    def on_menu_clicked(self, widget):
        d = gtk.MessageDialog(parent=None, flags=0, type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_NONE, message_format=None)
        d.set_markup("This is the onvista search plugin")
        d.run()
        d.destroy()
