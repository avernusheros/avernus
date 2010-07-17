#!/usr/bin/env python

from stocktracker.cairoplot.gtkcairoplot \
    import gtk_pie_plot, gtk_vertical_bar_plot, gtk_dot_line_plot
import gtk
from stocktracker.objects import controller
no_data_string = '\nNo Data!\nAdd transactions first.\n\n'


class AccountChartTab(gtk.ScrolledWindow):

    def __init__(self, account):
        gtk.ScrolledWindow.__init__(self)
        self.account = account
        self.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        self.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        self.table = gtk.Table()
        self.add_with_viewport(self.table)
        self.zooms = ['1m', '3m', '6m', 'YTD', '1y','2y','5y','10y', '20y']
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

    def _get_legend_weekly(self, date1, date2):
        timedelta = datetime.timedelta(days=7)

    def earningsvsspendings_chart(self):
        if self.current_zoom in ['1m']:
            earnings = self.account.get_weekly_earnings(date1, date2)
            spendings = self.account.get_weekly_spendings(date1, date2)
            legend = self._get_legend_weekly(date1, date2)
        elif self.current_zoom in ['3m', '6m', 'YTD', '1y']:
            earnings = self.account.get_monthly_earnings(date1, date2)
            spendings = self.account.get_monthly_spendings(date1, date2)
            legend = self._get_legend_monthly(date1, date2)
        elif self.current_zoom in ['2y','5y','10y', '20y']:
            earnings = self.account.get_yearly_earnings(date1, date2)
            spendings = self.account.get_yearly_spendings(date1, date2)
            legend = self._get_legend_yearly(date1, date2)
            
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
