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
    #fixme i think 3m should display this month and the last two etc
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

        earnings = chart.account.get_earnings(end_date, start_date, step)
        spendings = chart.account.get_spendings(end_date, start_date, step)
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
