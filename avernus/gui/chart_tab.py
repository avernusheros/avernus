#!/usr/bin/env python

from avernus import cairoplot
import gtk
from avernus.objects import controller
from avernus.gui import gui_utils

NO_DATA_STRING = '\nNo Data!\nAdd positions to portfolio first.\n\n'


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

        #table.attach(gtk.Label(_('Cash over time')), 0,2,0,1)
        #table.attach(self.cash_chart(),0,2,1,2)

        label = gtk.Label()
        label.set_markup(_('<b>Market value</b>'))
        table.attach(label, 0, 1, 0, 1)
        table.attach(self.current_pie(),0,1,1,2)

        label = gtk.Label()
        label.set_markup(_('<b>Investment types</b>'))
        table.attach(label,1,2,0,1)
        table.attach(self.types_chart(),1,2,1,2)

        label = gtk.Label()
        label.set_markup(_('<b>Tags</b>'))
        table.attach(label,0,1,2,3)
        table.attach(self.tags_pie(),0,1,3,4)

        label = gtk.Label()
        label.set_markup(_('<b>Sectors</b>'))
        table.attach(label,1,2,2,3)
        table.attach(Pie(self.pf, 'sector'),1,2,3,4)

        label = gtk.Label()
        label.set_markup(_('<b>Region</b>'))
        table.attach(label,0,1,4,5)
        table.attach(Pie(self.pf, 'region'),0,1,5,6)

        #table.attach(gtk.Label(_('Portfolio Value')), 0,1, 4,5)
        #FIXME
        #table.attach(self.portfolio_value_chart(), 0,1,5,6)

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
            return gtk.Label(NO_DATA_STRING)
        plot = cairoplot.plots.PiePlot('gtk',
                                    data=data,
                                    width=300,
                                    height=300,
                                    gradient=True
                                    )
        return plot.handler


    def portfolio_value_chart(self):
        start = self.pf.birthday
        end = date.today()
        delta = end - start
        step = delta // 100
        print "Step: ",step
        data = []
        x_labels = []
        current = start
        while current < end:
            data.append(self.pf.get_value_at_date(current))
            x_labels.append(str(current))
            current += step
        chart = gtk_dot_line_plot()
        print "Data: ", data
        chart.set_args({'data':data, "x_labels":x_labels})
        return chart

    def types_chart(self):
        sum = {0:0.0, 1:0.0, 2:0.0}
        for pos in self.pf:
            sum[pos.stock.type] += pos.cvalue
        data = {'fund':sum[0], 'stock':sum[1], 'etf':sum[2]}
        if sum[0]+sum[1]+sum[2] == 0.0:
            return gtk.Label(NO_DATA_STRING)
        plot = cairoplot.plots.PiePlot('gtk',
                                    data=data,
                                    width=300,
                                    height=300,
                                    gradient=True
                                    )
        return plot.handler

    def tags_pie(self):
        data = {}
        for pos in self.pf:
            for tag in pos.tags:
                try:
                    data[tag] += pos.cvalue
                except:
                    data[tag] = pos.cvalue
        if len(data) == 0:
            return gtk.Label(NO_DATA_STRING)
        plot = cairoplot.plots.PiePlot('gtk',
                                    data=data,
                                    width=300,
                                    height=300,
                                    gradient=True
                                    )
        return plot.handler

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
                     'y_formatters':gui_utils.get_string_from_float
                     })
        return chart


class Pie(gtk.VBox):

    def __init__(self, portfolio, attribute):
        gtk.VBox.__init__(self)
        self.portfolio = portfolio

        data = {'None':0.0}
        for pos in self.portfolio:
            if getattr(pos.stock, attribute) is None:
                data['None'] += pos.cvalue
            else:
                item = getattr(pos.stock, attribute).name
                if item in data:
                    data[item] += pos.cvalue
                else:
                    data[item] = pos.cvalue
        if sum(data.values()) == 0:
            self.pack_start(gtk.Label(NO_DATA_STRING))
        else:
            plot = cairoplot.plots.PiePlot('gtk',
                                        data=data,
                                        width=300,
                                        height=300,
                                        gradient=True
                                        )
            self.chart = plot.handler
            self.chart.show()
            self.pack_start(self.chart)
