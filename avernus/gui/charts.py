import gtk
from avernus.gui import gui_utils
from avernus import cairoplot



class ChartBase(gtk.VBox):
    SPINNER_SIZE = 40

    def __init__(self, controller, width):
        gtk.VBox.__init__(self)
        self.controller = controller
        self.width = width
        self.widget = None
        
        self.connect('realize', self.on_realize)

    def remove_widget(self):
        if self.widget:
            self.remove(self.widget)
            
    def draw_widget(self):
        pass
    
    def draw_spinner(self):
        self.remove_widget()
        self.widget = gtk.Spinner()
        self.pack_start(self.widget, fill=True, expand=True)
        self.widget.show()
        self.widget.set_size_request(self.SPINNER_SIZE, self.SPINNER_SIZE)
        self.widget.start()
    
    def on_realize(self, widget):
        self.draw_spinner()
        gui_utils.BackgroundTask(self.controller.calculate_values, self.draw_widget)
    
    def update(self, *args, **kwargs):
        self.draw_spinner()
        self.controller.update(*args, **kwargs)
        gui_utils.BackgroundTask(self.controller.calculate_values, self.draw_widget)


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
        self.widget = plot.handler
        self.widget.show()
        self.pack_start(self.widget)


class BarChart(ChartBase):

    def draw_widget(self):
        self.remove_widget()
        if len(self.controller.y_values) == 0:
            self.pack_start(gtk.Label(_('No data to plot')))
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
        self.widget = plot.handler
        self.widget.show()
        self.pack_start(self.widget)


class SimpleLineChart(ChartBase):

    def __init__(self, chartController, width, dots=2):
        self.dots = dots
        ChartBase.__init__(self, chartController, width)

    def draw_widget(self):
        self.remove_widget()
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
                                series_colors=['blue','green','red'])
        self.widget = plot.handler
        self.widget.show()
        self.pack_start(self.widget)

class TransactionChart(SimpleLineChart):

    def __init__(self, chartController, width, dots=2):
        self.totalAvgLabel = gtk.Label()
        SimpleLineChart.__init__(self, chartController, width, dots=dots)
        hbox = gtk.HBox()
        monthlyBtn = gtk.CheckButton(label=_('monthly'))
        monthlyBtn.connect('toggled',lambda x: self.on_combo_toggled(x, self.controller.set_monthly))
        hbox.pack_start(monthlyBtn, expand=False, fill=False)
        rollingAvgBtn = gtk.CheckButton(label=_('rolling average'))
        rollingAvgBtn.connect('toggled', lambda x: self.on_combo_toggled(x, self.controller.set_rolling_average))
        hbox.pack_start(rollingAvgBtn, expand=False, fill=False)
        totalAvgBtn = gtk.CheckButton(label=_('total average'))
        totalAvgBtn.connect('toggled', lambda x: self.on_combo_toggled(x, self.controller.set_total_average))
        hbox.pack_start(totalAvgBtn, expand=False, fill=False)
        hbox.pack_end(self.totalAvgLabel, expand=False, fill=False)
        self.pack_end(hbox, expand=False, fill=False)


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
        if self.widget:
            self.remove(self.widget)
        if not self.controller.total_avg:
            self.totalAvgLabel.hide()
