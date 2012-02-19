from gi.repository import Gtk
from avernus.gui import gui_utils, threads
from avernus import cairoplot, config


class ChartBase(Gtk.VBox):
    SPINNER_SIZE = 40

    def __init__(self, controller, width):
        Gtk.VBox.__init__(self)
        self.controller = controller
        self.width = width
        self.current_widget = None

        self.connect('realize', self.on_realize)

    def remove_widget(self):
        if self.current_widget:
            self.remove(self.current_widget)

    def draw_widget(self):
        pass

    def draw_spinner(self):
        self.remove_widget()
        self.current_widget = Gtk.Spinner()
        self.pack_start(self.current_widget, True, True, 0)
        self.current_widget.show()
        self.current_widget.set_size_request(self.SPINNER_SIZE, self.SPINNER_SIZE)
        self.current_widget.start()

    def on_realize(self, widget):
        self.draw_spinner()
        threads.GeneratorTask(self.controller.calculate_values, complete_callback=self.draw_widget).start()

    def update(self, *args, **kwargs):
        self.draw_spinner()
        self.controller.update(*args, **kwargs)
        threads.GeneratorTask(self.controller.calculate_values, complete_callback=self.draw_widget).start()


class Pie(ChartBase):

    def draw_widget(self):
        self.remove_widget()
        plot = cairoplot.plots.PiePlot('gtk',
                                        data=self.controller.values,
                                        width=self.width,
                                        height=self.width,
                                        gradient=True,
                                        values=True
                                        )
        self.current_widget = plot.handler
        self.current_widget.show()
        self.pack_start(self.current_widget, True, True, 0)


class BarChart(ChartBase):

    def draw_widget(self):
        self.remove_widget()
        if len(self.controller.y_values) == 0:
            self.pack_start(Gtk.Label(_('No data to plot')), True, True, 0)
            return

        plot = cairoplot.plots.VerticalBarPlot('gtk',
                                        data=self.controller.y_values,
                                        width=self.width,
                                        height=300,
                                        x_labels=self.controller.x_values,
                                        display_values=True,
                                        background="white light_gray",
                                        value_formatter = gui_utils.get_currency_format_from_float,
                                        )
        self.current_widget = plot.handler
        self.current_widget.show()
        self.pack_start(self.current_widget, True, True, 0)


class SimpleLineChart(ChartBase):

    def __init__(self, chartController, width, dots=2):
        self.dots = dots
        ChartBase.__init__(self, chartController, width)

    def draw_widget(self):
        self.remove_widget()
        configParser = config.AvernusConfig()
        option = configParser.get_option('normalize_y_axis', 'Chart')
        if option =="True":
            y_bounds = self.controller.get_y_bounds()
        else:
            y_bounds = None
        plot = cairoplot.plots.DotLinePlot('gtk',
                                data=self.controller.y_values,
                                width=self.width,
                                height=300,
                                x_labels=self.controller.x_values,
                                y_formatter=gui_utils.get_currency_format_from_float,
                                y_title='Amount',
                                background="white light_gray",
                                grid=True,
                                series_legend=True,
                                dots=self.dots,
                                series_colors=['blue','green','red'],
                                y_bounds = y_bounds)
        self.current_widget = plot.handler
        self.current_widget.show()
        self.pack_start(self.current_widget, True, True, 0)


class TransactionChart(SimpleLineChart):

    def __init__(self, chartController, width, dots=2):
        self.totalAvgLabel = Gtk.Label()
        SimpleLineChart.__init__(self, chartController, width, dots=dots)
        hbox = Gtk.HBox()
        monthlyBtn = Gtk.CheckButton(label=_('monthly'))
        monthlyBtn.connect('toggled',lambda x: self.on_combo_toggled(x, self.controller.set_monthly))
        hbox.pack_start(monthlyBtn, False, False, 0)
        rollingAvgBtn = Gtk.CheckButton(label=_('rolling average'))
        rollingAvgBtn.connect('toggled', lambda x: self.on_combo_toggled(x, self.controller.set_rolling_average))
        hbox.pack_start(rollingAvgBtn, False, False, 0)
        totalAvgBtn = Gtk.CheckButton(label=_('total average'))
        totalAvgBtn.connect('toggled', lambda x: self.on_combo_toggled(x, self.controller.set_total_average))
        hbox.pack_start(totalAvgBtn, False, False, 0)
        hbox.pack_end(self.totalAvgLabel, False, False, 0)
        self.pack_end(hbox, False, False, 0)

    def on_combo_toggled(self, widget, setter):
        active = widget.get_active()
        setter(active)
        self.draw_widget()

    def draw_widget(self):
        SimpleLineChart.draw_widget(self)
        if self.controller.total_avg:
            self.totalAvgLabel.set_text(_('Average ') + str(self.controller.average_y))
            self.totalAvgLabel.show()

    def remove_widget(self):
        if self.current_widget:
            self.remove(self.current_widget)
        if not self.controller.total_avg:
            self.totalAvgLabel.hide()
