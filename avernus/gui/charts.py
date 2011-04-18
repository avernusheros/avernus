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
                                dots=self.dots,
                                series_colors=['blue','green'])
        self.chart = plot.handler
        self.chart.show()
        self.pack_start(self.chart)
