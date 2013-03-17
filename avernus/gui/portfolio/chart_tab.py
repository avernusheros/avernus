#!/usr/bin/env python
from avernus.controller import chart_controller
from avernus.gui import charts, page, get_avernus_builder
from gi.repository import Gtk
import logging


logger = logging.getLogger(__name__)


class ChartTab(page.Page):

    def __init__(self):
        page.Page.__init__(self)
        builder = get_avernus_builder()
        self.sw = builder.get_object("charts_sw")
        self.sw.connect("map", self.show)

    def set_portfolio(self, portfolio):
        self.pf = portfolio

    def show(self, *args):
        child = self.sw.get_child()
        if child:
            self.sw.remove(child)
        if len(self.pf.positions) == 0:
            self.sw.add_with_viewport(Gtk.Label(label='\n%s\n%s\n\n' % (_('No data!'), _('Add positions to portfolio first.'))))
            self.sw.show_all()
            return
        width = self.sw.get_allocation().width
        table = Gtk.Table()
        y = 0

        # value over time chart
        hbox = Gtk.HBox()
        table.attach(hbox, 0, 2, y, y + 1)
        label = Gtk.Label()
        label.set_markup('<b>' + _('Portfolio performance over time') + '</b>')
        label.set_tooltip_text(_("This chart plots the portfolio value over the selected time period."))
        hbox.pack_start(label, True, True, 0)

        combobox = Gtk.ComboBoxText()
        for st in ['daily', 'weekly', 'monthly', 'yearly']:
            combobox.append_text(st)
        combobox.set_active(2)
        combobox.connect('changed', self.on_zoom_change)
        hbox.pack_start(combobox, False, False, 0)

        y += 1

        self.pfvalue_chart_controller = chart_controller.PortfolioChartController(self.pf, 'monthly')
        self.pfvalue_chart = charts.SimpleLineChart(self.pfvalue_chart_controller, width)
        table.attach(self.pfvalue_chart, 0, 2, y, y + 1)

        y += 1

        label = Gtk.Label()
        label.set_markup('<b>' + _('Market value') + '</b>')
        label.set_tooltip_text(_("Percentual fraction of each portfolio position."))
        table.attach(label, 0, 1, y, y + 1)

        controller = chart_controller.PositionAttributeChartController(self.pf, 'name')
        chart = charts.Pie(controller, width / 2)
        table.attach(chart, 0, 1, y + 1, y + 2)

        label = Gtk.Label()
        label.set_markup('<b>' + _('Investment types') + '</b>')
        label.set_tooltip_text(_("Percentual fraction by investment type."))
        table.attach(label, 1, 2, y, y + 1)
        # FIXME
        controller = chart_controller.PositionAttributeChartController(self.pf, 'type')
        chart = charts.Pie(controller, width / 2)
        table.attach(chart, 1, 2, y + 1 , y + 2)
        
        y += 2

        label = Gtk.Label()
        label.set_markup('<b>' + _('Dividends per year') + '</b>')
        label.set_tooltip_text(_('Total dividend payment per year.'))
        table.attach(label, 0, 2, y, y + 1)
        controller = chart_controller.DividendsPerYearChartController(self.pf)
        chart = charts.BarChart(controller, width)
        table.attach(chart, 0, 2, y + 1, y + 2)

        y += 2

        label = Gtk.Label()
        label.set_markup('<b>' + _('Dividends') + '</b>')
        label.set_tooltip_text(_('Total dividend payment for each position.'))
        table.attach(label, 0, 2, y , y + 1)
        controller = chart_controller.DividendsPerPositionChartController(self.pf)
        chart = charts.BarChart(controller, width)
        table.attach(chart, 0, 2, y + 1, y + 2)

        self.sw.add_with_viewport(table)
        self.sw.show_all()
        self.update_page()

    def on_zoom_change(self, combobox):
        value = combobox.get_model()[combobox.get_active()][0]
        self.pfvalue_chart_controller.step = value
        self.pfvalue_chart.update()

