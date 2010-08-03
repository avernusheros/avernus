#!/usr/bin/env python

from stocktracker.cairoplot.gtkcairoplot \
    import gtk_pie_plot, gtk_vertical_bar_plot, gtk_dot_line_plot
import gtk
from stocktracker.objects import controller
no_data_string = '\nNo Data!\nAdd positions to portfolio first.\n\n'


class ChartTab(gtk.ScrolledWindow):

    def __init__(self, pf):
        gtk.ScrolledWindow.__init__(self)
        self.pf = pf
        self.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        self.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        self.show_all()

    def show(self):
        self.clear()
        table = gtk.Table()
    
        #FIXME 
        #table.attach(gtk.Label(_('Cash over time')), 0,2,0,1)
        #table.attach(self.cash_chart(),0,2,1,2)

        table.attach(gtk.Label(_('Market value')), 0, 1, 0, 1)
        table.attach(self.current_pie(),0,1,1,2)

        table.attach(gtk.Label(_('Investment types')),1,2,0,1)
        table.attach(self.types_chart('pie'),1,2,1,2)
        #table.attach(self.types_chart('vertical_bars'),1,2,3,4)
        
        table.attach(gtk.Label(_('Tags')),0,1,2,3)
        table.attach(self.tags_pie(),0,1,3,4)
        
        table.attach(gtk.Label(_('Sectors')),1,2,2,3)
        table.attach(self.sector_pie(),1,2,3,4)
        
        #FIXME countries not supported yet
        #table.attach(gtk.Label(_('Countries')),0,1,6,7)
        #table.attach(self.country_pie(),0,1,7,8)
        
        self.add_with_viewport(table)
        self.show_all()
        
    def clear(self):
        for child in self.get_children():
            self.remove(child)
    
    def current_pie(self):
        data = {}
        for pos in self.pf:
            if pos.cvalue != 0:
                try:
                    data[pos.name] += pos.cvalue
                except:
                    data[pos.name] = pos.cvalue
        if len(data) == 0:
            return gtk.Label(no_data_string)  
        pie = gtk_pie_plot()        
        pie.set_args({'data':data, 'width':300, 'height':300, 'gradient':True})
        return pie

    def types_chart(self, chart_type):
        sum = {0:0.0, 1:0.0, 2:0.0}
        for pos in self.pf:
            sum[pos.stock.type] += pos.cvalue
        data = {'fund':sum[0], 'stock':sum[1]}
        if sum[0]+sum[1] == 0.0:
            return gtk.Label(no_data_string)      
        if chart_type == 'pie':
            chart = gtk_pie_plot()  
        elif chart_type == 'vertical_bars':
            chart = gtk_vertical_bar_plot()
        chart.set_args({'data':data, 'width':300, 'height':300, 'gradient':True})
        return chart
        
    def tags_pie(self):
        data = {}
        for pos in self.pf:
            for tag in pos.tags:
                try:
                    data[tag] += pos.cvalue
                except:
                    data[tag] = pos.cvalue
        if len(data) == 0:
            return gtk.Label(no_data_string)            
        pie = gtk_pie_plot()        
        pie.set_args({'data':data, 'width':300, 'height':300, 'gradient':True})
        return pie
        
    def country_pie(self):
        data = {}
        for pos in self.pf:
            try:
                data[pos.stock.country] += pos.cvalue
            except:
                data[pos.stock.country] = pos.cvalue
        if len(data) == 0:
            return gtk.Label(no_data_string)        
        pie = gtk_pie_plot()        
        pie.set_args({'data':data, 'width':300, 'height':300, 'gradient':True})
        return pie
    
    def sector_pie(self):       
        data = {'None':0.0}
        for pos in self.pf:
            if pos.stock.sector is None:
                data['None'] += pos.cvalue
            else:
                sector = pos.stock.sector.name
                if sector in data:
                    data[sector] += pos.cvalue
                else:
                    data[sector] = pos.cvalue
        if sum(data.values()) == 0:
            return gtk.Label(no_data_string)         
        pie = gtk_pie_plot()        
        pie.set_args({'data':data, 'width':300, 'height':300, 'gradient':True})
        return pie

    def cash_chart(self):
        #FIXME stufenchart?
        cot = self.pf.get_cash_over_time()
        cot.reverse()
        
        data = [b for a, b, in cot]
        legend = [str(a) for a,b in cot]   
            
        chart = gtk_dot_line_plot()
        chart.set_args({'data':data, 
                     'x_labels':legend, 
                     'y_title': 'Cash',
                     'series_colors': ['blue'],
                     'grid': True,
                     'width':600, 
                     'height':300,
                     })
        return chart
