import gtk
from stocktracker.treeviews import Tree

class Gainers(Tree):
    def __init__(self, pf):
        Tree.__init__(self)
        self.set_model(gtk.ListStore(str, str))
        self.create_column(_('Name'), 0)    
        self.create_column(_('Gain'), 1)    
            


class OverviewTab(gtk.Table):
    def __init__(self, pf, model, type):
        rows = 5
        columns = 2
        gtk.Table.__init__(self, rows, columns )
        self.pf = pf
        self.model = model
        self.type = type
        
        #self.add()
        
        self.show_all()
