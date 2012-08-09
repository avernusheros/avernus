#!/usr/bin/env python

from avernus.controller import chart_controller
from avernus.gui import charts, page, gui_utils
from avernus.controller import portfolio_controller
from avernus.controller import dimensions_controller
from gi.repository import Gtk

import logging
logger = logging.getLogger(__name__)


class ChartTab(page.Page):

    def __init__(self, pf):
        page.Page.__init__(self)
        self.sw = Gtk.ScrolledWindow()
        self.add(self.sw)
        self.pf = pf
        self.sw.set_property('hscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        self.sw.set_property('vscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        self.show_all()

    def show(self):
        self.update_page()
        if len(self.pf.positions) == 0:
            self.sw.add_with_viewport(Gtk.Label(label='\n%s\n%s\n\n' % (_('No data!'), _('Add positions to portfolio first.'))))
            self.show_all()
            return
        width = self.sw.get_allocation().width
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
        #FIXME
        controller = chart_controller.PositionAttributeChartController(self.pf, 'type')
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
            controller = chart_controller.DimensionChartController(self.pf, dim)
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
        label.set_markup('<b>' + _('Dividends per year') + '</b>')
        label.set_tooltip_text(_('Total dividend payment per year.'))
        table.attach(label, 0, 2, y, y + 1)
        controller = chart_controller.DividendsPerYearChartController(self.pf)
        chart = charts.BarChart(controller, width)
        table.attach(chart, 0, 2, y + 2, y + 3)

        label = Gtk.Label()
        label.set_markup('<b>' + _('Dividends') + '</b>')
        label.set_tooltip_text(_('Total dividend payment for each position.'))
        table.attach(label, 0, 2, y + 3, y + 4)
        controller = chart_controller.DividendsPerPositionChartController(self.pf)
        chart = charts.BarChart(controller, width)
        table.attach(chart, 0, 2, y + 4, y + 5)

        self.sw.add_with_viewport(table)
        self.sw.show_all()

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
        Gtk.Dialog.__init__(self, _('New portfolio benchmark'), parent
                            , Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                     (Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        self.set_default_size(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)
        self.portfolio = portfolio

        vbox = self.get_content_area()

        self.tree = gui_utils.Tree()
        self.model = Gtk.ListStore(object, str, float)
        self.tree.set_model(self.model)
        vbox.pack_start(self.tree, True, True, 0)

        self.tree.create_column(_('Name'), 1)
        self.tree.create_column(_('Percentage'), 2)

        # load items
        self.count = 0
        for bm in portfolio_controller.get_benchmarks_for_portfolio(portfolio):
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

    def on_add(self, widget, user_data=None):
        if self.count < 3:
            dlg = Gtk.Dialog(_("Add benchmark"), self
                            , Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                     (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                      Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))

            vbox = dlg.get_content_area()
            table = Gtk.Table()
            vbox.pack_end(table, True, True, 0)
            table.attach(Gtk.Label("Percentage:"), 0,1,0,1)
            entry = Gtk.SpinButton()
            entry.set_adjustment(Gtk.Adjustment(lower=0, upper=100, step_increment=1.0, value=1))
            entry.set_digits(1)
            table.attach(entry, 1, 2, 0, 1, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.SHRINK)
            dlg.show_all()
            response = dlg.run()
            if response == Gtk.ResponseType.ACCEPT:
                bm = portfolio_controller.new_benchmark(self.portfolio, entry.get_value() / 100.0)
                self.model.append([bm, str(bm), bm.percentage*100.0])
                self.count += 1
            dlg.destroy()

        else:
            pass
            #FIXME show some error message

    def on_remove(self, widget, user_data=None):
        selection = self.tree.get_selection()
        model, selection_iter = selection.get_selected()
        if selection_iter:
            portfolio_controller.delete_object(model[selection_iter][0])
            self.model.remove(selection_iter)
            self.count -= 1
