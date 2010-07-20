#!/usr/bin/env python

from stocktracker.cairoplot.gtkcairoplot \
    import gtk_pie_plot, gtk_vertical_bar_plot, gtk_dot_line_plot

import datetime
from dateutil.relativedelta import relativedelta
from stocktracker import date_utils

MONTHS = {
                        '1m':1,
                        '3m':3,
                        '6m':6,
                        '1y':12,
                        '2y':24,
                        '5y':60,
}

def _get_start_date(end_date, zoom):
    if zoom in MONTHS:
        return end_date - relativedelta(months=MONTHS[zoom])
    elif zoom == 'ACT':
        return date_utils.get_act_first()
    elif zoom == 'YTD':
        return date_utils.get_ytd_first()
    elif zoom == 'all':
        return self.account.birthday()

def _get_legend(bigger, smaller, step):
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

class AccountChart:

    def __init__(self, account):
        self.account = account
        self.chart = None

    @classmethod
    def getEarningsSpendingsChart(cls, account, zoom='ACT', step='day'):
        chart = cls(account)
        chart.chart = gtk_dot_line_plot()
        end_date = datetime.date.today()
        start_date = _get_start_date(end_date, zoom)

        earnings = chart.account.get_earnings_summed(end_date, start_date, step)
        spendings = chart.account.get_earnings_summed(end_date, start_date, step)
        legend = _get_legend(end_date, start_date, step)
        chart.chart.set_args({'data':[earnings, spendings],
                     'x_labels':legend,
                     'y_title': 'Amount',
                     'series_colors': ['blue','green'],
                     'grid': True,
                     'dots': True,
                     'width':600,
                     'height':300,
                     })
        return chart.chart

    @classmethod
    def get_balance_chart(self, account, zoom):
        chart = self(account)
        end_date = datetime.date.today()
        start_date = _get_start_date(end_date, zoom)
        balance = account.get_balance_over_time(start_date)
        #ugly line of code
        #selects every 20. date for the legend
        legend = [str(balance[int(len(balance)/20 *i)][0]) for i in range(20)]
        
        chart.chart = gtk_dot_line_plot()
        chart.chart.set_args({'data': [item[1] for item in balance],
                     'x_labels':legend,
                     'y_title': 'Amount',
                     'series_colors': ['blue','green'],
                     'grid': True,
                     'dots': True,
                     'width':600,
                     'height':300,
                     })
        return chart.chart

    @classmethod
    def get_category_pie(self, account, zoom, earnings=True):
        chart = self(account)
        end_date = datetime.date.today()
        start_date = _get_start_date(end_date, zoom)
        if earnings:
            trans = account.yield_earnings_in_period(start_date, end_date)
        else:
            trans = account.yield_spendings_in_period(start_date, end_date)
        buckets =  {}
        for t in trans:
            if t.category.name in buckets: 
                buckets[t.category.name] += t.amount
            else:
                buckets[t.category.name] = t.amount
        chart.chart = gtk_pie_plot()
        print buckets   
        chart.chart.set_args({'data':buckets, 'width':300, 'height':300, 'gradient':True, 'shadow':False})
        return chart.chart
