#!/usr/bin/env python

from stocktracker.cairoplot.gtkcairoplot \
    import gtk_pie_plot, gtk_vertical_bar_plot, gtk_dot_line_plot
import gtk
from stocktracker.objects import controller
import chart

no_data_string = '\nNo Data!\nAdd transactions first.\n\n'


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
        self.table.attach(gtk.Label('Spendings'), 0,1,5,6)
        self.table.attach(gtk.Label('Earnings'), 1,2,5,6)
        self.show_all()

    def show(self):
        self.table.attach(chart.AccountChart.getEarningsSpendingsChart(self.account, self.current_zoom, self.current_step),0,2,2,3)
        self.table.attach(chart.AccountChart.get_balance_chart(self.account, self.current_zoom),0,2,4,5)
        self.table.attach(chart.AccountChart.get_category_pie(self.account, self.current_zoom, earnings=False),0,1,6,7)
        self.table.attach(chart.AccountChart.get_category_pie(self.account, self.current_zoom, earnings=True),1,2,6,7)
        self.show_all()
    
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
