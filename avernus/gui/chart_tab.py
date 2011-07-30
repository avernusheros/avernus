#!/usr/bin/env python

from avernus.controller import chartController
from avernus.gui import charts
from avernus.controller import controller
import gtk


class ChartTab(gtk.ScrolledWindow):

    def __init__(self, pf):
        gtk.ScrolledWindow.__init__(self)
        self.pf = pf
        self.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        self.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        self.show_all()

    def show(self):
        if len(self.pf) == 0:
            self.add_with_viewport(gtk.Label('\n%s\n%s\n\n' % (_('No data!'), _('Add positions to portfolio first.') )))
            self.show_all()
            return

        width = self.allocation[2]
        self.clear()
        table = gtk.Table()

        #value over time chart
        hbox = gtk.HBox()
        table.attach(hbox, 0, 2, 0, 1)
        label = gtk.Label()
        label.set_markup('<b>'+_('Value over time')+'</b>')
        hbox.pack_start(label, fill=True, expand=True)

        combobox = gtk.combo_box_new_text()
        for st in ['daily', 'weekly', 'monthly', 'yearly']:
            combobox.append_text(st)
        combobox.set_active(2)
        combobox.connect('changed', self.on_zoom_change)
        hbox.pack_start(combobox, fill=False, expand=False)

        self.pfvalue_chart_controller = chartController.PortfolioValueChartController(self.pf, 'monthly')
        self.pfvalue_chart = charts.SimpleLineChart(self.pfvalue_chart_controller, width)
        table.attach(self.pfvalue_chart, 0, 2, 1, 2)

        label = gtk.Label()
        label.set_markup('<b>'+_('Market value')+'</b>')
        table.attach(label, 0,1,2,3)
        chart_controller = chartController.PositionAttributeChartController(self.pf, 'name')
        chart = charts.Pie(chart_controller, width/2)
        table.attach(chart, 0,1,3,4)

        label = gtk.Label()
        label.set_markup('<b>'+_('Investment types')+'</b>')
        table.attach(label,1,2,2,3)
        chart_controller = chartController.PositionAttributeChartController(self.pf, 'type_string')
        chart = charts.Pie(chart_controller, width/2)
        table.attach(chart, 1,2,3,4)

        row = 4
        col = 0
        switch = True
        for dim in controller.getAllDimension():
            label = gtk.Label()
            label.set_markup('<b>'+dim.name+'</b>')
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
        label.set_markup('<b>'+_('Dividends per Year')+'</b>')
        table.attach(label,0,2,row,row+1)
        chart_controller = chartController.DividendsPerYearChartController(self.pf)
        chart = charts.BarChart(chart_controller,width)
        table.attach(chart, 0,2,row+2,row+3)

        label = gtk.Label()
        label.set_markup('<b>'+_('Dividends')+'</b>')
        table.attach(label,0,2,row+3,row+4)
        chart_controller = chartController.DividendsPerPositionChartController(self.pf)
        chart = charts.BarChart(chart_controller,width)
        table.attach(chart, 0,2,row+4,row+5)

        self.add_with_viewport(table)
        self.show_all()

    def clear(self):
        for child in self.get_children():
            self.remove(child)

    def on_zoom_change(self, combobox):
        self.pfvalue_chart_controller.step = combobox.get_active_text()
        self.pfvalue_chart_controller.calculate_values()
        self.pfvalue_chart.draw_widget()
