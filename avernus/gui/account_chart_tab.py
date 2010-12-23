#!/usr/bin/env python

from avernus import cairoplot
import gtk
from avernus.objects import controller
import datetime
from avernus import date_utils
from avernus.gui import gui_utils
from dateutil.relativedelta import relativedelta

no_data_string = _('\nNo Data!\nAdd transactions first.\n\n')
MONTHS = {
        '1m':1,
        '3m':3,
        '6m':6,
        '1y':12,
        '2y':24,
        '5y':60,
        }

def get_legend(smaller, bigger, step):
    erg = []
    if step == 'month':
        delta = relativedelta(months=+1)
        formatstring = "%b %y"
    elif step == 'year':
        delta = relativedelta(years=+1)
        formatstring = "%Y"
    elif step == 'day':
        delta = relativedelta(days=+1)
        formatstring = "%x"
    elif step == 'week':
        delta = relativedelta(weeks=+1)
        formatstring = "%U"
    while smaller <= bigger:
        erg.append(smaller.strftime(formatstring))
        smaller+=delta
    return erg


class AccountChartTab(gtk.ScrolledWindow):

    TABLE_SPACINGS = 5

    def __init__(self, account):
        gtk.ScrolledWindow.__init__(self)
        self.account = account
        self.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        self.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        self.table = gtk.Table()
        self.table.set_col_spacings(self.TABLE_SPACINGS)
        self.table.set_row_spacings(self.TABLE_SPACINGS)

        self.add_with_viewport(self.table)
        self.zooms = ['ACT','1m', '3m', '6m', 'YTD', '1y','2y','5y', 'all']
        combobox = gtk.combo_box_new_text()
        for ch in self.zooms:
            combobox.append_text(ch)
        combobox.set_active(4)
        self.zoom = 'YTD'
        self.end_date = datetime.date.today()
        self._calc_start_date()
        combobox.connect('changed', self.on_zoom_change)
        self.table.attach(combobox, 0,1,0,1)

        #FIXME macht das step einstellen wirklich sinn? alternative ist automatische einstellung
        #oder manuelle einstellung erlauben, aber sachen vorgeben, zb 1y und month
        self.steps = ['day','week','month','year']
        active = 2
        combobox = gtk.combo_box_new_text()
        for st in self.steps:
            combobox.append_text(st)
        combobox.set_active(active)
        self.current_step = self.steps[active]
        combobox.connect('changed', self.on_step_change)
        self.table.attach(combobox,1,2,0,1)

        self.charts = []
        chart = EarningsVsSpendingsChart(self.account, self.start_date, self.end_date, self.current_step)
        self.charts.append(chart)
        self.table.attach(chart,0,2,2,3)

        label = gtk.Label()
        label.set_markup('<b>Balance over time</b>')
        self.table.attach(label, 0,2,3,4)
        chart = BalanceChart(self.account, self.start_date, self.end_date)
        self.charts.append(chart)
        self.table.attach(chart,0,2,4,5)

        label = gtk.Label()
        label.set_markup('<b>Earnings</b>')
        self.table.attach(label,0,1,5,6)
        chart = CategoryPie(self.account, self.start_date, self.end_date, earnings=True)
        self.charts.append(chart)
        self.table.attach(chart,0,1,6,7)

        label = gtk.Label()
        label.set_markup('<b>Spendings</b>')
        self.table.attach(label,1,2,5,6)
        chart = CategoryPie(self.account, self.start_date, self.end_date, earnings=False)
        self.table.attach(chart,1,2,6,7)
        self.charts.append(chart)
        self.show_all()

    def on_zoom_change(self, cb):
        zoom = self.zooms[cb.get_active()]
        if zoom != self.zoom:
            self.zoom = zoom
            self._calc_start_date()
            for chart in self.charts:
                chart.on_zoom_change(self.start_date)
            self.show_all()

    def on_step_change(self, cb):
        step = self.steps[cb.get_active()]
        if step != self.current_step:
            self.current_step = step
            for chart in self.charts:
                chart.on_step_change(step)
            self.show_all()

    def _calc_start_date(self):
        if self.zoom in MONTHS:
            self.start_date = self.end_date - relativedelta(months=MONTHS[self.zoom])
        elif self.zoom == 'ACT':
            self.start_date = date_utils.get_act_first()
        elif self.zoom == 'YTD':
            self.start_date = date_utils.get_ytd_first()
        elif self.zoom == 'all':
            self.start_date = self.account.birthday


class Chart(object):

    def on_zoom_change(self, start_date):
        self.start_date = start_date
        self.remove(self.chart)
        self._draw_chart()

    def on_step_change(self, step):
        pass

class BalanceChart(gtk.VBox, Chart):

    def __init__(self, account, start_date, end_date):
        gtk.VBox.__init__(self)
        self.account = account
        self.start_date = start_date
        self.end_date = end_date
        self._draw_chart()

    def _draw_chart(self):
        balance = self.account.get_balance_over_time(self.start_date)
        #ugly line of code
        #selects every 20. date for the legend
        legend = [gui_utils.get_date_string(balance[int(len(balance)/20 *i)][0]) for i in range(20)]

        plot = cairoplot.plots.DotLinePlot('gtk',
                                data=[item[1] for item in balance],
                                width=600,
                                height=300,
                                x_labels=legend,
                                y_formatter=gui_utils.get_currency_format_from_float,
                                y_title='Amount',
                                background="white light_gray",
                                grid=True,
                                dots=2,
                                series_colors=['blue','green'])
        self.chart = plot.handler
        self.pack_start(self.chart)


class EarningsVsSpendingsChart(gtk.VBox, Chart):

    def __init__(self, account, start_date, end_date, step='day'):
        gtk.VBox.__init__(self)
        self.account = account
        self.start_date = start_date
        self.end_date = end_date
        self.step = step
        hbox = gtk.HBox()
        markup = '<span weight="bold" color="blue">Earnings</span>'+' vs '+'<span weight="bold" color="darkgreen">Spendings</span>'
        label = gtk.Label()
        label.set_markup(markup)
        hbox.pack_start(label)
        self.type_cb = gtk.combo_box_new_text()
        for chart_type in ['bar chart', 'line chart']:
            self.type_cb.append_text(chart_type)
        self.type_cb.set_active(0)
        self.type_cb.connect('changed', self.on_type_change)
        hbox.pack_start(self.type_cb)

        self.pack_start(hbox)
        self._draw_chart()

    def on_type_change(self, widget):
        self.remove(self.chart)
        self._draw_chart()

    def on_step_change(self, step):
        self.step = step
        self.remove(self.chart)
        self._draw_chart()

    def _draw_chart(self):
        chart_type = self.type_cb.get_active_text()
        earnings = self.account.get_earnings_summed(self.end_date, self.start_date, self.step)
        spendings = self.account.get_spendings_summed(self.end_date, self.start_date, self.step)
        legend = get_legend(self.start_date, self.end_date, self.step)
        if chart_type == 'line chart':
            plot = cairoplot.plots.DotLinePlot('gtk',
                                data=[earnings, spendings],
                                width=600,
                                height=300,
                                x_labels=legend,
                                y_title='Amount',
                                y_formatter=gui_utils.get_currency_format_from_float,
                                background="white light_gray",
                                grid=True,
                                dots=2,
                                series_colors=['blue','green'],
                                dash=False)
        else:
            plot = cairoplot.plots.VerticalBarPlot('gtk',
                                data=[[earnings[i], spendings[i]] for i in range(len(earnings))],
                                width=600,
                                height=300,
                                #series_labels = ['earnings', 'spendings'],
                                x_labels=legend,
                                y_labels=['0', str(max(max(earnings),max(spendings)))],
                                #display_values=True,
                                #y_title='Amount',
                                background="white light_gray",
                                grid=True,
                                series_colors=['blue','green'],
                                )
        self.chart = plot.handler
        self.chart.show()
        self.pack_start(self.chart)


class CategoryPie(gtk.VBox, Chart):

    def __init__(self, account, start_date, end_date, earnings=True):
        gtk.VBox.__init__(self)
        self.account = account
        self.b_earnings = earnings
        self.start_date = start_date
        self.end_date = end_date
        self.category = None
        self._init_widgets()
        self._draw_chart()

    def _init_widgets(self):
        self.liststore = gtk.ListStore(object, str)
        combobox = gtk.ComboBox(self.liststore)
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 1)
        combobox.connect('changed', self.on_category_changed)
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Category')))
        hbox.pack_start(combobox)
        self.pack_start(hbox)

    def _draw_chart(self):
        self.liststore.clear()
        self.liststore.append([None, 'top level'])
        sums = self.account.get_sum_in_period_by_category(self.start_date,\
                          self.end_date, self.category, self.b_earnings)
        data = {}
        for cat, amount in sums.items():
            if type(cat) == str:
                name = cat
            else:
                name = cat.name
            if amount != 0:
                data[name] = amount
                if type(cat) != str:
                    self.liststore.append([cat, name])
        plot = cairoplot.plots.PiePlot('gtk',
                                data=data,
                                width=300,
                                height=300,
                                gradient=True,
                                shadow=False
                                )
        self.chart = plot.handler
        self.chart.show()
        self.pack_start(self.chart)

    def on_category_changed(self, combobox):
        active_iter = combobox.get_active_iter()
        if active_iter:
            self.category, name = self.liststore[active_iter]
            self.remove(self.chart)
            self._draw_chart()
