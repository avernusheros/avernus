from stocktracker.cairoplot.gtkcairoplot import gtk_dot_line_plot, gtk_vertical_bar_plot
import gtk
from stocktracker.treeviews import get_green_red_string
from datetime import date, timedelta
from stocktracker import updater

class ChartWindow(gtk.Window):
    def __init__ (self, stock):
        gtk.Window.__init__(self)
        self.add(Chart(stock))
        self.show_all()

class Chart(gtk.VBox):
    def __init__(self, stock):
        gtk.VBox.__init__(self)
        self.stock = stock
        
        hbox = gtk.HBox()
        self.add(hbox)
        label = gtk.Label()
        label.set_markup('<b>'+stock.name+'</b>')
        hbox.add(label)
        hbox.add(gtk.VSeparator())
        hbox.add(gtk.Label('Zoom:'))
        
        self.zooms = ['1m', '3m', '6m', 'YTD', '1y','2y','5y','10y', '20y']
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
        ret = None
        if zoom == '1m':
            ret = date(date1.year, ((date1.month+10) % 12)+1,date1.day)
        elif zoom == '3m':
            ret =  date(date1.year, ((date1.month+8) % 12)+1,date1.day)
        elif zoom == '6m':
            ret =  date(date1.year, ((date1.month+5) % 12)+1,date1.day)
        elif zoom == 'YTD':
            date2 = date(date1.year, 1,1)
            if (date1 - date2).days > 4:
                ret =  date(date1.year, 1,1)
            else: ret =  date(date1.year-1, 1,1)
        elif zoom == '1y':
            ret =  date(date1.year-1, date1.month,date1.day)
        elif zoom == '2y':
            ret =  date(date1.year-2, date1.month,date1.day)
        elif zoom == '5y':
            ret =  date(date1.year-5, date1.month,date1.day)
        elif zoom == '10y':
            ret =  date(date1.year-10, date1.month,date1.day)
        elif zoom == '20y':
            ret =  date(date1.year-20, date1.month,date1.day)
        if ret > date1:
            ret = date(ret.year-1, ret.month, ret.day)
        return ret
                
    def get_chart(self, zoom):
        vbox = gtk.VBox()
        date1 = date.today()
        date2 = self.get_date2(zoom, date1)
        data = updater.get_historical_prices(self.stock, date1, date2) 
        
        quotes = [d[4] for d in data]

        y_min = 0.95*min(quotes)
        y_max = 1.05*max(quotes)
        
        legend = [str(data[int(len(data)/20 *i)][0].date()) for i in range(20)]
       
        p1 = gtk_dot_line_plot()
        p1.set_args({'data':quotes, 
                     'x_labels':legend, 
                     'y_title': 'Share Price',
                     'series_colors': ['blue'],
                     'grid': True,
                     'width':600, 
                     'height':250,
                     'y_bounds':(y_min, y_max)})
                   
        change = quotes[-1] - quotes[0]
        change_str = get_green_red_string(change, str(change)+' ('+str(round(change/quotes[0]*100,2))+'%)')
        label = gtk.Label()
        label.set_markup(str(date2)+' - '+str(date1)+'     '+change_str)
        vbox.add(label)
        vbox.add(p1)
        vbox.add(gtk.Label(_('Volume (mil/1d)')))
        
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
        

