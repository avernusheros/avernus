#!/usr/bin/env python
from avernus import config, objects
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
from avernus.gui.portfolio.portfolio_notebook import PortfolioNotebook
from avernus.gui.portfolio.positions_tab import WatchlistPositionsTab
from avernus.gui.preferences import PrefDialog
from gi.repository import Gdk, Gtk
from webbrowser import open as web
import avernus
import sys


# hack to switch from ascii to utf8. can be removed once we switch to python3
reload(sys)
sys.setdefaultencoding("utf-8")


PAGES = {
    'Portfolio': PortfolioNotebook,
    'AllPortfolio': PortfolioNotebook,
    'Watchlist': WatchlistPositionsTab,
    'Category Accounts': AccountOverview,
    'Category Portfolios': OverviewNotebook,
        }


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

        self.hpaned = builder.get_object("hpaned")
        self.account_page = AccountTransactionTab()

        sidebar = sidebar.Sidebar()
        sidebar.connect("unselect", self.on_sidebar_unselect)
        sidebar.connect("select", self.on_sidebar_select)

        builder.connect_signals(HandlerFinder([self,
                                               self.account_page,
                                               sidebar]))

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
        objects.session.commit()
        # save db on quit
        self.config.set_option('hpaned position', self.hpaned.get_position(), 'Gui')
        threads.terminate_all()
        Gtk.main_quit()

    def on_sidebar_select(self, caller=None, item=None):
        self.on_sidebar_unselect()
        page = None
        if item.__class__.__name__ == 'Category':
            if item.name == 'Portfolios':
                page = "Category Portfolios"
            elif item.name == 'Accounts':
                page = "Category Accounts"
        else:
            page = item.__class__.__name__
        if page == "Account" or page == "AllAccount":
            self.hpaned.pack2(self.account_page)
            self.account_page.show()
            self.account_page.set_account(item)
        elif page is not None:
            self.hpaned.pack2(PAGES[page](item))

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
        web("https://answers.launchpad.net/avernus")

    def on_website(self, *args):
        web("https://launchpad.net/avernus")

    def on_feature(self, *args):
        web("https://blueprints.launchpad.net/avernus")

    def on_bug(self, *args):
        web("https://bugs.launchpad.net/avernus")

    def on_export(self, *args):
        ExportDialog(parent=self.window)

    def on_apply_categorization_rules(self, *args):
        # FIXME the threaded version does not work
        # threads.GeneratorTask(categorization_controller.apply_categorization_rules).start()
        for foo in categorization_controller.apply_categorization_rules():
            pass

    def on_get_historical_data(self, *args):
        def finished_cb():
            progress_manager.remove_monitor(42)
        m = progress_manager.add_monitor(42, _('downloading quotations...'), Gtk.STOCK_REFRESH)
        threads.GeneratorTask(datasource_controller.update_historical_prices, m.progress_update, complete_callback=finished_cb).start()

    def on_update_assets(self, *args):
        def finished_cb():
            progress_manager.remove_monitor(11)
        m = progress_manager.add_monitor(11, _('updating stocks...'), Gtk.STOCK_REFRESH)
        threads.GeneratorTask(datasource_controller.update_all, m.progress_update, complete_callback=finished_cb).start()
