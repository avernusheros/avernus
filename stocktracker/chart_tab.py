from stocktracker.cairoplot.gtkcairoplot import gtk_pie_plot,gtk_vertical_bar_plot
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
        table = gtk.Table(rows = 4, columns =2)
               
        table.attach(gtk.Label(_('Market value')), 0, 1, 0, 1)
        table.attach(self.current_pie(),0,1,1,2)
        
        table.attach(gtk.Label(_('Buy value')),1,2,0,1)
        table.attach(self.buy_pie(),1,2,1,2)
        
        table.attach(gtk.Label(_('Investment types')),0,2,2,3)
        table.attach(self.types_chart('pie'),0,1,3,4)
        table.attach(self.types_chart('vertical_bars'),1,2,3,4)
        
        self.add_with_viewport(table)
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
        pie.set_args({'data':data, 'width':300, 'height':300})
        return pie

    def buy_pie(self):
        data = {}
        for pos in self.pf:
            val = pos.bvalue
            if val != 0:
                data[pos.name] = val
        pie = gtk_pie_plot()        
        pie.set_args({'data':data, 'width':300, 'height':300})
        return pie
   
    def types_chart(self, chart_type):
        sum = {0:0.0, 1:0.0}
        for pos in self.pf:
            sum[pos.type] += pos.cvalue
        data = {'stock':sum[0], 'fund':sum[1]}    
        if chart_type == 'pie':
            chart = gtk_pie_plot()  
        elif chart_type == 'vertical_bars':
            chart = gtk_vertical_bar_plot()
        chart.set_args({'data':data, 'width':300, 'height':300})
        return chart

    
