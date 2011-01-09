#!/usr/bin/env python

try:
    import pygtk
    pygtk.require("2.0")
except:
    raise Exception("PyGTK Version >=2.0 required")

if __name__ == '__main__':
    import sys
    sys.path.append('..')

import gtk,os #, gobject
from avernus import pubsub, config
from avernus.gui import dialogs, chart_tab
from avernus.gui.positions_tab import PositionsTab
from avernus.gui.overview_tab import OverviewTab
from avernus.gui.left_pane import MainTreeBox, Category
from avernus.gui.dividends_tab import DividendsTab
from avernus.gui.transactions_tab import TransactionsTab
from avernus.gui.container_overview_tab import ContainerOverviewTab
from avernus.gui.closed_positions_tab import ClosedPositionsTab
from avernus.gui.preferences import PrefDialog
from avernus.gui.account_transactions_tab import AccountTransactionTab
from avernus.gui.account_chart_tab import AccountChartTab
from avernus.gui.csv_import_dialog import CSVImportDialog
from webbrowser import open as web
import avernus
from avernus.objects import model

class AboutDialog(gtk.AboutDialog):
    def __init__(self, *arg, **args):
        gtk.AboutDialog.__init__(self)

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


class MenuBar(gtk.MenuBar):
    def __init__(self, parent, actiongroup, accelgroup):
        self.actiongroup = actiongroup
        gtk.MenuBar.__init__(self)

        # Create actions
        #item: name, stockid, label, accel, tooltip, callback
        actiongroup.add_actions(
            [('avernus'  , None                 , '_avernus'),
             ('Edit'          , None                 , '_Edit'),
             ('Tools'         , None                 , '_Tools'),
             ('Help'          , None                 , '_Help'),
             ('import'        , None                 , '_Import CSV'        , None        , None, CSVImportDialog),
             ('quit'          , gtk.STOCK_QUIT       , '_Quit'              , '<Control>q', None, parent.on_destroy),
             ('prefs'         , gtk.STOCK_PREFERENCES, '_Preferences'       , None        , None, parent.on_prefs),
             ('update'        , gtk.STOCK_REFRESH    , '_Update all stocks' , 'F5'        , None, lambda x: avernus.objects.controller.update_all()),
             ('help'          , gtk.STOCK_HELP       , '_Help'              , 'F1'        , None, lambda x:web("https://answers.launchpad.net/avernus")),
             ('website'       , None                 , '_Website'           , None        , None, lambda x:web("https://launchpad.net/avernus")),
             ('feature'       , None                 , 'Request a _Feature' , None        , None, lambda x:web("https://blueprints.launchpad.net/avernus")),
             ('bug'           , None                 , 'Report a _Bug'      , None        , None, lambda x:web("https://bugs.launchpad.net/avernus")),
             ('about'         , gtk.STOCK_ABOUT      , '_About'             , None        , None, AboutDialog),
             ])

        for action in actiongroup.list_actions():
            action.set_accel_group(accelgroup)

        file_menu_items  = ['import','---','quit']
        edit_menu_items = ['prefs']
        tools_menu_items = ['update']
        help_menu_items  = ['help', 'website', 'feature', 'bug', '---', 'about']

        self._create_menu('avernus', file_menu_items)
        self._create_menu('Edit', edit_menu_items)
        self._create_menu('Tools', tools_menu_items)
        self._create_menu('Help', help_menu_items)

    def _create_menu(self, action, items):
        menu_item = self.actiongroup.get_action(action).create_menu_item()
        menu_item.mname = action #used in plugin api
        self.append(menu_item)
        menu = gtk.Menu()
        menu_item.set_submenu(menu)
        for item in items:
            if item == '---':
                menu.append(gtk.SeparatorMenuItem())
            else:
                menu.append(self.actiongroup.get_action(item).create_menu_item())


class MainWindow(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)
        self.config = config.avernusConfig()
        self.set_title(avernus.__appname__)

        vbox = gtk.VBox()
        self.add(vbox)

        # Create an accelerator group
        accelgroup = gtk.AccelGroup()
        # Add the accelerator group to the toplevel window
        self.add_accel_group(accelgroup)
        # Create an ActionGroup
        actiongroup = gtk.ActionGroup('main_window')

        self.main_menu = MenuBar(self, actiongroup, accelgroup)
        vbox.pack_start(self.main_menu, expand=False, fill=False)

        self.hpaned = gtk.HPaned()
        vbox.pack_start(self.hpaned)

        self.hpaned.pack1(MainTreeBox())

        self.notebook = gtk.Notebook()
        self.hpaned.pack2(self.notebook)

        self.notebook.connect('switch-page', self.on_notebook_selection)
        self.connect("destroy", self.on_destroy)
        self.connect('size_allocate', self.on_size_allocate)
        self.connect('window-state-event', self.on_window_state_event)
        pubsub.subscribe('maintree.select', self.on_maintree_select)
        pubsub.subscribe('maintree.unselect', self.on_maintree_unselect)

        self.tabs = {}
        self.tabs['Portfolio'] = [(PositionsTab, 'Positions'),
                                  (TransactionsTab, 'Transactions'),
                                  (DividendsTab, 'Dividends'),
                                  (ClosedPositionsTab, 'Closed positions'),
                                  (chart_tab.ChartTab, 'Charts')]
        self.tabs['Watchlist'] = [(PositionsTab, 'Positions')]
        self.tabs['Category']  = [(ContainerOverviewTab, 'Overview')]
        self.tabs['Account']   = [(AccountTransactionTab, 'Transactions'),
                                  (AccountChartTab, 'Charts')]

        #set min size
        screen = self.get_screen()
        monitor = screen.get_monitor_geometry(0)
        width = int(monitor.width * 0.66)
        height = int(monitor.height * 0.66)
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
        if event.new_window_state == gtk.gdk.WINDOW_STATE_MAXIMIZED:
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
        gtk.main_quit()

    def clear_notebook(self):
        for child in self.notebook.get_children():
            self.notebook.remove_page(-1)
            child.destroy()

    def on_notebook_selection(self, notebook, page, page_num):
        notebook.get_nth_page(page_num).show()

    def on_maintree_select(self, item):
        self.clear_notebook()
        for tab, name in self.tabs[item.__name__]:
            self.notebook.append_page(tab(item), gtk.Label(name))

    def on_maintree_unselect(self):
        self.clear_notebook()

    def on_prefs(self, *args):
        PrefDialog(self.pengine)
