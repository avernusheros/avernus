#!/usr/bin/env python

from avernus.controller import chart_controller
from avernus.gui import charts, page, gui_utils
from avernus.controller import portfolio_controller
from avernus.controller import dimensions_controller
from gi.repository import Gtk

import logging
logger = logging.getLogger(__name__)


class ChartTab(Gtk.ScrolledWindow, page.Page):

    def __init__(self, pf):
        Gtk.ScrolledWindow.__init__(self)
        self.pf = pf
        self.set_property('hscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        self.set_property('vscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        self.show_all()

    def show(self):
        self.update_page()
        if len(self.pf.positions) == 0:
            self.add_with_viewport(Gtk.Label(label='\n%s\n%s\n\n' % (_('No data!'), _('Add positions to portfolio first.'))))
            self.show_all()
            return

        width = self.get_allocation().width
        self.clear()
        table = Gtk.Table()
        y = 0

        #value over time chart
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

        benchmark_button = Gtk.Button(_("Benchmarks"))
        benchmark_button.connect('button-press-event', self.on_button_press_event)
        hbox.pack_start(benchmark_button, False, False, 0)

        y += 1

        self.pfvalue_chart_controller = chart_controller.PortfolioChartController(self.pf, 'monthly')
        self.pfvalue_chart = charts.SimpleLineChart(self.pfvalue_chart_controller, width)
        table.attach(self.pfvalue_chart, 0, 2, y, y + 1)

        y += 1

        label = Gtk.Label()
        label.set_markup('<b>' + _('Market value') + '</b>')
        label.set_tooltip_text(_("Percentual fraction of each portfolio position."))
        table.attach(label, 0, 1, y, y + 1)

        y += 1

        controller = chart_controller.PositionAttributeChartController(self.pf, 'name')
        chart = charts.Pie(controller, width / 2)
        table.attach(chart, 0, 1, y, y + 1)

        label = Gtk.Label()
        label.set_markup('<b>' + _('Investment types') + '</b>')
        label.set_tooltip_text(_("Percentual fraction by investment type."))
        table.attach(label, 1, 2, y - 1, y)
        controller = chart_controller.PositionAttributechart_controller(self.pf, 'type_string')
        chart = charts.Pie(controller, width / 2)
        table.attach(chart, 1, 2, y, y + 1)

        y = y + 1

        col = 0
        switch = True
        for dim in dimensions_controller.get_all_dimensions():
            label = Gtk.Label()
            label.set_markup('<b>' + dim.name + '</b>')
            label.set_tooltip_text(_('Percentual fraction by "') + dim.name + '".')
            table.attach(label, col, col + 1, y, y + 1)
            controller = chart_controller.Dimensionchart_controller(self.pf, dim)
            chart = charts.Pie(controller, width / 2)
            table.attach(chart, col, col + 1, y + 1, y + 2)
            if switch:
                col = 1
            else:
                col = 0
                y += 2
            switch = not switch

        if not switch:
            y += 2

        label = Gtk.Label()
        label.set_markup('<b>' + _('Dividends per Year') + '</b>')
        label.set_tooltip_text(_('Total dividend payment per year.'))
        table.attach(label, 0, 2, y, y + 1)
        controller = chart_controller.DividendsPerYearchart_controller(self.pf)
        chart = charts.BarChart(controller, width)
        table.attach(chart, 0, 2, y + 2, y + 3)

        label = Gtk.Label()
        label.set_markup('<b>' + _('Dividends') + '</b>')
        label.set_tooltip_text(_('Total dividend payment for each position.'))
        table.attach(label, 0, 2, y + 3, y + 4)
        controller = chart_controller.DividendsPerPositionchart_controller(self.pf)
        chart = charts.BarChart(controller, width)
        table.attach(chart, 0, 2, y + 4, y + 5)

        self.add_with_viewport(table)
        self.show_all()

    def clear(self):
        for child in self.get_children():
            self.remove(child)

    def on_zoom_change(self, combobox):
        value = combobox.get_model()[combobox.get_active()][0]
        self.pfvalue_chart_controller.step = value
        self.pfvalue_chart.update()

    def on_button_press_event(self, widget, event):
        BenchmarkDialog(self.pf)


class BenchmarkDialog(Gtk.Dialog):
    DEFAULT_WIDTH = 300
    DEFAULT_HEIGHT = 300

    def __init__(self, portfolio, parent=None):
        Gtk.Dialog.__init__(self, _('New portfolio benchmakr'), parent
                            , Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                     (Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        self.set_default_size(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)
        self.portfolio = portfolio

        vbox = self.get_content_area()

        self.tree = gui_utils.Tree()
        self.model = Gtk.ListStore(object, str, float)
        self.tree.set_model(self.model)
        vbox.pack_start(self.tree, True, True, 0)

        self.tree.create_column('Name', 1)

        cell = Gtk.CellRendererSpin()
        adjustment = Gtk.Adjustment(0.00, 0, 100, 0.01, 10, 0)
        cell.set_property("digits", 1)
        cell.set_property("editable", True)
        cell.set_property("adjustment", adjustment)
        cell.connect("edited", self.on_percent_edited, 2)
        self.percent_col = Gtk.TreeViewColumn(_('Percentage'), cell, text=2)
        self.percent_col.set_cell_data_func(cell, gui_utils.float_format, 2)
        self.tree.append_column(self.percent_col)

        # load items
        self.count = 0
        for bm in self.portfolio.benchmarks:
            self.model.append([bm, str(bm), bm.percentage * 100])
            self.count += 1

        actiongroup = Gtk.ActionGroup('benchmarks')
        actiongroup.add_actions([
                ('add', Gtk.STOCK_ADD, 'new dimension', None, _('Add new dimension'), self.on_add),
                ('remove', Gtk.STOCK_DELETE, 'remove dimension', None, _('Remove selected dimension'), self.on_remove)
                     ])
        toolbar = Gtk.Toolbar()

        for action in actiongroup.list_actions():
            button = action.create_tool_item()
            toolbar.insert(button, -1)
        vbox.pack_start(toolbar, False, True, 0)

        self.show_all()
        self.run()

        self.destroy()

    def on_percent_edited(self, cellrenderertext, path, new_text, columnnumber):
        try:
            value = float(new_text.replace(",", ".")) / 100.0
            self.model[path][columnnumber] = value * 100
            self.model[path][0].percentage = value
        except:
            logger.debug("entered value is not a float", new_text)

    def on_add(self, widget, user_data=None):
        if self.count < 3:
            bm = portfolio_controller.new_benchmark(self.portfolio, 0.05)
            iterator = self.model.append([bm, str(bm), bm.percentage*100])
            self.tree.set_cursor(self.model.get_path(iterator), self.tree.get_column(0), True)
            self.count += 1
        else:
            pass
            #FIXME show some error message

    def on_remove(self, widget, user_data=None):
        selection = self.tree.get_selection()
        model, selection_iter = selection.get_selected()
        if selection_iter:
            model[selection_iter][0].delete()
            self.model.remove(selection_iter)
            self.count -= 1
