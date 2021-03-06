#!/usr/bin/env python
from avernus import config
from avernus.controller import datasource_controller, categorization_controller
from avernus.gui import progress_manager, threads, get_avernus_builder
from avernus.gui.account.account_overview import AccountOverview
from avernus.gui.account.account_transactions_tab import AccountTransactionTab
from avernus.gui.account.categorization_dialog import CategorizationRulesDialog
from avernus.gui.account.csv_import_dialog import CSVImportDialog
from avernus.gui.account.exportDialog import ExportDialog
from avernus.gui import sidebar
from avernus.gui.portfolio.asset_manager import AssetManager
from avernus.gui.portfolio.overview_notebook import OverviewNotebook
from avernus.gui.portfolio.positions_tab import PortfolioPositionsTab
from avernus.gui.portfolio.transactions_tab import TransactionsTab
from avernus.gui.portfolio.dividends_tab import DividendsTab
from avernus.gui.portfolio.closed_positions_tab import ClosedPositionsTab
from avernus.gui.portfolio.chart_tab import ChartTab
from avernus.gui.portfolio import watchlist_positions_page
from avernus.gui.portfolio import asset_allocation
# from avernus.gui.portfolio.positions_tab import WatchlistPositionsTab
from avernus.gui.preferences import PrefDialog
from avernus.objects import db
from gi.repository import Gdk, Gtk
from webbrowser import open as web 
import avernus
import sys
import logging

logger = logging.getLogger(__name__)

# hack to switch from ascii to utf8. can be removed once we switch to python3
reload(sys)
sys.setdefaultencoding("utf-8")



class HandlerFinder(object):
    """Searches for handler implementations across multiple objects.
    """
    # http://stackoverflow.com/questions/4637792/pygtk-gtk-builder-connect-signals-onto-multiple-objects

    def __init__(self, objects):
        self.objects = objects

    def __getattr__(self, name):
        for o in self.objects:
            if hasattr(o, name):
                return getattr(o, name)
        else:
            raise AttributeError("%r not found on any of %r"
                % (name, self.objects))


class MainWindow:

    def __init__(self):
        builder = get_avernus_builder()
        self.window = builder.get_object("main_window")

        self.config = config.avernusConfig()
        self.window.set_title(avernus.__appname__)

        sb = sidebar.Sidebar()
        self.hpaned = builder.get_object("hpaned")
        self.account_page = AccountTransactionTab()
        self.portfolio_notebook = builder.get_object("portfolio_notebook")
        self.portfolio_pages = [PortfolioPositionsTab(),
                                TransactionsTab(),
                                DividendsTab(),
                                ClosedPositionsTab(),
                                ChartTab()
                                ]
        self.watchlist_page = watchlist_positions_page.WatchlistPositionsPage()
        self.asset_allocation_page = asset_allocation.AssetAllocation()
        sb.insert_report('asset allocation', _("Asset allocation"))
        sb.tree.expand_all()

        sb.connect("unselect", self.on_sidebar_unselect)
        sb.connect("select", self.on_sidebar_select)

        # connect signals
        handlers = [self, self.account_page, sb, self.watchlist_page, self.asset_allocation_page]
        handlers.extend(self.portfolio_pages)
        builder.connect_signals(HandlerFinder(handlers))

        # set min size
        screen = self.window.get_screen()
        width = int(screen.get_width() * 0.66)
        height = int(screen.get_height() * 0.66)
        self.window.set_size_request(width, height)

        size = self.config.get_option('size', section='Gui')
        if size is not None:
            width, height = eval(size)
            self.window.resize(width, height)

        pos = self.config.get_option('hpaned position', 'Gui') or width * 0.25
        self.hpaned.set_position(int(pos))

        # config entries are strings...
        if self.config.get_option('maximize', section='Gui') == 'True':
            self.window.maximize()
            self.maximized = True
        else:
            self.maximized = False

        # display everything
        self.window.show_all()

    def on_window_size_allocate(self, widget, allocation):
        if not self.maximized:
            self.config.set_option('size', self.window.get_size(), 'Gui')

    def on_window_state_event(self, widget, event):
        if event.new_window_state == Gdk.WindowState.MAXIMIZED:
            self.maximized = True
            self.config.set_option('maximize', True, section='Gui')
        else:
            self.maximized = False
            self.config.set_option('maximize', False, section='Gui')

    def on_destroy(self, widget=None, data=None):
        """on_destroy - called when the avernusWindow is closed. """
        db.close_session()
        # save db on quit
        self.config.set_option('hpaned position', self.hpaned.get_position(), 'Gui')
        threads.terminate_all()
        Gtk.main_quit()

    def on_sidebar_select(self, caller=None, item=None):
        self.on_sidebar_unselect()
        if isinstance(item, str):
            page = item
        else:
            page = item.__class__.__name__
        if page == "Account" or page == "AllAccount":
            self.hpaned.pack2(self.account_page.widget)
            self.account_page.widget.show()
            self.account_page.set_account(item)
        elif page == "Portfolio" or page == "AllPortfolio":
            self.hpaned.pack2(self.portfolio_notebook)
            for page in self.portfolio_pages:
                page.set_portfolio(item)
            self.portfolio_notebook.set_current_page(0)
        elif page == "Watchlist":
            self.hpaned.pack2(self.watchlist_page.widget)
            self.watchlist_page.set_watchlist(item)
        elif page == "asset allocation":
            self.hpaned.pack2(self.asset_allocation_page.widget)
            self.asset_allocation_page.load_categories()
        elif page == 'Category Accounts':
            self.hpaned.pack2(AccountOverview())
        elif page == "Category Portfolios":
            self.hpaned.pack2(OverviewNotebook())
        elif page is not None:
            logger.debug("Sidebar select unknown page " + page)

    def on_sidebar_unselect(self, caller=None):
        page = self.hpaned.get_child2()
        if page:
            self.hpaned.remove(page)
            try:
                page.close()
            except:
                pass

    def on_prefs(self, *args):
        PrefDialog(parent=self.window)

    def on_categorization_rules(self, *args):
        CategorizationRulesDialog(parent=self.window)

    def on_asset_manager(self, *args):
        AssetManager(parent=self.window)

    def on_import(self, *args):
        CSVImportDialog(parent=self.window)

    def on_about(self, *args):
        dialog = Gtk.AboutDialog(parent=self.window)
        dialog.set_name(avernus.__appname__)
        dialog.set_version(avernus.__version__)
        dialog.set_copyright(avernus.__copyright__)
        dialog.set_comments(avernus.__description__)
        dialog.set_license(avernus.__license__)
        dialog.set_authors(avernus.__authors__)
        dialog.set_website(avernus.__url__)
        dialog.set_logo_icon_name('avernus')
        dialog.run()
        dialog.hide()

    def on_help(self, *args):
        # unused
        web("https://answers.launchpad.net/avernus")

    def on_website(self, *args):
        web("https://github.com/avernusheros/avernus")

    def on_feature(self, *args):
        web("https://github.com/avernusheros/avernus/issues")

    def on_bug(self, *args):
        web("https://github.com/avernusheros/avernus/issues")

    def on_export(self, *args):
        ExportDialog(parent=self.window)

    def on_apply_categorization_rules(self, *args):
        for foo in categorization_controller.apply_categorization_rules():
            pass

    def on_get_historical_data(self, *args):
        progress_manager.add_task(datasource_controller.update_historical_prices,
                            description = _('downloading quotations...'))

    def on_update_assets(self, *args):
        progress_manager.add_task(datasource_controller.update_all,
                            description = _('updating assets...'))
