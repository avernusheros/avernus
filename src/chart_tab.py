from cairoplot.gtkcairoplot import gtk_pie_plot
import gtk



class ChartTab(gtk.ScrolledWindow):
    def __init__(self, pf, model):
        gtk.ScrolledWindow.__init__(self)
        self.pf = pf
        self.model = model
        
        
        self.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        self.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        self.show_all()

    
    def show(self):
        self.clear()
        vbox = gtk.VBox()
       
        vbox.pack_start(gtk.Label(_('Current')), False, False)
        vbox.pack_start(self.current_pie())
        
        vbox.pack_start(gtk.Label(_('Buy')), False, False)
        vbox.pack_start(self.buy_pie())
        self.add_with_viewport(vbox)
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
