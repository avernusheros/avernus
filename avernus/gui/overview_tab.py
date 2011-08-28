#!/usr/bin/env python

from gi.repository import Gtk
from avernus.gui.gui_utils import Tree


class OverviewTab(Gtk.Table):
    
    def __init__(self, container):
        Gtk.Table.__init__(self)
        self.container = container
        
        self.attach(Gtk.Label(label='Performance'),0,2,0,1)
        self.attach(PerformanceTree(container),0,2,1,2)
        
        self.attach(Gtk.Label(label='Gainers'),0,1,2,3)
        self.attach(GainersTree(container),0,1,3,4)
        self.attach(Gtk.Label(label='Losers'),1,2,2,3)
        self.attach(LosersTree(container),1,2,3,4)
        
        self.set_col_spacing(0, 50)
        
        self.show_all()


class PerformanceTree(Tree):
    def __init__(self, container):
        Tree.__init__(self)
        self.container = container
        self.set_model(Gtk.TreeStore(str, float, float))
        self.create_column('Period', 0)
        self.create_column('absolut', 1)
        self.create_column('relative', 2)
        self.set_rules_hint(True)
        self.set_headers_visible(False)
        self.load()
   
    def load(self):
        absolut, percent = self.container.current_change
        self.get_model().append(None, ['<b>Today</b>', absolut, percent])
        #TODO 30 days, ytd, 1year, 2year ..
        absolut, percent = self.container.overall_change
        self.get_model().append(None, ['<b>Overall</b>', absolut, percent])
        

class GainersTree(Tree):
    def __init__(self, container):
        self.container = container
        Tree.__init__(self)
        self.set_model(Gtk.ListStore(str, str))
        self.create_column(_('Name'), 0)    
        self.create_column(_('Gain'), 1)    
        self.load()
        
    def load(self):
        pass


class LosersTree(Tree):
    def __init__(self, container):
        self.container = container
        Tree.__init__(self)
        self.set_model(Gtk.ListStore(str, str))
        self.create_column(_('Name'), 0)    
        self.create_column(_('Loss'), 1)    
        self.load()
        
    def load(self):
        pass
