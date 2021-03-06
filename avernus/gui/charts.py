#!/usr/bin/env python

from gi.repository import Gtk
import matplotlib
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter
from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas
#from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas

from avernus.gui import gui_utils
from avernus.gui import threads


class ChartBase(Gtk.VBox):
    SPINNER_SIZE = 40

    def __init__(self, controller, width):
        Gtk.VBox.__init__(self)
        self.set_size_request(width, 300)
        self.controller = controller
        self.width = width
        self.current_widget = None
        self.connect('realize', self.on_realize)

        self.generate_colors()

        # spinner
        self.spinner = Gtk.Spinner()
        self.spinner.set_size_request(self.SPINNER_SIZE, self.SPINNER_SIZE)
        self.pack_start(self.spinner, True, True, 0)

        # plot
        self.setup()

    def draw_plot(self):
        pass

    def setup(self):
        pass

    def draw_spinner(self):
        if self.plot:
            self.plot.hide()
        self.spinner.show()
        self.spinner.start()

    def on_realize(self, widget):
        self.draw_spinner()
        threads.GeneratorTask(self.controller.calculate_values, complete_callback=self.draw_plot).start()

    def update(self, *args, **kwargs):
        self.draw_spinner()
        self.controller.update(*args, **kwargs)
        threads.GeneratorTask(self.controller.calculate_values, complete_callback=self.draw_plot).start()

    def redraw(self, *args, **kwargs):
        self.draw_spinner()
        threads.GeneratorTask(self.controller.calculate_values, complete_callback=self.draw_plot).start()

    def x_formatter(self, pos, *args):
        try:
            return self.controller.x_values[int(pos)]
        except:
            return "foo"

    def generate_colors(self, count=10):
        # gets theme color
        style = self.get_style()
        color = style.lookup_color('selected_bg_color')[1]
        color = (float(color.red) / 65535, float(color.green) / 65535, float(color.blue) / 65535)
        self.colors = []
        for i in range(0, 10):
            temp = (((color[0] + 0.8 * i) % 1.0), ((color[1] + 0.4 * i) % 1.0), ((color[2] + 0.2 * i) % 1.0))
            self.colors.append(temp)


class SimpleLineChart(ChartBase):

    def setup(self):
        fig = Figure(dpi=100, facecolor="white", edgecolor="white")
        self.ax = ax = fig.add_subplot(111)
        fig.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.1)

        # gridlines
        ax.yaxis.grid(color='gray')
        ax.xaxis.grid(color='gray')

        # background
        # ax.patch.set_alpha(1)

        # font
        matplotlib.rc('font', family="sans", weight="normal", size=9)

        # frame
        ax.set_frame_on(False)

        # formatter
        formatter = FuncFormatter(gui_utils.get_currency_format_from_float)
        ax.yaxis.set_major_formatter(formatter)
        formatter = FuncFormatter(self.x_formatter)
        ax.xaxis.set_major_formatter(formatter)

        self.ax.autoscale(enable=True, axis='both', tight=True)

        # annotation
        self.annotation = ax.annotate("foo",
                xy=(0.0, 0.0), xytext=(-20, 20),
                textcoords='offset points', ha='right', va='bottom',
                color='white',
                bbox=dict(boxstyle='round,pad=0.5', color=self.colors[0]),
                # arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0')
                )
        self.annotation.set_visible(False)

        # pack
        self.plot = FigureCanvas(fig)
        self.pack_start(self.plot, True, True, 0)

        # connect events
        fig.canvas.mpl_connect('motion_notify_event', self.on_move)

    def draw_plot(self):
        # remove lines
        self.ax.lines = []
        # vertical line
        self.line = self.ax.axvline(color='gray')
        self.line.set_visible(False)
        c = 0
        x_values = range(len(self.controller.x_values))
        for key, val in self.controller.y_values:
            while len(val) < len(x_values):
                val.append(0.0)
            self.ax.plot(x_values,
                         val,
                         'o-',
                         label=key,
                         color=self.colors[c])
            c += 1

        # legend
        legend = self.ax.legend(loc="best")
        # legend.draw_frame(False)
        legend.get_frame().set_edgecolor("gray")

        # show figure
        self.spinner.hide()
        self.plot.show()

    def on_move(self, event):
        if not event.inaxes:
            self.line.set_visible(False)
            self.annotation.set_visible(False)
            event.canvas.draw()
            return

        x_val = min(int(round(event.xdata, 0)), len(self.controller.x_values) - 1)
        self.line.set_xdata(x_val)
        self.line.set_visible(True)
        self.annotation.set_visible(True)
        self.annotation.xy = x_val, event.ydata
        text = self.controller.x_values[x_val] + "\n"
        for name, vals in self.controller.y_values:
            text += name + ": " + gui_utils.get_currency_format_from_float(vals[x_val]) + "\n"
        self.annotation.set_text(text)
        event.canvas.draw()


class BarChart(ChartBase):

    bar_width = 0.6

    def setup(self):
        fig = Figure(figsize=(5, 5), dpi=100, facecolor="white", edgecolor="white")
        self.ax = fig.add_subplot(111)

        fig.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.2)

        # font
        matplotlib.rc('font', family="sans", weight="normal", size=9)

        # frame
        self.ax.set_frame_on(False)

        # pack fig
        self.plot = FigureCanvas(fig)
        self.pack_start(self.plot, True, True, 0)

        # connect events
        fig.canvas.mpl_connect('motion_notify_event', self.on_move)

    def draw_plot(self):
        self.ax.clear()
        # gridlines
        self.ax.yaxis.grid(color='gray')
        self.ax.xaxis.grid(color='gray')

        # annotation
        self.annotation = self.ax.annotate("",
                xy=(0.0, 0.0), xytext=(-20, 20),
                textcoords='offset points', ha='right', va='bottom',
                color='white',
                bbox=dict(boxstyle='round,pad=0.5', color=self.colors[0]),
                # arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0')
                )
        self.annotation.set_visible(False)

        self.spinner.hide()
        pos = range(len(self.controller.x_values))
        if len(self.controller.y_values) == 0:
            self.plot.show()
            return

        c = 0
        for name, vals in self.controller.y_values:
            self.ax.bar(pos,
                        vals,
                        width=self.bar_width,
                        align="center",
                        facecolor=self.colors[c],
                        linewidth=0,
                        label=name)
            c += 1
        # self.ax.set_xticklabels(self.controller.x_values)

        # formatter
        formatter = FuncFormatter(gui_utils.get_currency_format_from_float)
        self.ax.yaxis.set_major_formatter(formatter)
        formatter = FuncFormatter(self.x_formatter)
        self.ax.xaxis.set_major_formatter(formatter)

        # ensure plots with less than 5 bars look ok
        if len(pos) < 5:
            self.ax.xaxis.set_ticks(pos)

        # legend
        legend = self.ax.legend(loc="best")
        # legend.draw_frame(False)
        legend.get_frame().set_edgecolor("gray")

        # recalc limits
        self.ax.relim()
        self.ax.autoscale_view(True, True, True)

        # vertical line
        # line needs to be drawn after recalc limits
        self.line = self.ax.axvline(color='gray')
        self.line.set_visible(False)

        # show plot
        self.plot.show()

    def on_move(self, event):
        if not event.inaxes:
            self.annotation.set_visible(False)
            self.line.set_visible(False)
            event.canvas.draw()
            return

        x_val = min(int(round(event.xdata, 0)), len(self.controller.x_values) - 1)

        self.annotation.set_visible(True)
        self.line.set_visible(True)
        self.line.set_xdata(x_val)
        self.annotation.xy = x_val, event.ydata
        text = self.controller.x_values[x_val] + "\n"
        for name, vals in self.controller.y_values:
            text += name + ": " + gui_utils.get_currency_format_from_float(vals[x_val]) + "\n"
        self.annotation.set_text(text)
        event.canvas.draw()


class Pie(ChartBase):

    def setup(self):
        fig = Figure(figsize=(10, 10), dpi=100, facecolor="white", edgecolor="white")
        self.ax = fig.add_subplot(111)
        fig.subplots_adjust(left=0.1, right=0.90, top=0.95, bottom=0.05)
        # ensure the pie is round
        self.ax.set_aspect('equal')

        matplotlib.rc('font', family="sans", weight="normal", size=9)

        self.plot = FigureCanvas(fig)
        self.pack_start(self.plot, True, True, 0)

    def draw_plot(self):
        self.ax.clear()
        self.ax.pie(self.controller.values.values(),
                    labels=self.controller.values.keys(),
                    autopct='%1.1f%%',
                    colors=self.colors
                    )
        # show pie
        self.spinner.hide()
        self.plot.show()
