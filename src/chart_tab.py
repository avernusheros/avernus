from cairoplot.gtkcairoplot import gtk_pie_plot
import gtk



class ChartTab(gtk.VBox):
    def __init__(self, pf, model):
        gtk.VBox.__init__(self)
        self.pf = pf
        self.model = model
        self.show_all()

    
    def show(self):
        self.clear()
        self.pack_start(gtk.Label(_('Current')), False, False)
        self.pack_start(self.current_pie())
        
        self.pack_start(gtk.Label(_('Buy')), False, False)
        self.pack_start(self.buy_pie())
        
        self.show_all()
        
    def clear(self):
        for child in self.get_children():
            self.remove(child)
    
    def current_pie(self):
        data = {}
        for pos in self.pf:
            val = pos.cvalue
            if val != 0:
                data[pos.name] = val
        pie = gtk_pie_plot()        
        pie.set_args({'data':data, 'width':200, 'height':200})
        return pie

    def buy_pie(self):
        data = {}
        for pos in self.pf:
            val = pos.bvalue
            if val != 0:
                data[pos.name] = val
        pie = gtk_pie_plot()        
        pie.set_args({'data':data, 'width':200, 'height':200})
        return pie
