#!/usr/bin/env python

from stocktracker.cairoplot.gtkcairoplot \
    import gtk_pie_plot, gtk_vertical_bar_plot, gtk_dot_line_plot
import gtk
from stocktracker.objects import controller
import datetime
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
        self.zooms = ['1m', '3m', '6m', 'YTD', '1y','2y','5y']
        combobox = gtk.combo_box_new_text()
        for ch in self.zooms:
            combobox.append_text(ch)
        combobox.set_active(3)
        self.current_zoom = 'YTD'
        combobox.connect('changed', self.on_zoom_change)
        self.table.attach(combobox, 0,1,0,1)
        self.show_all()

    def show(self):
        #self.clear()
        self.table.attach(gtk.Label(_('Earnings vs. Spendings')), 0,2,1,2)
        self.table.attach(self.earningsvsspendings_chart(),0,2,2,3)
        self.show_all()

    def clear(self):
        for child in self.get_children():
            if isinstance(child, gtk.DrawingArea):
                self.remove(child)

    def _get_legend(self, bigger, smaller, step=1):
        erg = []
        delta = bigger - smaller
        while delta > datetime.timedelta(days =step):
            erg.append(smaller + delta)
            delta -= datetime.timedelta(days =step)
        return erg

    def earningsvsspendings_chart(self):
        today = datetime.date.today()
        month = 0
        if self.current_zoom in MONTHS:
            month = MONTHS[self.current_zoom]
        if month > 0:
            earnings = self.account.get_monthly_earnings(today, month=month)
            spendings = self.account.get_monthly_spendings(today, month=month)
            legend = self._get_legend(today, today - datetime.timedelta(days=30*month))
        elif  self.current_zoom == 'YTD':
            earnings = self.account.get_all_earnings()
            spendings = self.account.get_all_spendings()
            legend = self._get_legend(today, self.account.birthday())
        else:
            earnings = spendings = legend = []
        data = [earnings, spendings]

        chart = gtk_dot_line_plot()
        chart.set_args({'data':data,
                     'x_labels':legend,
                     'y_title': 'Amount',
                     'series_colors': ['blue','green'],
                     'grid': True,
                     'width':600,
                     'height':300,
                     })
        return chart

    def on_zoom_change(self, cb):
        zoom = self.zooms[cb.get_active()]
        if zoom != self.current_zoom:
            self.current_zoom = zoom
            self.show()
