#!/usr/bin/env python

from avernus.controller import chartController
from avernus.gui import charts, page
from avernus.controller import controller
from gi.repository import Gtk


class ChartTab(Gtk.ScrolledWindow, page.Page):

    def __init__(self, pf):
        Gtk.ScrolledWindow.__init__(self)
        self.pf = pf
        self.set_property('hscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        self.set_property('vscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        self.show_all()

    def show(self):
        self.update_page()
        if len(self.pf) == 0:
            self.add_with_viewport(Gtk.Label(label='\n%s\n%s\n\n' % (_('No data!'), _('Add positions to portfolio first.') )))
            self.show_all()
            return

        width = self.get_allocation().width
        self.clear()
        table = Gtk.Table()
        y = 0

        #value over time chart
        hbox = Gtk.HBox()
        table.attach(hbox, 0, 2, y, y+1)
        label = Gtk.Label()
        label.set_markup('<b>'+_('Value over time')+'</b>')
        label.set_tooltip_text(_("The value over time chart plots the portfolio value over the selected time period."))
        hbox.pack_start(label, True, True, 0)

        combobox = Gtk.ComboBoxText()
        for st in ['daily', 'weekly', 'monthly', 'yearly']:
            combobox.append_text(st)
        combobox.set_active(2)
        combobox.connect('changed', self.on_zoom_change)
        hbox.pack_start(combobox, False, False, 0)

        y += 1

        self.pfvalue_chart_controller = chartController.PortfolioValueChartController(self.pf, 'monthly')
        self.pfvalue_chart = charts.SimpleLineChart(self.pfvalue_chart_controller, width)
        table.attach(self.pfvalue_chart, 0, 2, y, y+1)

        y += 1

        label = Gtk.Label()
        label.set_markup('<b>'+_('Invested capital')+'</b>')
        label.set_tooltip_text(_("Invested capital over time. This plot is based on your transactions and dividend payments."))
        table.attach(label, 0,2,y,y+1)

        y += 1

        self.invest_chart_controller = chartController.InvestmentChartController(self.pf)
        self.invest_chart = charts.SimpleLineChart(self.invest_chart_controller, width)
        table.attach(self.invest_chart, 0, 2, y, y+1)

        y += 1

        label = Gtk.Label()
        label.set_markup('<b>'+_('Market value')+'</b>')
        label.set_tooltip_text(_("Percentual fraction of each portfolio position."))
        table.attach(label, 0,1,y,y+1)

        y += 1

        chart_controller = chartController.PositionAttributeChartController(self.pf, 'name')
        chart = charts.Pie(chart_controller, width/2)
        table.attach(chart, 0,1,y,y+1)

        label = Gtk.Label()
        label.set_markup('<b>'+_('Investment types')+'</b>')
        label.set_tooltip_text(_("Percentual fraction by investment type."))
        table.attach(label,1,2,y-1,y)
        chart_controller = chartController.PositionAttributeChartController(self.pf, 'type_string')
        chart = charts.Pie(chart_controller, width/2)
        table.attach(chart, 1,2,y,y+1)

        y = y+1

        col = 0
        switch = True
        for dim in controller.getAllDimension():
            label = Gtk.Label()
            label.set_markup('<b>'+dim.name+'</b>')
            label.set_tooltip_text(_('Percentual fraction by "')+dim.name+'".')
            table.attach(label, col,col+1,y,y+1)
            chart_controller = chartController.DimensionChartController(self.pf, dim)
            chart = charts.Pie(chart_controller, width/2)
            table.attach(chart, col, col+1, y+1, y+2)
            if switch:
                col = 1
            else:
                col = 0
                y += 2
            switch = not switch

        if not switch:
            y+=2

        label = Gtk.Label()
        label.set_markup('<b>'+_('Dividends per Year')+'</b>')
        label.set_tooltip_text(_('Total dividend payment per year.'))
        table.attach(label,0,2,y,y+1)
        chart_controller = chartController.DividendsPerYearChartController(self.pf)
        chart = charts.BarChart(chart_controller,width)
        table.attach(chart, 0,2,y+2,y+3)

        label = Gtk.Label()
        label.set_markup('<b>'+_('Dividends')+'</b>')
        label.set_tooltip_text(_('Total dividend payment for each position.'))
        table.attach(label,0,2,y+3,y+4)
        chart_controller = chartController.DividendsPerPositionChartController(self.pf)
        chart = charts.BarChart(chart_controller,width)
        table.attach(chart, 0,2,y+4,y+5)

        self.add_with_viewport(table)
        self.show_all()

    def clear(self):
        for child in self.get_children():
            self.remove(child)

    def on_zoom_change(self, combobox):
        self.pfvalue_chart_controller.step = combobox.get_active_text()
        self.pfvalue_chart_controller.calculate_values()
        self.pfvalue_chart.draw_widget()
