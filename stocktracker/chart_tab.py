#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/stocktracker
#    objects.py: Copyright 2009 Wolfgang Steitz <wsteitz(at)gmail.com>
#
#    This file is part of stocktracker.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

from stocktracker.cairoplot.gtkcairoplot import gtk_pie_plot,gtk_vertical_bar_plot, gtk_dot_line_plot
import gtk
from session import session
from datetime import datetime

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
        
        table.attach(gtk.Label(_('PortfolioPerfomance')), 0,2,0,1)
        table.attach(PortfolioPerformanceChart(self.pf),0,2,1,2)
        
        table.attach(gtk.Label(_('Market value')), 0, 1, 2, 3)
        table.attach(self.current_pie(),0,1,3,4)
        
        table.attach(gtk.Label(_('Buy value')),1,2,2,3)
        table.attach(self.buy_pie(),1,2,3,4)
        
        table.attach(gtk.Label(_('Investment types')),0,1,4,5)
        table.attach(self.types_chart('pie'),0,1,5,6)
        #table.attach(self.types_chart('vertical_bars'),1,2,3,4)
        
        table.attach(gtk.Label(_('Tags')),1,2,4,5)
        table.attach(self.tags_pie(),1,2,5,6)
        
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
        pie.set_args({'data':data, 'width':300, 'height':300, 'gradient':True})
        return pie

    def buy_pie(self):
        data = {}
        for pos in self.pf:
            val = pos.bvalue
            if val != 0:
                data[pos.name] = val
        pie = gtk_pie_plot()        
        pie.set_args({'data':data, 'width':300, 'height':300, 'gradient':True})
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
        pie = gtk_pie_plot()        
        pie.set_args({'data':data, 'width':300, 'height':300, 'gradient':True})
        return pie




class PortfolioPerformanceChart(gtk.VBox):
    def __init__(self, pf):
        gtk.VBox.__init__(self)
        self.pf = pf
        
        hbox = gtk.HBox()
        self.add(hbox)
        hbox.add(gtk.Label('Zoom:'))
        
        self.zooms = ['1m', '3m', '6m', 'YTD', '1y','2y','5y','10y', '20y']
        combobox = gtk.combo_box_new_text()
        for ch in self.zooms:
            combobox.append_text(ch)
        combobox.set_active(3)
        combobox.connect('changed', self.on_zoom_change)
        hbox.add(combobox)
        
        self.current_zoom = 'YTD'
        self.create_chart(self.current_zoom)
        self.add(self.chart)
                
    def on_zoom_change(self, zoom):
        pass
                
    def create_chart(self, zoom): 
        data = {}
        data['investments'], data['cash'], data['overall'], legend = self.pf.value_over_time(datetime(2009, 10,1))
        
        print data
        
        self.chart = gtk_dot_line_plot()
        self.chart.set_args({'data':data, 
                     'x_labels':legend, 
                     #'y_title': 'Cash',
                     'series_colors': ['blue', 'green', 'red'],
                     'series_legend': True,
                     'grid': True,
                     'width':600, 
                     'height':300,
                     #'y_bounds':(y_min, y_max)
                     })
