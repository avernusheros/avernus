#!/usr/bin/env python
from avernus import pubsub, config
from avernus.controller import controller, filterController
from avernus.gui import progress_manager, gui_utils
from avernus.gui.account_transactions_tab import AccountTransactionTab
from avernus.gui.container_overview_tab import ContainerOverviewTab
from avernus.gui.csv_import_dialog import CSVImportDialog
from avernus.gui.filterDialog import FilterDialog
from avernus.gui.left_pane import MainTreeBox
from avernus.gui.portfolio_notebook import PortfolioNotebook
from avernus.gui.positions_tab import PositionsTab
from avernus.gui.preferences import PrefDialog
from avernus.gui.exportDialog import ExportDialog
from avernus.objects import model
from webbrowser import open as web
import avernus
from gi.repository import Gtk
from gi.repository import Gdk
import sys


if __name__ == '__main__':
    sys.path.append('..')


class AboutDialog(Gtk.AboutDialog):

    def __init__(self, *arg, **args):
        super(Gtk.AboutDialog, self).__init__()

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


class MenuBar(Gtk.MenuBar):

    def __init__(self, parent, actiongroup, accelgroup):
        self.actiongroup = actiongroup
        super(Gtk.MenuBar, self).__init__()

        # Create actions
        #item: name, stockid, label, accel, tooltip, callback
        actiongroup.add_actions(
            [('Avernus'  , None                 , '_Avernus'),
             ('Edit'          , None                 , '_Edit'),
             ('Tools'         , None                 , '_Tools'),
             ('Help'          , None                 , '_Help'),
             ('import'        , None                 , '_Import CSV'        , None        , None, CSVImportDialog),
             ('quit'          , Gtk.STOCK_QUIT       , '_Quit'              , '<Control>q', None, parent.on_destroy),
             ('prefs'         , Gtk.STOCK_PREFERENCES, '_Preferences'       , None        , None, parent.on_prefs),
             ('update'        , Gtk.STOCK_REFRESH    , '_Update all stocks' , 'F5'        , None, parent.on_update_all),
             ('historical'    , Gtk.STOCK_REFRESH     ,'Get _historical data', None       , None,  parent.on_historical),
             ('help'          , Gtk.STOCK_HELP       , '_Help'              , 'F1'        , None, lambda x, y:web("https://answers.launchpad.net/avernus")),
             ('website'       , None                 , '_Website'           , None        , None, lambda x, y:web("https://launchpad.net/avernus")),
             ('feature'       , None                 , 'Request a _Feature' , None        , None, lambda x, y:web("https://blueprints.launchpad.net/avernus")),
             ('bug'           , None                 , 'Report a _Bug'      , None        , None, lambda x, y:web("https://bugs.launchpad.net/avernus")),
             ('about'         , Gtk.STOCK_ABOUT      , '_About'             , None        , None, AboutDialog),
             ('filter'        , None                 , '_Category Filters'  , None        , None, FilterDialog),
             ('do_assignments', None                 , '_Run auto-assignments', None      , None, parent.on_do_category_assignments),
             ('export CSV'    , None                 , '_Export Account Transactions', None, None, ExportDialog)
             ])

        for action in actiongroup.list_actions():
            action.set_accel_group(accelgroup)

        file_menu_items  = ['import','export CSV','---', 'quit']
        edit_menu_items = ['prefs']
        tools_menu_items = ['update', 'historical','filter', 'do_assignments']
        help_menu_items  = ['help', 'website', 'feature', 'bug', '---', 'about']

        self._create_menu('Avernus', file_menu_items)
        self._create_menu('Edit', edit_menu_items)
        self._create_menu('Tools', tools_menu_items)
        self._create_menu('Help', help_menu_items)

    def _create_menu(self, action, items):
        menu_item = self.actiongroup.get_action(action).create_menu_item()
        #menu_item.mname = action #used in plugin api
        self.append(menu_item)
        menu = Gtk.Menu()
        menu_item.set_submenu(menu)
        for item in items:
            if item == '---':
                menu.append(Gtk.SeparatorMenuItem())
            else:
                menu.append(self.actiongroup.get_action(item).create_menu_item())


class MainWindow(Gtk.Window):

    def __init__(self):
        super(Gtk.Window, self).__init__(type=Gtk.WindowType.TOPLEVEL)
        self.config = config.avernusConfig()
        self.set_title(avernus.__appname__)

        vbox = Gtk.VBox()
        self.add(vbox)

        # Create an accelerator group
        accelgroup = Gtk.AccelGroup()
        # Add the accelerator group to the toplevel window
        self.add_accel_group(accelgroup)
        # Create an ActionGroup
        actiongroup = Gtk.ActionGroup('main_window')

        self.main_menu = MenuBar(self, actiongroup, accelgroup)
        vbox.pack_start(self.main_menu, False, False, 0)

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
        self.pages['Watchlist'] = PositionsTab
        self.pages['Category']  = ContainerOverviewTab
        self.pages['Account']   = AccountTransactionTab

        #set min size
        screen = self.get_screen()
        width = int(screen.get_width() * 0.66)
        height = int(screen.get_height() * 0.66)
        self.set_size_request(width, height)

        size = self.config.get_option('size', section='Gui')
        if size is not None:
            width, height = eval(size)
            self.resize(width, height)

        pos = self.config.get_option('hpaned position', 'Gui') or width*0.25
        self.hpaned.set_position(int(pos))

        #config entries are strings...
        if self.config.get_option('maximize', section='Gui') == 'True':
            self.maximize()
            self.maximized = True
        else:
            self.maximized = False

        #display everything
        self.show_all()

    def on_size_allocate(self, widget = None, data = None):
        if not self.maximized:
            self.config.set_option('size', self.get_size(), 'Gui')

    def on_window_state_event(self, widget, event):
        if event.new_window_state == Gdk.WindowState.MAXIMIZED:
            self.maximized = True
            self.config.set_option('maximize', True, section='Gui')
        else:
            self.maximized = False
            self.config.set_option('maximize', False, section='Gui')

    def on_destroy(self, widget, data=None):
        """on_destroy - called when the avernusWindow is closed. """
        #save db on quit
        self.config.set_option('hpaned position', self.hpaned.get_position(), 'Gui')
        model.store.close()
        #sys.exit()

    def on_maintree_select(self, item):
        self.on_maintree_unselect()
        self.hpaned.pack2(self.pages[item.__name__](item))

    def on_maintree_unselect(self):
        page = self.hpaned.get_child2()
        if page:
            self.hpaned.remove(page)
            del page

    def on_prefs(self, *args):
        PrefDialog()

    def on_do_category_assignments(self, *args):
        gui_utils.BackgroundTask(filterController.run_auto_assignments).start()

    def on_historical(self, *args):
        def finished_cb():
            progress_manager.remove_monitor(42)
        m = progress_manager.add_monitor(42, _('downloading quotations...'), Gtk.STOCK_REFRESH)
        gui_utils.GeneratorTask(controller.update_historical_prices, m.progress_update, complete_callback=finished_cb).start()

    def on_update_all(self, *args):
        def finished_cb():
            progress_manager.remove_monitor(11)
        m = progress_manager.add_monitor(11, _('updating stocks...'), Gtk.STOCK_REFRESH)
        m.progress_update_auto()
        gui_utils.GeneratorTask(controller.update_all, complete_callback=finished_cb).start()
