# -*- coding: utf-8 -*-

class OnvistaPlugin():
    configurable = False
    
    def __init__(self):
        self.name = 'onvista.de'

    def activate(self):
        self.api.register_datasource(self, self.name)
        
                        
    def deactivate(self):
        self.api.deregister_datasource(self, self.name)
        
    def search(self, searchstring, callback):
        print "searching using ", self.name