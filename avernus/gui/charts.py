import gtk
from avernus.gui import gui_utils
from avernus import cairoplot

class SimpleLineChart(gtk.VBox):

    def __init__(self, chartController, width):
        gtk.VBox.__init__(self)
        self.controller = chartController
        self.width = width
        self.chart = None
        self.draw_chart()

    def remove_chart(self):
        if self.chart:
            self.remove(self.chart)

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
                                dots=2,
                                series_colors=['blue','green'])
        self.chart = plot.handler
        self.pack_start(self.chart)
