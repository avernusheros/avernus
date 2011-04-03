#!/usr/bin/env python

import gtk
from datetime import date
from avernus import cairoplot
from avernus.gui import gui_utils
from avernus.controller import controller


class ChartWindow(gtk.Window):
    
    def __init__ (self, stock):
        gtk.Window.__init__(self)
        self.stock = stock
        self.vbox = gtk.VBox()
        hbox = gtk.HBox()
        self.vbox.pack_start(hbox)
        label = gtk.Label()
        label.set_markup('<b>'+stock.name+'</b>\n'+stock.exchange)
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
        self.noDataLabelShown = False
        self.current_chart = gtk.Label('Fetching data...')
        self.change_label = gtk.Label('')
        self.vbox.pack_start(self.change_label)
        self.vbox.pack_end(self.current_chart)
        self.current_zoom = 'YTD'
        controller.GeneratorTask(controller.datasource_manager.update_historical_prices, complete_callback=self.add_chart).start(stock)
        self.add(self.vbox)
        self.show_all()

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

    def add_chart(self):
        self.vbox.remove(self.current_chart)
        date1 = date.today()
        date2 = self.get_date2(self.current_zoom, date1)

        data = controller.getQuotationsFromStock(self.stock, date2)
        if len(data) == 0:
            if not self.noDataLabelShown:
                self.noDataLabelShown = True
                self.add(gtk.Label('No historical data found!'))
                self.show_all()
            return
        quotes = [d.close for d in data]
        y_min = 0.95*min(quotes)
        y_max = 1.05*max(quotes)

        legend = [gui_utils.get_date_string(data[int(len(data)/18 *i)].date) for i in range(18)]
        legend.insert(0,str(data[0].date))
        legend.insert(len(legend),str(data[-1].date))

        plot = cairoplot.plots.DotLinePlot('gtk',
                        data=quotes,
                        x_labels=legend,
                        y_title='Share Price',
                        y_formatter = gui_utils.get_currency_format_from_float,
                        width=600,
                        height=250,
                        background="white light_gray",
                        grid=True,
                        series_colors=['blue'],
                        y_bounds=(y_min, y_max)
                        )
        change = quotes[-1] - quotes[0]
        if quotes[0] == 0:
            safeDiv = 1
        else:
            safeDiv = quotes[0]
        change_str = gui_utils.get_green_red_string(change, gui_utils.get_currency_format_from_float(change)+' ('+str(round(change/safeDiv*100,2))+'%)')
        self.change_label.set_markup(gui_utils.get_date_string(date2)+' - '+gui_utils.get_date_string(date1)+'     '+change_str)
        
        self.vbox.pack_end(plot.handler)

        self.current_chart = plot.handler
        self.show_all()

    def on_zoom_change(self, cb):
        zoom = self.zooms[cb.get_active()]
        if zoom != self.current_zoom:
            self.current_zoom = zoom
            self.add_chart()
