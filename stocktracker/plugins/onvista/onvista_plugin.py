# -*- coding: utf-8 -*-

import gtk
from stocktracker.engine import engine

class OnvistaPlugin():
    configurable = False

    def activate(self):
        self.api.register_datasource(self, self.name)
                
    def deactivate(self):
        self.api.deregister_datasource(self, self.name)
        
    def search(self, searchstring):
        print "searching using ", self.name
        engine.onvista_search(searchstring)
