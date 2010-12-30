#!/usr/bin/env python

from avernus import cairoplot, date_utils
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
        width = self.allocation[2]     
        self.clear()
        table = gtk.Table()

        #table.attach(gtk.Label(_('Cash over time')), 0,2,0,1)
        #table.attach(self.cash_chart(),0,2,1,2)
        
        label = gtk.Label()
        label.set_markup(_('<b>Market value</b>'))
        table.attach(label, 0,1,0,1)
        table.attach(Pie(width/2, self.pf, 'name'),0,1,1,2)
        
        label = gtk.Label()
        label.set_markup(_('<b>Investment types</b>'))
        table.attach(label,1,2,0,1)
        table.attach(Pie(width/2, self.pf, 'type_string'),1,2,1,2)
        
        row = 2
        col = 0
        switch = True
        for dim in controller.getAllDimension():
            label = gtk.Label()
            label.set_markup(_('<b>'+dim.name+'</b>'))
            table.attach(label, col,col+1,row,row+1)
            table.attach(DimensionPie(width/2, self.pf, dim),col,col+1,row+1,row+2)
            if switch:
                col = 1
            else:
                col = 0
                row += 2
            switch = not switch
            
        label = gtk.Label()
        label.set_markup(_('<b>Dividends per Year</b>'))
        table.attach(label,0,2,row,row+1)
        table.attach(DividendsPerYearChart(width/2, self.pf), 1,2,row+2,row+3)
        
        label = gtk.Label()
        label.set_markup(_('<b>Dividends</b>'))
        table.attach(label,0,2,row+3,row+4)
        table.attach(DividendsChart(width, self.pf), 0,2,row+4,row+5)

        self.add_with_viewport(table)
        self.show_all()

    def clear(self):
        for child in self.get_children():
            self.remove(child)

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


class DividendsPerYearChart(gtk.VBox):

    def __init__(self, width, portfolio):
        gtk.VBox.__init__(self)
        data = {}
        for year in date_utils.get_years(portfolio.birthday):
            data[str(year)] = 0.0
        for pos in portfolio:
            for div in pos.dividends:
                data[str(div.date.year)]+=div.total
        plot = cairoplot.plots.VerticalBarPlot('gtk',
                                        data=data,
                                        width=width,
                                        height=300,
                                        x_labels=data.keys(),
                                        display_values=True,
                                        background="white light_gray",
                                        value_formatter = gui_utils.get_currency_format_from_float,
                                        )
        chart = plot.handler
        chart.show()
        self.pack_start(chart)


class DividendsChart(gtk.VBox):

    def __init__(self, width, portfolio):
        gtk.VBox.__init__(self)
        data = {}
        for pos in portfolio:
            for div in pos.dividends:
                try:
                    data[pos.name]+=div.total
                except:
                    data[pos.name]=div.total                    
        if len(data) == 0:
            self.pack_start(gtk.Label('No dividends...'))
        else:
            plot = cairoplot.plots.VerticalBarPlot('gtk',
                                            data=data.values(),
                                            width=width,
                                            height=300,
                                            x_labels=data.keys(),
                                            display_values=True,
                                            background="white light_gray",
                                            value_formatter = gui_utils.get_currency_format_from_float,
                                            )
            chart = plot.handler
            chart.show()
            self.pack_start(chart)
            
class Pie(gtk.VBox):

    def __init__(self, width, portfolio, attribute):
        gtk.VBox.__init__(self)
        self.portfolio = portfolio
        data = {}
        for pos in self.portfolio:
            if getattr(pos.stock, attribute) is None:
                try:
                    data['None'] += pos.cvalue
                except:
                    data['None'] = pos.cvalue
            else:
                item = str(getattr(pos.stock, attribute))
                try:
                    data[item] += pos.cvalue
                except:
                    data[item] = pos.cvalue
        if sum(data.values()) == 0:
            self.pack_start(gtk.Label(NO_DATA_STRING))
        else:
            plot = cairoplot.plots.PiePlot('gtk',
                                        data=data,
                                        width=width,
                                        height=300,
                                        gradient=True,
                                        values=True
                                        )
            self.chart = plot.handler
            self.chart.show()
            self.pack_start(self.chart)


class DimensionPie(gtk.VBox):
    
    #FIXME show how many positions of portfolio are considered

    def __init__(self, width, portfolio, dimension):
        gtk.VBox.__init__(self)
        self.portfolio = portfolio
        data = {}
        for val in dimension.values:
            data[val.name] = 0
        for pos in self.portfolio:
            for adv in pos.stock.getAssetDimensionValue(dimension):
                data[adv.dimensionValue.name] += adv.value * pos.price * pos.quantity
        #remove unused dimvalues
        data = dict((k, v) for k, v in data.iteritems() if v != 0.0)
        if sum(data.values()) == 0:
            self.pack_start(gtk.Label('No positions assigned to dimension!'))
        else:
            plot = cairoplot.plots.PiePlot('gtk',
                                        data=data,
                                        width=width,
                                        height=300,
                                        gradient=True,
                                        values=True
                                        )
            self.chart = plot.handler
            self.chart.show()
            self.pack_start(self.chart)
