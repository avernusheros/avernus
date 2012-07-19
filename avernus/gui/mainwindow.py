#!/usr/bin/env python
from gi.repository import Gtk
from gi.repository import Gdk
from webbrowser import open as web
import sys

import avernus
from avernus import config
from avernus.controller import filter_controller
from avernus.controller import asset_controller
from avernus.gui import progress_manager, threads
from avernus.gui.account.account_transactions_tab import AccountTransactionTab
from avernus.gui.account.account_overview import AccountOverview
from avernus.gui.account.csv_import_dialog import CSVImportDialog
from avernus.gui.account.filterDialog import FilterDialog
from avernus.gui.left_pane import MainTreeBox
from avernus.gui.portfolio.portfolio_notebook import PortfolioNotebook
from avernus.gui.portfolio.positions_tab import WatchlistPositionsTab
from avernus.gui.portfolio.overview_notebook import OverviewNotebook
from avernus.gui.portfolio.asset_manager import AssetManager
from avernus.gui.preferences import PrefDialog
from avernus.gui.account.exportDialog import ExportDialog
from avernus.gui import get_ui_file

reload(sys)
sys.setdefaultencoding("utf-8")


PAGES = {
    'Portfolio': PortfolioNotebook,
    'AllPortfolio': PortfolioNotebook,
    'Watchlist': WatchlistPositionsTab,
    'Category Accounts': AccountOverview,
    'Category Portfolios': OverviewNotebook,
    'Account': AccountTransactionTab,
    'AllAccount': AccountTransactionTab,
        }

class MainWindow:

    def __init__(self):
        builder = Gtk.Builder()
        builder.add_from_file(get_ui_file("avernus.glade"))
        builder.connect_signals(self)
        self.window = builder.get_object("window")

        self.config = config.avernusConfig()
        self.window.set_title(avernus.__appname__)

        self.hpaned = builder.get_object("hpaned")

        sidebar = MainTreeBox()
        sidebar.main_tree.connect("unselect", self.on_maintree_unselect)
        sidebar.main_tree.connect("select", self.on_maintree_select)
        self.hpaned.pack1(sidebar)

        self.window.connect("destroy", self.on_destroy)
        self.window.connect('size_allocate', self.on_size_allocate)
        self.window.connect('window-state-event', self.on_window_state_event)

        #set min size
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

        #config entries are strings...
        if self.config.get_option('maximize', section='Gui') == 'True':
            self.window.maximize()
            self.maximized = True
        else:
            self.maximized = False

        #display everything
        self.window.show_all()

    def on_size_allocate(self, widget=None, data=None):
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
        avernus.objects.session.commit()
        #save db on quit
        self.config.set_option('hpaned position', self.hpaned.get_position(), 'Gui')
        threads.terminate_all()
        Gtk.main_quit()

    def on_maintree_select(self, caller=None, item=None):
        self.on_maintree_unselect()
        page = None
        if item.__class__.__name__ == 'Category':
            if item.name == 'Portfolios':
                page = "Category Portfolios"
            elif item.name == 'Accounts':
                page = "Category Accounts"
        else:
            page = item.__class__.__name__
        if page is not None:
            self.hpaned.pack2(PAGES[page](item))

    def on_maintree_unselect(self, caller=None):
        page = self.hpaned.get_child2()
        if page:
            self.hpaned.remove(page)
            page.destroy()

    def on_prefs(self, *args):
        PrefDialog(parent=self.window)

    def on_category_assignments(self, *args):
        FilterDialog(parent=self.window)

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

    def on_run_auto_assignments(self, *args):
        #FIXME the threaded version does not work
        #threads.GeneratorTask(filter_controller.run_auto_assignments).start()
        for foo in filter_controller.run_auto_assignments():
            pass

    def on_get_historical_data(self, *args):
        def finished_cb():
            progress_manager.remove_monitor(42)
        m = progress_manager.add_monitor(42, _('downloading quotations...'), Gtk.STOCK_REFRESH)
        threads.GeneratorTask(asset_controller.update_historical_prices, m.progress_update, complete_callback=finished_cb).start()

    def on_update_assets(self, *args):
        def finished_cb():
            progress_manager.remove_monitor(11)
        m = progress_manager.add_monitor(11, _('updating stocks...'), Gtk.STOCK_REFRESH)
        threads.GeneratorTask(asset_controller.update_all, m.progress_update, complete_callback=finished_cb).start()
