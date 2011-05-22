import gtk
from avernus.gui import gui_utils
from avernus import cairoplot


class ChartBase(gtk.VBox):

    def __init__(self, controller, width):
        gtk.VBox.__init__(self)
        self.controller = controller
        self.width = width
        self.chart = None
        self.draw_chart()

    def remove_chart(self):
        if self.chart:
            self.remove(self.chart)


class Pie(ChartBase):

    def draw_chart(self):
        self.remove_chart()
        plot = cairoplot.plots.PiePlot('gtk',
                                        data=self.controller.values,
                                        width=self.width,
                                        height=300,
                                        gradient=True,
                                        values=True
                                        )
        self.chart = plot.handler
        self.pack_start(self.chart)


class BarChart(ChartBase):

    def draw_chart(self):
        plot = cairoplot.plots.VerticalBarPlot('gtk',
                                        data=self.controller.y_values,
                                        width=self.width,
                                        height=300,
                                        x_labels=self.controller.x_values,
                                        display_values=True,
                                        background="white light_gray",
                                        value_formatter = gui_utils.get_currency_format_from_float,
                                        )
        chart = plot.handler
        chart.show()
        self.pack_start(chart)


class SimpleLineChart(ChartBase):

    def __init__(self, chartController, width, dots=2):
        self.dots = dots
        ChartBase.__init__(self, chartController, width)

    def draw_chart(self):
        self.remove_chart()
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
        self.chart = plot.handler
        self.chart.show()
        self.pack_start(self.chart)
        
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
        self.draw_chart()
        
    def draw_chart(self):
        SimpleLineChart.draw_chart(self)
        if self.controller.total_avg:
            self.totalAvgLabel.set_text(_('Average ') + str(self.controller.average_y))
            self.totalAvgLabel.show()
        
    def remove_chart(self):
        if self.chart:
            self.remove(self.chart)
        if not self.controller.total_avg:
            self.totalAvgLabel.hide()
