#!/usr/bin/env python
from avernus.controller import datasource_controller, chart_controller
from avernus.gui import threads, gui_utils, charts
from datetime import date
from gi.repository import Gtk


class ChartWindow(Gtk.Window):

    def __init__(self, stock):
        Gtk.Window.__init__(self)
        self.stock = stock
        self._init_widgets()

    def _init_widgets(self):
        self.vbox = Gtk.VBox()
        hbox = Gtk.HBox()
        self.vbox.pack_start(hbox, False, False, 0)
        label = Gtk.Label()
        label.set_markup('<b>' + self.stock.name + '</b>')
        hbox.add(label)
        hbox.add(Gtk.VSeparator())
        hbox.add(Gtk.Label(label='Zoom:'))

        self.zooms = ['1m', '3m', '6m', 'YTD', '1y', '2y', '5y', '10y', '20y']
        combobox = Gtk.ComboBoxText()
        for ch in self.zooms:
            combobox.append_text(ch)
        combobox.set_active(3)
        combobox.connect('changed', self.on_zoom_change)
        hbox.add(combobox)
        self.noDataLabelShown = False
        self.current_chart = Gtk.Label(label=_('Fetching data...'))
        self.change_label = Gtk.Label(label='')
        self.vbox.pack_start(self.change_label, False, False, 0)
        self.vbox.pack_end(self.current_chart, True, True, 0)
        self.current_zoom = 'YTD'
        threads.GeneratorTask(datasource_controller.get_historical_prices, complete_callback=self.add_chart, args=self.stock).start()
        self.add(self.vbox)
        self.show_all()

    def get_date2(self, zoom, date1):
        ret = None
        if zoom == '1m':
            ret = date(date1.year, ((date1.month + 10) % 12) + 1, date1.day)
        elif zoom == '3m':
            ret = date(date1.year, ((date1.month + 8) % 12) + 1, date1.day)
        elif zoom == '6m':
            ret = date(date1.year, ((date1.month + 5) % 12) + 1, date1.day)
        elif zoom == 'YTD':
            date2 = date(date1.year, 1, 1)
            if (date1 - date2).days > 4:
                ret = date(date1.year, 1, 1)
            else: ret = date(date1.year - 1, 1, 1)
        elif zoom == '1y':
            ret = date(date1.year - 1, date1.month, date1.day)
        elif zoom == '2y':
            ret = date(date1.year - 2, date1.month, date1.day)
        elif zoom == '5y':
            ret = date(date1.year - 5, date1.month, date1.day)
        elif zoom == '10y':
            ret = date(date1.year - 10, date1.month, date1.day)
        elif zoom == '20y':
            ret = date(date1.year - 20, date1.month, date1.day)
        if ret > date1:
            ret = date(ret.year - 1, ret.month, ret.day)
        return ret

    def add_chart(self):
        self.vbox.remove(self.current_chart)
        date1 = date.today()
        date2 = self.get_date2(self.current_zoom, date1)

        data = self.stock.get_quotations(date2)
        if len(data) == 0:
            if not self.noDataLabelShown:
                self.noDataLabelShown = True
                self.vbox.pack_end(Gtk.Label(label='No historical data found!'), True, True, 0)
                self.show_all()
            return
        controller = chart_controller.StockChartPlotController(data)
        self.current_chart = charts.SimpleLineChart(controller, 600)
        self.vbox.pack_end(self.current_chart, True, True, 0)

        change = controller.y_values[0][1][-1] - controller.y_values[0][1][0]
        if controller.y_values[0][1][0] == 0.1:
            safeDiv = 1
        else:
            safeDiv = controller.y_values[0][1][0]
        change_str = gui_utils.get_green_red_string(change, gui_utils.get_currency_format_from_float(change) + ' (' + str(round(change / safeDiv * 100, 2)) + '%)')
        self.change_label.set_markup(gui_utils.get_date_string(date2) + ' - ' + gui_utils.get_date_string(date1) + '     ' + change_str)

        self.show_all()

    def on_zoom_change(self, cb):
        zoom = self.zooms[cb.get_active()]
        if zoom != self.current_zoom:
            self.current_zoom = zoom
            self.add_chart()
