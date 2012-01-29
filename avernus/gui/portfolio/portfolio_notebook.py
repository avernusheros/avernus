from gi.repository import Gtk
from avernus.gui.portfolio.positions_tab import PositionsTab
from avernus.gui.portfolio.transactions_tab import TransactionsTab
from avernus.gui.portfolio.dividends_tab import DividendsTab
from avernus.gui.portfolio.closed_positions_tab import ClosedPositionsTab
from avernus.gui.portfolio.chart_tab import ChartTab


class PortfolioNotebook(Gtk.Notebook):

    def __init__(self, portfolio):
        Gtk.Notebook.__init__(self)
        self.append_page(PositionsTab(portfolio), Gtk.Label(label='Positions'))
        self.append_page(TransactionsTab(portfolio), Gtk.Label(label='Transactions'))
        self.append_page(DividendsTab(portfolio), Gtk.Label(label='Dividends'))
        self.append_page(ClosedPositionsTab(portfolio), Gtk.Label(label='Closed positions'))
        self.append_page(ChartTab(portfolio), Gtk.Label(label='Charts'))

        self.connect('switch-page', self.on_notebook_selection)
        self.show_all()
        self.on_notebook_selection(self, 0, 0)

    def on_notebook_selection(self, notebook, page, page_num):
        notebook.get_nth_page(page_num).show()
