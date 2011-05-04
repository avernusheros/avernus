import gtk
from avernus.gui.positions_tab import PositionsTab
from avernus.gui.transactions_tab import TransactionsTab
from avernus.gui.dividends_tab import DividendsTab
from avernus.gui.closed_positions_tab import ClosedPositionsTab
from avernus.gui.chart_tab import ChartTab


class PortfolioNotebook(gtk.Notebook):

    def __init__(self, portfolio):
        gtk.Notebook.__init__(self)
        self.append_page(PositionsTab(portfolio), gtk.Label('Positions'))
        self.append_page(TransactionsTab(portfolio), gtk.Label('Transactions'))
        self.append_page(DividendsTab(portfolio), gtk.Label('Dividends'))
        self.append_page(ClosedPositionsTab(portfolio), gtk.Label('Closed positions'))
        self.append_page(ChartTab(portfolio), gtk.Label('Charts'))

        self.connect('switch-page', self.on_notebook_selection)
        self.show_all()

    def on_notebook_selection(self, notebook, page, page_num):
        notebook.get_nth_page(page_num).show()
