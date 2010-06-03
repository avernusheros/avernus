# -*- coding: utf-8 -*-

import gtk

class helloWorldPlugin():
    prefs = {'text': "This is the hello world plugin"}
    configurable = True
    name = "HelloWorld"
    
    def __init__(self):
        self.menu_item = gtk.MenuItem("Hello World Plugin")
        self.menu_item.connect('activate', self.on_menu_clicked)

    def activate(self):
        self.api.add_menu_item(self.menu_item, 'Tools')
        self.load_preferences()
                
    def deactivate(self):
        self.api.remove_menu_item(self.menu_item)
        
    def on_menu_clicked(self, widget):
        d = gtk.MessageDialog(parent=None, flags=0, type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_NONE, message_format=None)
        d.set_markup(self.prefs['text'])
        d.run()
        d.destroy()

    def load_preferences(self):
        data = self.api.load_configuration(self.name)
        if not data is None and type(data) == type (dict()):
            self.prefs = data
    
    def configure(self):
        """called in plugins manager"""
        d = gtk.Dialog(buttons =  (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        vbox = d.get_content_area()
        self.entry = gtk.TextView()
        buffer = self.entry.get_buffer()
        buffer.set_text(self.prefs['text'])
        vbox.pack_start(self.entry)
        d.show_all()
        self.process_result(d.run())
        d.destroy()

    def process_result(self, response):
        if response == gtk.RESPONSE_ACCEPT:
            buffer = self.entry.get_buffer()
            self.prefs['text'] = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter())            
            self.api.save_configuration(self.name, self.prefs)
