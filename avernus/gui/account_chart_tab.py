#!/usr/bin/env python

from avernus import cairoplot
import gtk
from avernus.controller import controller
import datetime
from avernus import date_utils
from avernus.gui import gui_utils, page
from dateutil.relativedelta import relativedelta
import dateutil.rrule as rrule
from avernus.controller import chartController

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
    if step == 'monthly':
        delta = relativedelta(months=+1)
        formatstring = "%b %y"
    elif step == 'yearly':
        delta = relativedelta(years=+1)
        formatstring = "%Y"
    elif step == 'daily':
        delta = relativedelta(days=+1)
        formatstring = "%x"
    elif step == 'weekly':
        delta = relativedelta(weeks=+1)
        formatstring = "%U"
    while smaller <= bigger:
        erg.append(smaller.strftime(formatstring))
        smaller+=delta
    return erg


class AccountChartTab(gtk.VBox, page.Page):

    TABLE_SPACINGS = 5

    def __init__(self, account):
        gtk.VBox.__init__(self)
        self.account = account
        
        self.zooms = ['ACT','1m', '3m', '6m', 'YTD', '1y','2y','5y', 'all']
        self.show_all()
        
        
    def clear(self):
        for child in self.get_children():
            self.remove(child)

    def show(self):
        self.clear()
        sw = gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        self.table = gtk.Table()
        self.table.set_col_spacings(self.TABLE_SPACINGS)
        self.table.set_row_spacings(self.TABLE_SPACINGS)

        sw.add_with_viewport(self.table)
        self.pack_end(sw)
        hbox = gtk.HBox()
        self.pack_start(hbox, expand = False)
        width = self.allocation[2]
        combobox = gtk.combo_box_new_text()
        for ch in self.zooms:
            combobox.append_text(ch)
        combobox.set_active(4)
        self.zoom = 'YTD'
        self.end_date = datetime.date.today()
        self._calc_start_date()
        combobox.connect('changed', self.on_zoom_change)
        hbox.pack_start(combobox)

        #FIXME macht das step einstellen wirklich sinn? alternative ist automatische einstellung
        #oder manuelle einstellung erlauben, aber sachen vorgeben, zb 1y und month
        self.steps = ['daily','weekly','monthly','yearly']
        active = 2
        combobox = gtk.combo_box_new_text()
        for st in self.steps:
            combobox.append_text(st)
        combobox.set_active(active)
        self.current_step = self.steps[active]
        combobox.connect('changed', self.on_step_change)
        hbox.pack_start(combobox)

        self.charts = []
        
        y = 0
        
        #chart = TransactionsChart(width, self.account, self.start_date, self.end_date, self.current_step)
        #self.charts.append(chart)
        chart = chartController.TransactionValueOverTimeChartController([t for t in self.account])
        self.table.attach(SimpleLineChart(chart,width),0,2,y,y+1)
        y += 1

        label = gtk.Label()
        label.set_markup('<b>Balance over time</b>')
        self.table.attach(label, 0,2,y,y+1)
        chart = BalanceChart(width, self.account, self.start_date, self.end_date)
        self.charts.append(chart)
        self.table.attach(chart,0,2,y+1,y+2)
        y += 2

        label = gtk.Label()
        label.set_markup('<b>Earnings</b>')
        self.table.attach(label,0,1,y,y+1)
        chart = CategoryPie(width/2, self.account, self.start_date, self.end_date, earnings=True)
        self.charts.append(chart)
        self.table.attach(chart,0,1,y+1,y+2)
        

        label = gtk.Label()
        label.set_markup('<b>Spendings</b>')
        self.table.attach(label,1,2,y,y+1)
        chart = CategoryPie(width/2, self.account, self.start_date, self.end_date, earnings=False)
        self.table.attach(chart,1,2,y+1,y+2)
        self.charts.append(chart)
        y += 2
        
        self.update_page()
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
            
class SimpleLineChart(gtk.VBox):
    
    def __init__(self, chartController, width):
        gtk.VBox.__init__(self)
        self.controller = chartController
        self.width = width
        self.draw_chart()
        
    def draw_chart(self):
        plot = cairoplot.plots.DotLinePlot('gtk',
                                data=self.controller.y_values,
                                width=self.width,
                                height=300,
                                x_labels=self.controller.legend,
                                y_formatter=gui_utils.get_currency_format_from_float,
                                y_title='Amount',
                                background="white light_gray",
                                grid=True,
                                dots=2,
                                series_colors=['blue','green'])
        self.chart = plot.handler
        self.pack_start(self.chart)

class Chart(object):

    def __init__(self, width, account, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date
        self.width = width
        self.account = account
        self._draw_chart()

    def on_zoom_change(self, start_date):
        self.start_date = start_date
        self.remove(self.chart)
        self._draw_chart()

    def on_step_change(self, step):
        pass


class BalanceChart(gtk.VBox, Chart):

    def __init__(self, width, account, start_date, end_date):
        gtk.VBox.__init__(self)
        Chart.__init__(self, width, account, start_date, end_date)

    def _draw_chart(self):
        balance = self.account.get_balance_over_time(self.start_date)
        #ugly line of code
        #selects every 20. date for the legend
        #legend = [gui_utils.get_date_string(balance[int(len(balance)/20 *i)][0]) for i in range(20)]
        legend = [gui_utils.get_date_string(balance[i][0]) for i in range(0,len(balance))]
        plot = cairoplot.plots.DotLinePlot('gtk',
                                data=[item[1] for item in balance],
                                width=self.width,
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
        

class TransactionsChart(gtk.VBox, Chart):

    def __init__(self, width, account, start_date, end_date, step='day'):
        gtk.VBox.__init__(self)
        self.step = step
        hbox = gtk.HBox()
        self.type_cb = gtk.combo_box_new_text()
        for chart_type in ['Earnings vs Spendings', 'Transactions Summed']:
            self.type_cb.append_text(chart_type)
        self.type_cb.set_active(0)
        self.type_cb.connect('changed', self.on_change)
        hbox.pack_start(self.type_cb)
        
        liststore = gtk.ListStore(object, str)
        self.category_cb = gtk.ComboBox(liststore)
        cell = gtk.CellRendererText()
        self.category_cb.pack_start(cell, True)
        self.category_cb.add_attribute(cell, 'text', 1)
        liststore.append([None, _('All')])
        for category in sorted(controller.getAllAccountCategories()):
            liststore.append([category, category.name])
        self.category_cb.set_active(0)
        self.category_cb.connect('changed', self.on_change)
        hbox.pack_start(self.category_cb)
        
        self.style_cb = gtk.combo_box_new_text()
        for chart_style in ['bar chart', 'line chart']:
            self.style_cb.append_text(chart_style)
        self.style_cb.set_active(0)
        self.style_cb.connect('changed', self.on_change)
        hbox.pack_start(self.style_cb)

        self.pack_start(hbox)
        Chart.__init__(self, width, account, start_date, end_date)
    
    def on_change(self, widget=None):
        self.remove(self.chart)
        self._draw_chart()

    def on_step_change(self, step):
        self.step = step
        self.on_change()

    def _draw_chart(self):
        chart_type = self.type_cb.get_active_text()
        if chart_type == 'Earnings vs Spendings':
            self._draw_chart1()
        else:
            self._draw_chart2()
        self.chart.show()
        self.pack_start(self.chart)

    def _draw_chart1(self):
        chart_style = self.style_cb.get_active_text()
        earnings = self.account.get_earnings_summed(self.end_date, self.start_date, self.step)
        spendings = self.account.get_spendings_summed(self.end_date, self.start_date, self.step)
        legend = get_legend(self.start_date, self.end_date, self.step)
        if chart_style == 'line chart':
            plot = cairoplot.plots.DotLinePlot('gtk',
                                data=[earnings, spendings],
                                width=self.width,
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
                                width=self.width,
                                height=300,
                                series_labels = ['earnings', 'spendings'],
                                x_labels=legend,
                                y_labels=['0', str(max(max(earnings),max(spendings)))],
                                #display_values=True,
                                #y_title='Amount',
                                background="white light_gray",
                                grid=True,
                                series_colors=['blue','green'],
                                )
        self.chart = plot.handler
    
    def _draw_chart2(self):
        chart_style = self.style_cb.get_active_text()
        active_category = self.category_cb.get_model()[self.category_cb.get_active()][0]
        transactions = self.account.get_transactions_in_period(self.start_date, self.end_date)
        transactions = filter(lambda trans:trans.category == active_category, transactions) 
        time_points = list(rrule.rrule(rrule.MONTHLY, dtstart = self.start_date, until = self.end_date, bymonthday=1))
        legend = [d.strftime("%b %y") for d in time_points]
        sums = {}
        for tp in time_points:
            sums[tp] = 0
        for trans in transactions:
            for start,end in controller.pairwise(time_points):
                if start.date() < trans.date and end.date() >= trans.date:
                    sums[start] += trans.amount
                    break
            if trans.date > time_points[-1].date():
                sums[time_points[-1]] += trans.amount
        data = [sums[d] for d in time_points]
        display = {'actual':data}
        colors = ['blue']
        if len(data)>10:
            avgs = []
            avgs.append(data[0])
            avgs.append((data[0] + data[1])/2)
            for i in range(2,len(data)):
                avgs.append((data[i]+data[i-1]+data[i-2])/3)
            display['3 floating average'] = avgs
            colors.insert(0,'yellow')
        if chart_style == 'line chart':
            plot = cairoplot.plots.DotLinePlot('gtk',
                            data=display,
                            width=self.width,
                            height=300,
                            x_labels=legend,
                            y_formatter=gui_utils.get_currency_format_from_float,
                            background="white light_gray",
                            grid=True,
                            dots=2,
                            series_colors=colors,
                            series_legend =True,
                            dash=False)
        else:
            labels = data
            #WHY?
            data.append(0)
            plot = cairoplot.plots.VerticalBarPlot('gtk',
                            data=[data],
                            width=self.width,
                            height=300,
                            #series_labels = ['earnings', 'spendings'],
                            x_labels=legend,
                            y_labels=[str(min(labels)), str(max(labels))],
                            display_values=True,
                            grid=True,
                            series_colors=['blue' for i in range(len(data))],
                            )
        self.chart = plot.handler


class CategoryPie(gtk.VBox, Chart):

    def __init__(self, width, account, start_date, end_date, earnings=True):
        gtk.VBox.__init__(self)
        self.b_earnings = earnings
        self.category = None
        self._init_widgets()
        Chart.__init__(self, width, account, start_date, end_date)

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
                                width=self.width,
                                height=300,
                                gradient=True,
                                shadow=False,
                                values=True
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
