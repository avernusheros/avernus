#!/usr/bin/env python

from account_chart_tab import get_legend
from avernus import cairoplot, date_utils
from avernus.controller import chartController
from avernus.gui import gui_utils, charts
from avernus.controller import controller
from dateutil.rrule import *
import datetime
import gtk
import gobject


NO_DATA_STRING = '\nNo Data!\nAdd positions to portfolio first.\n\n'


class ChartTab(gtk.ScrolledWindow):

    def __init__(self, pf):
        gtk.ScrolledWindow.__init__(self)
        self.pf = pf
        self.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        self.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        self.show_all()

    def show(self):
        if len(self.pf) == 0:
            self.add_with_viewport(gtk.Label(NO_DATA_STRING))
            self.show_all()
            return

        width = self.allocation[2]
        self.clear()
        table = gtk.Table()

        table.attach(ValueChart(width, self.pf),0,2,0,1)

        label = gtk.Label()
        label.set_markup(_('<b>Market value</b>'))
        table.attach(label, 0,1,1,2)
        table.attach(Pie(width/2, self.pf, 'name'),0,1,2,3)

        label = gtk.Label()
        label.set_markup(_('<b>Investment types</b>'))
        table.attach(label,1,2,1,2)
        table.attach(Pie(width/2, self.pf, 'type_string'),1,2,2,3)

        row = 3
        col = 0
        switch = True
        for dim in controller.getAllDimension():
            label = gtk.Label()
            label.set_markup(_('<b>'+dim.name+'</b>'))
            table.attach(label, col,col+1,row,row+1)
            chart_controller = chartController.DimensionChartController(self.pf, dim)
            chart = charts.Pie(chart_controller, width/2)
            table.attach(chart, col, col+1, row+1, row+2)
            if switch:
                col = 1
            else:
                col = 0
                row += 2
            switch = not switch

        if not switch:
            row+=2

        label = gtk.Label()
        label.set_markup(_('<b>Dividends per Year</b>'))
        table.attach(label,0,2,row,row+1)
        chart_controller = chartController.DividendsPerYearChartController(self.pf)
        chart = BarChart(chart_controller,width)
        table.attach(chart, 0,2,row+2,row+3)

        label = gtk.Label()
        label.set_markup(_('<b>Dividends</b>'))
        table.attach(label,0,2,row+3,row+4)
        chart_controller = chartController.DividendsPerPositionChartController(self.pf)
        chart = BarChart(chart_controller,width)
        table.attach(chart, 0,2,row+4,row+5)

        self.add_with_viewport(table)
        self.show_all()

    def clear(self):
        for child in self.get_children():
            self.remove(child)


class ValueChart(gtk.VBox):
    SPINNER_SIZE = 40
    MAX_VALUES = 25

    def __init__(self, width, portfolio):
        gtk.VBox.__init__(self)
        self.portfolio = portfolio
        self.width = width
        self.chart = None

        hbox = gtk.HBox()
        self.pack_start(hbox, fill=False, expand=False)
        label = gtk.Label()
        label.set_markup(_('<b>Value over time</b>'))
        hbox.pack_start(label, fill=True, expand=True)

        combobox = gtk.combo_box_new_text()
        for st in ['daily', 'weekly', 'monthly', 'yearly']:
            combobox.append_text(st)
        combobox.set_active(2)
        combobox.connect('changed', self.on_zoom_change)
        hbox.pack_start(combobox, fill=False, expand=False)

        self.on_zoom_change(combobox)

    def on_zoom_change(self, cb):
        self.step = cb.get_active_text()
        if self.step == 'daily':
            self.days = list(rrule(DAILY, dtstart = self.portfolio.birthday, until = datetime.date.today()))[-self.MAX_VALUES:]
        elif self.step == 'weekly':
            self.days = list(rrule(WEEKLY, dtstart = self.portfolio.birthday, until = datetime.date.today(), byweekday=FR))[-self.MAX_VALUES:]
        elif self.step == 'monthly':
            self.days = list(rrule(MONTHLY, dtstart = self.portfolio.birthday, until = datetime.date.today(), bymonthday=-1))[-self.MAX_VALUES:]
        elif self.step == 'yearly':
            self.days = list(rrule(YEARLY, dtstart = self.portfolio.birthday, until = datetime.date.today(), bymonthday=-1, bymonth=12))[-self.MAX_VALUES:]
        self.redraw()

    def redraw(self):
        if self.chart:
            self.remove(self.chart)
        self.spinner = gtk.Spinner()
        self.spinner.set_size_request(self.SPINNER_SIZE, self.SPINNER_SIZE)
        self.pack_start(self.spinner, fill=True, expand=False)
        self.spinner.show()
        self.spinner.start()
        controller.GeneratorTask(self._get_data, complete_callback=self._show_chart).start()

    def _get_data(self):
        self.data = [self.portfolio.get_value_at_date(t) for t in self.days]
        yield 1

    def _show_chart(self):
        self.remove(self.spinner)
        plot = cairoplot.plots.DotLinePlot('gtk',
                                data=self.data,
                                width=self.width,
                                height=300,
                                x_labels = get_legend(self.days[0], self.days[-1], self.step),
                                y_formatter=gui_utils.get_currency_format_from_float,
                                y_title='Amount',
                                background="white light_gray",
                                grid=True,
                                dots=2,
                                )
        self.chart = plot.handler
        self.pack_start(self.chart)
        self.chart.show()


class BarChart(gtk.VBox):

    def __init__(self, chart_controller, width):
        gtk.VBox.__init__(self)
        self.chart_controller = chart_controller
        self.width = width
        self.draw()

    def draw(self):
        plot = cairoplot.plots.VerticalBarPlot('gtk',
                                        data=self.chart_controller.y_values,
                                        width=self.width,
                                        height=300,
                                        x_labels=self.chart_controller.x_values,
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
