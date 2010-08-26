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
from stocktracker import pubsub, config
from stocktracker.gui import dialogs, chart_tab
from stocktracker.gui.positions_tab import PositionsTab
from stocktracker.gui.overview_tab import OverviewTab
from stocktracker.gui.left_pane import MainTreeBox, Category
from stocktracker.gui.dividends_tab import DividendsTab
from stocktracker.gui.transactions_tab import TransactionsTab
from stocktracker.gui.indexpositions_tab import IndexPositionsTab
from stocktracker.gui.container_overview_tab import ContainerOverviewTab
from stocktracker.gui.preferences import PrefDialog
from stocktracker.gui.account_transactions_tab import AccountTransactionTab
from stocktracker.gui.account_chart_tab import AccountChartTab
from stocktracker.gui.csv_import_dialog import CSVImportDialog
from webbrowser import open as web
import stocktracker
from stocktracker.objects import model

class AboutDialog(gtk.AboutDialog):
    def __init__(self, *arg, **args):
        gtk.AboutDialog.__init__(self)
        
        self.set_name(stocktracker.__appname__)
        self.set_version(stocktracker.__version__)
        self.set_copyright(stocktracker.__copyright__)
        self.set_comments(stocktracker.__description__)
        self.set_license(stocktracker.__license__)
        self.set_authors(stocktracker.__authors__)
        self.set_website(stocktracker.__url__)
        self.set_logo_icon_name('stocktracker')
        
        self.run()
        self.hide()


class MenuBar(gtk.MenuBar):
    def __init__(self, parent, actiongroup, accelgroup):
        self.actiongroup = actiongroup
        gtk.MenuBar.__init__(self)
        
        # Create actions
        #item: name, stockid, label, accel, tooltip, callback
        actiongroup.add_actions(
            [('Stocktracker'  , None                 , '_Stocktracker'),
             ('Edit'          , None                 , '_Edit'),
             ('Tools'         , None                 , '_Tools'),
             ('Help'          , None                 , '_Help'),
             ('import'        , None                 , '_Import CSV'        , None        , None, CSVImportDialog),
             ('quit'          , gtk.STOCK_QUIT       , '_Quit'              , '<Control>q', None, parent.on_destroy),
             ('prefs'         , gtk.STOCK_PREFERENCES, '_Preferences'       , None        , None, parent.on_prefs),
             ('update'        , gtk.STOCK_REFRESH    , '_Update all stocks' , 'F5'        , None, lambda x: stocktracker.objects.controller.update_all()),
             #('merge', _("Merge two positions"), gtk.STOCK_CONVERT, dialogs.MergeDialog),
             ('help'          , gtk.STOCK_HELP       , '_Help'              , 'F1'        , None, lambda x:web("https://answers.launchpad.net/stocktracker")),
             ('website'       , None                 , '_Website'           , None        , None, lambda x:web("https://launchpad.net/stocktracker")),
             ('feature'       , None                 , 'Request a _Feature' , None        , None, lambda x:web("https://blueprints.launchpad.net/stocktracker")),
             ('bug'           , None                 , 'Report a _Bug'      , None        , None, lambda x:web("https://bugs.launchpad.net/stocktracker")),
             ('about'         , gtk.STOCK_ABOUT      , '_About'             , None        , None, AboutDialog),
             ])
        
        for action in actiongroup.list_actions():
            action.set_accel_group(accelgroup)
            
        file_menu_items  = ['import','---','quit']                  
        edit_menu_items = ['prefs']
        tools_menu_items = ['update']
        help_menu_items  = ['help', 'website', 'feature', 'bug', '---', 'about']
        
        self._create_menu('Stocktracker', file_menu_items)
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
        self.config = config.StocktrackerConfig()
        #self.set_title(__appname__)
        
        #set min size
        screen = self.get_screen()
        monitor = screen.get_monitor_geometry(0)
        width = int(monitor.width * 0.66)
        height = int(monitor.height * 0.66)
        self.set_size_request(width, height)

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
        
        hpaned = gtk.HPaned()
        hpaned.set_position(int(width*0.15))
        vbox.pack_start(hpaned)
        
        hpaned.pack1(MainTreeBox())
        
        self.notebook = gtk.Notebook()
        hpaned.pack2(self.notebook)
        
        self.notebook.connect('switch-page', self.on_notebook_selection)
        self.connect("destroy", self.on_destroy)
        self.connect('size_allocate', self.on_size_allocate)
        pubsub.subscribe('maintree.select', self.on_maintree_select)
        pubsub.subscribe('maintree.unselect', self.on_maintree_unselect)
        
        self.tabs = {}
        self.tabs['Portfolio'] = [(PositionsTab, 'Positions'), 
                                  (TransactionsTab, 'Transactions'),
                                  (DividendsTab, 'Dividends'),
                                  (chart_tab.ChartTab, 'Charts')]
        self.tabs['Watchlist'] = [(PositionsTab, 'Positions')]
        self.tabs['Tag']       = [(PositionsTab, 'Positions'),
                                  (TransactionsTab, 'Transactions'),
                                  (chart_tab.ChartTab, 'Charts')]
        self.tabs['Index']     = [(IndexPositionsTab, 'Positions')]
        self.tabs['Category']  = [(ContainerOverviewTab, 'Overview')]    
        self.tabs['Account']   = [(AccountTransactionTab, 'Transactions'),
                                  (AccountChartTab, 'Charts')]

        size = self.config.get_option('size', section='Gui')
        if size is not None:
            size = eval(size)
            self.resize(size[0], size[1])        
        #display everything
        self.show_all()
    
    def on_size_allocate(self, widget = None, data = None):
        self.width, self.height = self.get_size()
        
    def on_destroy(self, widget, data=None):
        """on_destroy - called when the StocktrackerWindow is closed. """
        #clean up code for saving application state should be added here
        #save db on quit
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
