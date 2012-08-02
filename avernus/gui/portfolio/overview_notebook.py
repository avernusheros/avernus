from gi.repository import Gtk
from gi.repository import Pango

from avernus.gui import gui_utils
from avernus.gui import charts
from avernus.controller import portfolio_controller
from avernus.controller import chart_controller


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

        pfvalue_chart_controller = chart_controller.AllPortfolioValueOverTime('monthly')
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

        pfinvestments_chart_controller = chart_controller.AllPortfolioInvestmentsOverTime('monthly')
        pfinvestments_chart = charts.SimpleLineChart(pfinvestments_chart_controller, width)
        table.attach(pfinvestments_chart, 0, 2, y, y + 1)
        combobox.connect('changed', self.on_zoom_change, pfinvestments_chart_controller, pfinvestments_chart)

        y += 1

        label = Gtk.Label()
        label.set_markup('<b>' + _('Market value') + '</b>')
        table.attach(label, 0, 1, y, y + 1)

        y += 1

        controller = chart_controller.PortfolioAttributeChartController('name')
        chart = charts.Pie(controller, width / 2)
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
    ANNUAL = 9
    PANGO_WEIGHT = 10

    def __init__(self, container):
        self.container = container
        gui_utils.Tree.__init__(self)
        self.set_model(Gtk.TreeStore(object, str, float, float, float, float, object, int, float, float, int))

        col, cell = self.create_column(_('Name'), self.NAME)
        cell.set_property('weight-set', True)
        col.add_attribute(cell, 'weight', self.PANGO_WEIGHT)
        col, cell = self.create_column(_('Current value'), self.VALUE, func=gui_utils.currency_format)
        cell.set_property('weight-set', True)
        col.add_attribute(cell, 'weight', self.PANGO_WEIGHT)
        col, cell = self.create_column(_('%'), self.PERCENT, func=gui_utils.percent_format)
        cell.set_property('weight-set', True)
        col.add_attribute(cell, 'weight', self.PANGO_WEIGHT)
        self.create_column(_('Last update'), self.LAST_UPDATE, func=gui_utils.date_to_string)
        col, cell = self.create_column(_('# positions'), self.COUNT)
        cell.set_property('weight-set', True)
        col.add_attribute(cell, 'weight', self.PANGO_WEIGHT)
        col, cell = self.create_column(_('Change'), self.CHANGE, func=gui_utils.float_to_red_green_string)
        cell.set_property('weight-set', True)
        col.add_attribute(cell, 'weight', self.PANGO_WEIGHT)
        col, cell = self.create_column(_('Change %'), self.CHANGE_PERCENT, func=gui_utils.float_to_red_green_string)
        cell.set_property('weight-set', True)
        col.add_attribute(cell, 'weight', self.PANGO_WEIGHT)
        col, cell = self.create_column(unichr(8709) + ' TER', self.TER, func=gui_utils.float_format)
        cell.set_property('weight-set', True)
        col.add_attribute(cell, 'weight', self.PANGO_WEIGHT)
        col, cell = self.create_column(_('Annual return'), self.ANNUAL, func=gui_utils.percent_format)
        cell.set_property('weight-set', True)
        col.add_attribute(cell, 'weight', self.PANGO_WEIGHT)

        self.set_rules_hint(True)
        self.load_items()
        self.expand_all()
        self.set_property("show-expanders", False)
        self.selected_item = None

    def on_update(self):
        self.container.update_positions()

    def load_items(self):
        model = self.get_model()
        all_portfolio = portfolio_controller.AllPortfolio()
        self.overall_value = portfolio_controller.get_current_value(all_portfolio)
        # ensure no division by zero error occurs
        if self.overall_value == 0.0:
            self.overall_value = 1.0
        iterator = model.append(None, self.get_row(all_portfolio, Pango.Weight.BOLD))
        for item in portfolio_controller.get_all_portfolio():
            model.append(iterator, self.get_row(item))

    def get_row(self, item, weight=Pango.Weight.NORMAL):
        return [item,
               item.name,
               portfolio_controller.get_current_value(item),
               portfolio_controller.get_current_change(item)[0],
               float(portfolio_controller.get_percent(item)),
               portfolio_controller.get_ter(item),
               item.last_update,
               len(item.positions),
               portfolio_controller.get_current_value(item) / self.overall_value,
               portfolio_controller.get_annual_return(item),
               weight]
