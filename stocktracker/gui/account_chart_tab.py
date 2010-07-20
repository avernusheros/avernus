#!/usr/bin/env python

from stocktracker.cairoplot.gtkcairoplot \
    import gtk_pie_plot, gtk_vertical_bar_plot, gtk_dot_line_plot
import gtk
from stocktracker.objects import controller
import datetime
from dateutil.relativedelta import relativedelta
from stocktracker import date_utils

no_data_string = '\nNo Data!\nAdd transactions first.\n\n'

MONTHS = {
                        '1m':1,
                        '3m':3,
                        '6m':6,
                        '1y':12,
                        '2y':24,
                        '5y':60,
}


class AccountChartTab(gtk.ScrolledWindow):

    def __init__(self, account):
        gtk.ScrolledWindow.__init__(self)
        self.account = account
        self.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        self.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        self.table = gtk.Table()
        self.add_with_viewport(self.table)
        self.zooms = ['ACT','1m', '3m', '6m', 'YTD', '1y','2y','5y', 'all']
        combobox = gtk.combo_box_new_text()
        for ch in self.zooms:
            combobox.append_text(ch)
        combobox.set_active(4)
        self.current_zoom = 'YTD'
        combobox.connect('changed', self.on_zoom_change)
        self.table.attach(combobox, 0,1,0,1)
        #FIXME macht das step einstellen wirklich sinn? alternative ist automatische einstellung 
        #oder manuelle einstellung erlauben, aber sachen vorgeben, zb 1y und month
        self.steps = ['day','week','month','year']
        combobox = gtk.combo_box_new_text()
        for st in self.steps:
            combobox.append_text(st)
        combobox.set_active(0)
        self.current_step = 'day'
        combobox.connect('changed', self.on_step_change)
        self.table.attach(combobox,1,2,0,1)
        markup = '<span weight="bold" color="blue">Earnings</span>'+' vs '+'<span weight="bold" color="darkgreen">Spendings</span>' 
        label = gtk.Label()
        label.set_markup(markup)
        self.table.attach(label, 0,2,1,2)
        self.table.attach(gtk.Label('Balace over time'), 0,2,3,4)
        self.show_all()

    def show(self):
        self.table.attach(self.earningsvsspendings_chart(),0,2,2,3)
        self.table.attach(self.balance_chart(),0,2,4,5)
        self.show_all()

    def _get_legend(self, bigger, smaller):
        erg = []
        if self.current_step == 'month':
            delta = relativedelta(months=+1)
            formatstring = "%b %y"
        elif self.current_step == 'year':
            delta = relativedelta(years=+1)
            formatstring = "%Y"
        elif self.current_step == 'day':
            delta = relativedelta(days=+1)
            formatstring = "%x"
        elif self.current_step == 'week':
            delta = relativedelta(weeks=+1)
            formatstring = "%U"
        
        while smaller <= bigger:
            erg.append(smaller.strftime(formatstring))
            smaller+=delta
        return erg
    
    def _get_start_date(self, end_date):
        if self.current_zoom in MONTHS:
            return end_date - relativedelta(months=MONTHS[self.current_zoom])
        elif self.current_zoom == 'ACT':
            return date_utils.get_act_first()
        elif self.current_zoom == 'YTD':
            return date_utils.get_ytd_first()
        elif self.current_zoom == 'all':
            return self.account.birthday()

    def earningsvsspendings_chart(self):
        end_date = datetime.date.today()
        start_date = self._get_start_date(end_date)
        
        earnings = self.account.get_earnings(end_date, start_date, self.current_step)
        spendings = self.account.get_spendings(end_date, start_date, self.current_step)
        legend = self._get_legend(end_date, start_date)
        #FIXME earnings, spendings, legend do not always have the same length
        chart = gtk_dot_line_plot()
        chart.set_args({'data':[earnings, spendings],
                     'x_labels':legend,
                     'y_title': 'Amount',
                     'series_colors': ['blue','green'],
                     'grid': True,
                     'dots': True,
                     'width':600,
                     'height':300,
                     })
        return chart
    
    def balance_chart(self):
        end_date = datetime.date.today()
        start_date = self._get_start_date(end_date)
        balance = self.account.get_balance_over_time(start_date)
        #ugly line of code
        #selects every 20. date for the legend
        legend = [str(balance[int(len(balance)/20 *i)][0]) for i in range(20)]
        
        chart = gtk_dot_line_plot()
        chart.set_args({'data': [item[1] for item in balance],
                     'x_labels':legend,
                     'y_title': 'Amount',
                     'series_colors': ['blue','green'],
                     'grid': True,
                     'dots': True,
                     'width':600,
                     'height':300,
                     })
        return chart

    def on_zoom_change(self, cb):
        zoom = self.zooms[cb.get_active()]
        if zoom != self.current_zoom:
            self.current_zoom = zoom
            self.show()

    def on_step_change(self, cb):
        step = self.steps[cb.get_active()]
        if step != self.current_step:
            self.current_step = step
            self.show()
