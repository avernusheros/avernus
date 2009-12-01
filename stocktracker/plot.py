from stocktracker.cairoplot.gtkcairoplot import gtk_dot_line_plot, gtk_vertical_bar_plot
import gtk
from datetime import date


class ChartWindow(gtk.Window):
    def __init__ (self, stock, model):
        gtk.Window.__init__(self)
        self.add(Chart(stock, model))
        self.show_all()

class Chart(gtk.VBox):
    def __init__(self, stock, model):
        gtk.VBox.__init__(self)
        self.stock = stock
        self.model = model
        
        hbox = gtk.HBox()
        self.add(hbox)
        label = gtk.Label()
        label.set_markup('<b>'+stock.name+'</b>')
        hbox.add(label)
        hbox.add(gtk.VSeparator())
        hbox.add(gtk.Label('Zoom:'))
        
        self.zooms = ['1m', '3m', '6m', 'YTD', '1y','2y','5y','10y', 'Max']
        combobox = gtk.combo_box_new_text()
        for ch in self.zooms:
            combobox.append_text(ch)
        combobox.set_active(3)
        combobox.connect('changed', self.on_zoom_change)
        hbox.add(combobox)
        
        self.current_zoom = 'YTD'
        self.current_chart = self.get_chart(self.current_zoom)
        self.add(self.current_chart)
        
        
    def get_date2(self, zoom, date1):
        if zoom == '1m':
            return date(date1.year, date1.month-1,date1.day)
        elif zoom == '3m':
            return date(date1.year, date1.month-3,date1.day)
        elif zoom == '6m':
            return date(date1.year, date1.month-6,date1.day)
        elif zoom == 'YTD':
            return date(date1.year, 1,1)
        elif zoom == '1y':
            return date(date1.year-1, date1.month,date1.day)
        elif zoom == '2y':
            return date(date1.year-2, date1.month,date1.day)
        elif zoom == '5y':
            return date(date1.year-5, date1.month,date1.day)
        elif zoom == '10y':
            return date(date1.year-10, date1.month,date1.day)
        elif zoom == 'Max':
            print "TODO"
            return date(date1.year-1, date1.month,date1.day)
        
    def get_chart(self, zoom):
        vbox = gtk.VBox()
        date1 = date.today()
        date2 = self.get_date2(zoom, date1)
        data = self.model.data_provider.get_historical_prices(self.stock, date1, date2) 
        
        quotes = [d[4] for d in data]
        #legend = ['Jan', 'Feb', 'Mar']        
       
        p1 = gtk_dot_line_plot()
        p1.set_args({'data':quotes, 
                     #'x_labels':legend, 
                     'y_title': 'Share Price',
                     'series_colors': ['blue'],
                     'grid': True,
                     'width':600, 
                     'height':250})
        vbox.add(p1)
        
        p2 = gtk_vertical_bar_plot()
        vols = [d[5] for d in data]
        p2.set_args({'data':vols, 
                     #'x_labels':legend, 
                     'grid': True,
                     'width':600, 
                     'height':100,
                     #'y_labels':[str(max(vols)), str(min(vols))],
                     'colors':['blue' for i in range(len(vols))]})
                     
        vbox.add(p2)
        return vbox
        
        
    def on_zoom_change(self, cb):
        zoom = self.zooms[cb.get_active()]
        if zoom != self.current_zoom:
            self.current_zoom = zoom
            self.remove(self.current_chart)
            self.current_chart = self.get_chart(zoom)
            self.add(self.current_chart)
            self.show_all()
        

if __name__ == '__main__':
    import objects
    w = gtk.Window()
    s = objects.Stock(0, 'Google', 'BMW.DE', None, 'Xetra',0, None, '234', None, '23')
    w.add(Chart(s))
    w.show_all()
    gtk.main()
