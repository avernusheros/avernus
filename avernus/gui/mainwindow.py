#!/usr/bin/env python
from avernus import pubsub, config
from avernus.controller import filterController
from avernus.controller import portfolio_controller
from avernus.gui import progress_manager, threads
from avernus.gui.account.account_transactions_tab import AccountTransactionTab
from avernus.gui.account_overview import AccountOverview
from avernus.gui.account.csv_import_dialog import CSVImportDialog
from avernus.gui.account.filterDialog import FilterDialog
from avernus.gui.left_pane import MainTreeBox
from avernus.gui.portfolio.portfolio_notebook import PortfolioNotebook
from avernus.gui.portfolio.positions_tab import WatchlistPositionsTab
from avernus.gui.portfolio.overview_notebook import OverviewNotebook
from avernus.gui.preferences import PrefDialog
from avernus.gui.account.exportDialog import ExportDialog
from avernus.objects import model
from webbrowser import open as web
import avernus
from gi.repository import Gtk
from gi.repository import Gdk
import sys

#FIXME remove this hack
reload(sys)
sys.setdefaultencoding("utf-8")



UI_INFO = """
<ui>
  <menubar name='MenuBar'>
    <menu action='AvernusMenu'>
      <menuitem action='import' />
      <menuitem action='export CSV' />
      <separator />
      <menuitem action='quit' />
    </menu>
    <menu action='EditMenu'>
      <menuitem action='Preferences' />
    </menu>
    <menu action='ToolsMenu'>
      <menuitem action='update'/>
      <menuitem action='historical'/>
      <menuitem action='filter'/>
      <menuitem action='do_assignments'/>
    </menu>
    <menu action='HelpMenu'>
      <menuitem action='help'/>
      <menuitem action='website'/>
      <menuitem action='feature'/>
      <menuitem action='bug'/>
      <separator />
      <menuitem action='about'/>
    </menu>
  </menubar>
</ui>
"""



class AboutDialog(Gtk.AboutDialog):

    def __init__(self, parent=None):
        Gtk.AboutDialog.__init__(self, parent=parent)

        self.set_name(avernus.__appname__)
        self.set_version(avernus.__version__)
        self.set_copyright(avernus.__copyright__)
        self.set_comments(avernus.__description__)
        self.set_license(avernus.__license__)
        self.set_authors(avernus.__authors__)
        self.set_website(avernus.__url__)
        self.set_logo_icon_name('avernus')

        self.run()
        self.hide()


class MainWindow(Gtk.Window):

    def __init__(self):
        super(Gtk.Window, self).__init__(type=Gtk.WindowType.TOPLEVEL)
        self.config = config.avernusConfig()
        self.set_title(avernus.__appname__)

        vbox = Gtk.VBox()
        self.add(vbox)

        actiongroup = Gtk.ActionGroup('main')
        self.add_actions(actiongroup)

        uimanager = Gtk.UIManager()
        # Throws exception if something went wrong
        uimanager.add_ui_from_string(UI_INFO)
        # Add the accelerator group to the toplevel window
        accelgroup = uimanager.get_accel_group()
        self.add_accel_group(accelgroup)
        uimanager.insert_action_group(actiongroup)

        menubar = uimanager.get_widget("/MenuBar")
        vbox.pack_start(menubar, False, False, 0)

        self.hpaned = Gtk.HPaned()
        vbox.pack_start(self.hpaned, True, True, 0)

        self.hpaned.pack1(MainTreeBox())

        self.connect("destroy", self.on_destroy)
        self.connect('size_allocate', self.on_size_allocate)
        self.connect('window-state-event', self.on_window_state_event)
        pubsub.subscribe('maintree.select', self.on_maintree_select)
        pubsub.subscribe('maintree.unselect', self.on_maintree_unselect)

        self.pages = {}
        self.pages['Portfolio'] = PortfolioNotebook
        self.pages['Watchlist'] = WatchlistPositionsTab
        self.pages['Category Accounts'] = AccountOverview
        self.pages['Category Portfolios'] = OverviewNotebook
        self.pages['Account'] = AccountTransactionTab

        #set min size
        screen = self.get_screen()
        width = int(screen.get_width() * 0.66)
        height = int(screen.get_height() * 0.66)
        self.set_size_request(width, height)

        size = self.config.get_option('size', section='Gui')
        if size is not None:
            width, height = eval(size)
            self.resize(width, height)

        pos = self.config.get_option('hpaned position', 'Gui') or width * 0.25
        self.hpaned.set_position(int(pos))

        #config entries are strings...
        if self.config.get_option('maximize', section='Gui') == 'True':
            self.maximize()
            self.maximized = True
        else:
            self.maximized = False

        #display everything
        self.show_all()

    def add_actions(self, actiongroup):
        actiongroup.add_actions([
            ("EditMenu", None, "Edit"),
            ("Preferences", Gtk.STOCK_PREFERENCES, '_Preferences', None, None,
             self.on_prefs),

            ("AvernusMenu", None, "_Avernus"),
            ('import', None, '_Import Account Transactions', None, None, self.on_csv_import),
            ('export CSV', None, '_Export Account Transactions', None, None, self.on_csv_export),
            ('quit', Gtk.STOCK_QUIT, '_Quit', '<Control>q', None, self.on_destroy),

            ('ToolsMenu', None, '_Tools'),
            ('update', Gtk.STOCK_REFRESH, '_Update all stocks', 'F5', None, self.on_update_all),
            ('historical', Gtk.STOCK_REFRESH, 'Get _historical data', None, None, self.on_historical),
            ('filter', None, '_Category Filters', None, None, self.on_category_assignments),
            ('do_assignments', None, '_Run auto-assignments', None, None, self.on_do_category_assignments),


            ('HelpMenu', None, '_Help'),
            ('help', Gtk.STOCK_HELP, '_Help', 'F1', None, lambda x:web("https://answers.launchpad.net/avernus")),
            ('website', None, '_Website', None, None, lambda x:web("https://launchpad.net/avernus")),
            ('feature', None, 'Request a _Feature' , None, None, lambda x:web("https://blueprints.launchpad.net/avernus")),
            ('bug', None, 'Report a _Bug', None, None, lambda x:web("https://bugs.launchpad.net/avernus")),
            ('about', Gtk.STOCK_ABOUT, '_About', None, None, self.on_about),

            ])

    def on_size_allocate(self, widget=None, data=None):
        if not self.maximized:
            self.config.set_option('size', self.get_size(), 'Gui')

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
        model.store.close()
        model.store.join()
        Gtk.main_quit()

    def on_maintree_select(self, item):
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
            self.hpaned.pack2(self.pages[page](item))

    def on_maintree_unselect(self):
        page = self.hpaned.get_child2()
        if page:
            self.hpaned.remove(page)
            page.destroy()

    def on_prefs(self, *args):
        PrefDialog(parent=self)

    def on_category_assignments(self, *args):
        FilterDialog(parent=self)

    def on_csv_import(self, *args):
        CSVImportDialog(parent=self)

    def on_about(self, *args):
        AboutDialog(parent=self)

    def on_csv_export(self, *args):
        ExportDialog(parent=self)

    def on_do_category_assignments(self, *args):
        threads.GeneratorTask(filterController.run_auto_assignments).start()
        #filterController.run_auto_assignments()

    def on_historical(self, *args):
        def finished_cb():
            progress_manager.remove_monitor(42)
        m = progress_manager.add_monitor(42, _('downloading quotations...'), Gtk.STOCK_REFRESH)
        threads.GeneratorTask(portfolio_controller.update_historical_prices, m.progress_update, complete_callback=finished_cb).start()

    def on_update_all(self, *args):
        def finished_cb():
            progress_manager.remove_monitor(11)
        m = progress_manager.add_monitor(11, _('updating stocks...'), Gtk.STOCK_REFRESH)
        threads.GeneratorTask(portfolio_controller.update_all, m.progress_update, complete_callback=finished_cb).start()
