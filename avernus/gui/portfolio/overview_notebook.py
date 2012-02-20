from gi.repository import Gtk
from avernus.gui import gui_utils
from avernus import pubsub
from avernus.controller import portfolio_controller as pfctlr
from avernus.controller import chartController
from avernus.gui import charts


class OverviewNotebook(Gtk.Notebook):

    def __init__(self, portfolio):
        Gtk.Notebook.__init__(self)
        tree = PortfolioOverviewTree(portfolio)
        self.append_page(tree, Gtk.Label(label=_('Overview')))
        self.append_page(OverviewCharts(), Gtk.Label(label=_('Charts')))

        self.connect('switch-page', self.on_notebook_selection)
        self.on_notebook_selection(self, tree, 0)
        self.set_current_page(0)
        self.show_all()

    def on_notebook_selection(self, notebook, page, page_num):
        page.show()


class OverviewCharts(Gtk.ScrolledWindow):

    def __init__(self):
        Gtk.ScrolledWindow.__init__(self)
        self.set_property('hscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        self.set_property('vscrollbar-policy', Gtk.PolicyType.AUTOMATIC)
        self.show_all()

    def show(self):
        width = self.get_allocation().width
        self.clear()
        table = Gtk.Table()
        y = 0

        #value over time chart
        hbox = Gtk.HBox()
        table.attach(hbox, 0, 2, y, y + 1)
        label = Gtk.Label()
        label.set_markup('<b>' + _('Portfolio value over time') + '</b>')
        label.set_tooltip_text(_("This chart plots the portfolio value over the selected time period."))
        hbox.pack_start(label, True, True, 0)

        combobox = Gtk.ComboBoxText()
        for st in ['daily', 'weekly', 'monthly', 'yearly']:
            combobox.append_text(st)
        combobox.set_active(2)

        hbox.pack_start(combobox, False, False, 0)

        y += 1

        pfvalue_chart_controller = chartController.AllPortfolioValueOverTime('monthly')
        pfvalue_chart = charts.SimpleLineChart(pfvalue_chart_controller, width)
        table.attach(pfvalue_chart, 0, 2, y, y + 1)
        combobox.connect('changed', self.on_zoom_change, pfvalue_chart_controller, pfvalue_chart)

        y += 1
        #investments over time chart
        hbox = Gtk.HBox()
        table.attach(hbox, 0, 2, y, y + 1)
        label = Gtk.Label()
        label.set_markup('<b>' + _('Investments over time') + '</b>')
        label.set_tooltip_text(_("This chart plots the investments over time."))
        hbox.pack_start(label, True, True, 0)

        combobox = Gtk.ComboBoxText()
        for st in ['daily', 'weekly', 'monthly', 'yearly']:
            combobox.append_text(st)
        combobox.set_active(2)

        hbox.pack_start(combobox, False, False, 0)

        y += 1

        pfinvestments_chart_controller = chartController.AllPortfolioInvestmentsOverTime('monthly')
        pfinvestments_chart = charts.SimpleLineChart(pfinvestments_chart_controller, width)
        table.attach(pfinvestments_chart, 0, 2, y, y + 1)
        combobox.connect('changed', self.on_zoom_change, pfinvestments_chart_controller, pfinvestments_chart)

        y += 1

        label = Gtk.Label()
        label.set_markup('<b>' + _('Market value') + '</b>')
        #FIXME label.set_tooltip_text(_(""))
        table.attach(label, 0, 1, y, y + 1)

        y += 1

        chart_controller = chartController.PortfolioAttributeChartController('name')
        chart = charts.Pie(chart_controller, width / 2)
        table.attach(chart, 0, 1, y, y + 1)

        self.add_with_viewport(table)
        self.show_all()

    def clear(self):
        for child in self.get_children():
            self.remove(child)

    def on_zoom_change(self, combobox, controller, chart):
        value = combobox.get_model()[combobox.get_active()][0]
        controller.step = value
        chart.update()


class PortfolioOverviewTree(gui_utils.Tree):

    OBJ = 0
    NAME = 1
    VALUE = 2
    CHANGE = 3
    CHANGE_PERCENT = 4
    TER = 5
    LAST_UPDATE = 6
    COUNT = 7
    PERCENT = 8

    def __init__(self, container):
        self.container = container
        gui_utils.Tree.__init__(self)
        self.set_model(Gtk.ListStore(object, str, float, float, float, float, object, int, float))

        self.create_column(_('Name'), self.NAME)
        self.create_column(_('Current value'), self.VALUE, func=gui_utils.currency_format)
        self.create_column(_('%'), self.PERCENT, func=gui_utils.percent_format)
        self.create_column(_('Last update'), self.LAST_UPDATE, func=gui_utils.date_to_string)
        self.create_column(_('# positions'), self.COUNT)
        col, cell = self.create_column(_('Change'), self.CHANGE, func=gui_utils.float_to_red_green_string)
        col, cell = self.create_column(_('Change %'), self.CHANGE_PERCENT, func=gui_utils.float_to_red_green_string)
        col, cell = self.create_column(unichr(8709) + ' TER', self.TER, func=gui_utils.float_format)

        self.set_rules_hint(True)
        self.load_items()
        self.connect("destroy", self.on_destroy)
        self.connect("row-activated", self.on_row_activated)
        self.subscriptions = (
            ('stocks.updated', self.on_stocks_updated),
            ('shortcut.update', self.on_update)
        )
        for topic, callback in self.subscriptions:
            pubsub.subscribe(topic, callback)

        self.selected_item = None

    def on_update(self):
        self.container.update_positions()

    def on_row_activated(self, treeview, path, view_column):
        item = self.get_model()[path][0]
        pubsub.publish('overview.item.selected', item)

    def on_destroy(self, x):
        for topic, callback in self.subscriptions:
            pubsub.unsubscribe(topic, callback)

    def load_items(self):
        items = []
        if self.container.name == 'Watchlists':
            items = pfctlr.getAllWatchlist()
        elif self.container.name == 'Portfolios':
            items = pfctlr.getAllPortfolio()
        self.overall_value = sum([i.cvalue for i in items])
        if self.overall_value == 0.0:
            self.overall_value = 1
        for item in items:
            self.insert_item(item)

    def on_stocks_updated(self, container):
        if container.id == self.container.id:
            for row in self.get_model():
                item = row[0]
                row[self.VALUE] = item.cvalue
                row[self.LAST_UPDATE] = item.last_update
                row[self.CHANGE] = item.change
                row[self.CHANGE_PERCENT] = item.percent
                row[self.TER] = item.ter

    def insert_item(self, item):
        self.get_model().append([item,
                               item.name,
                               item.cvalue,
                               item.change,
                               float(item.percent),
                               item.ter,
                               item.last_update,
                               len(item),
                               100 * item.cvalue / self.overall_value])
