#!/usr/bin/env python

try:
    import pygtk
    pygtk.require("2.0")
except:
    raise Exception("PyGTK Version >=2.0 required")

if __name__ == '__main__':
    import sys
    sys.path.append('..')


import logging, gtk,os #, gobject
from stocktracker import pubsub, updater
from stocktracker.gui import dialogs, chart_tab
from stocktracker.gui.positions_tab import PositionsTab
from stocktracker.gui.overview_tab import OverviewTab
from stocktracker.gui.main_tree import MainTreeBox, Category
from stocktracker.gui.dividends_tab import DividendsTab
from stocktracker.gui.transactions_tab import TransactionsTab
from stocktracker.gui.indexpositions_tab import IndexPositionsTab
from stocktracker.gui.news_tab import NewsTab
from stocktracker.gui.index_tab import IndexTab
from webbrowser import open as web
import stocktracker
import stocktracker.objects

logger= logging.getLogger(__name__)



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
    def __init__(self, parent=None):
        gtk.MenuBar.__init__(self)
        file_menu_items  = (('New', gtk.STOCK_NEW, self.on_new),
                            ('Open', gtk.STOCK_OPEN, OpenDialog),
                            ('Save', gtk.STOCK_SAVE, self.on_save),
                            ('Save As', gtk.STOCK_SAVE, SaveAsDialog),
                            ('----'  , None, None),
                            (_("Quit"), gtk.STOCK_QUIT, parent.on_destroy),
                           )
        edit_menu_items = (
                           (_("Preferences"),gtk.STOCK_PREFERENCES,self.on_pref),
                           )
        tools_menu_items = ((_('Update all stocks') , gtk.STOCK_REFRESH, self.on_update),
                            (_('Reload stocks from yahoo'), gtk.STOCK_REFRESH, lambda x: stocktracker.objects.controller.load_stocks()), 
                            (_('Add a stock'), gtk.STOCK_ADD, self.on_add),
                            (_("Merge two positions"), gtk.STOCK_CONVERT, self.on_merge),
                           )                   
        help_menu_items  = (#("Help"  , gtk.STOCK_HELP, None),
                            (_("Website"), None, lambda x:web("https://launchpad.net/stocktracker")),
                            (_("Request a Feature"), None, lambda x:web("https://blueprints.launchpad.net/stocktracker")),
                            (_("Report a Bug"), None, lambda x:web("https://bugs.launchpad.net/stocktracker")),
                            ('----', None, None),
                            (_("About"), gtk.STOCK_ABOUT , AboutDialog),
                           )

        filemenu = gtk.MenuItem(_("File"))
        filemenu.set_submenu(self.build_menu(file_menu_items))
        
        editmenu = gtk.MenuItem(_('Edit'))
        editmenu.set_submenu(self.build_menu(edit_menu_items))
        
        toolsmenu = gtk.MenuItem(_('Tools'))
        toolsmenu.set_submenu(self.build_menu(tools_menu_items))

        helpmenu = gtk.MenuItem(_("Help"))
        helpmenu.set_submenu(self.build_menu(help_menu_items))

        self.append(filemenu)
        self.append(editmenu)
        self.append(toolsmenu)
        self.append(helpmenu)
        
    def build_menu(self, menu_items):
        menu = gtk.Menu()
        
        for label, icon, func in menu_items:
            if label == '----':
                s = gtk.SeparatorMenuItem()
                s.show()
                menu.add(s)
            else:
                if icon is not None:
                    item = gtk.ImageMenuItem(icon)
                    item.get_children()[0].set_label(label)
                else:
                    item = gtk.MenuItem(label) 
                if func is not None:
                    item.connect("activate", func)
                item.show()
                menu.add(item)
        return menu

    def on_merge(self, widget):
        dialogs.MergeDialog()
    
    def on_update(self, widget):
        stocktracker.objects.controller.update_all()
        
    def on_add(self,widget):
        dialogs.AddStockDialog()
    
    def on_save(self, widget):
        model.commit()
        
    def on_pref(self, widget):
        dialogs.PrefDialog()
    
    def on_new(self, widget):
        print "not implemented"
        #session['model'].clear()
        #session['model'].store.new() 
        #session['model'].initialize()   
        

class OpenDialog(gtk.FileChooserDialog):            
    def __init__(self, *arg, **args):
        gtk.FileChooserDialog.__init__(self, title='Open...', 
                    action=gtk.FILE_CHOOSER_ACTION_OPEN, 
                    buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                        gtk.STOCK_OK, gtk.RESPONSE_ACCEPT), backend=None)    
        response = self.run()  
        self.process_result(response)
        self.destroy()
    
    def process_result(self, response):
        if response == gtk.RESPONSE_ACCEPT:
            print "not implemented"
            #session['model'].clear()
            #session['model'].store.open(self.get_filename())
            #session['model'].initialize()
            

class SaveAsDialog(gtk.FileChooserDialog):            
    def __init__(self, *arg, **args):
        gtk.FileChooserDialog.__init__(self, title='Save as...',  action=gtk.FILE_CHOOSER_ACTION_SAVE, buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT), backend=None)    
        response = self.run()  
        self.process_result(response)
        self.destroy()
    
    def process_result(self, response):
        if response == gtk.RESPONSE_ACCEPT:
            model.save_as(self.get_filename)
    
    

class MainWindow(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)
        #self.set_title(__appname__)

        # Use two thirds of the screen by default
        screen = self.get_screen()
        monitor = screen.get_monitor_geometry(0)
        width = int(monitor.width * 0.8)
        height = int(monitor.height * 0.66)
        self.set_default_size(width, height)

        vbox = gtk.VBox()
        self.add(vbox)
        
        #the main menu
        vbox.pack_start(MenuBar(parent = self), expand=False, fill=False)
        
        hpaned = gtk.HPaned()
        hpaned.set_position(int(width*0.15))
        vbox.pack_start(hpaned)
        
        hpaned.pack1(MainTreeBox())
        
        self.notebook = gtk.Notebook()
        hpaned.pack2(self.notebook)
        
        self.notebook.connect('switch-page', self.on_notebook_selection)
        self.connect('key-press-event', self.on_key_press_event)
        #subscribe
        self.connect("destroy", self.on_destroy)
        pubsub.subscribe('maintree.select', self.on_maintree_select)
        pubsub.subscribe('maintree.unselect', self.on_maintree_unselect)
        
        #display everything    
        self.show_all()
        
    def on_key_press_event(self, widget, event):
        if event.keyval == gtk.gdk.keyval_from_name('F5'):
             stocktracker.objects.controller.update_all()
             return True
        if event.keyval == gtk.gdk.keyval_from_name('q'):
            self.on_destroy(widget) 
        return False

    def on_destroy(self, widget, data=None):
        """on_destroy - called when the StocktrackerWindow is close. """
        #clean up code for saving application state should be added here
        #FIXME save db on quit
        #model.commit()
        gtk.main_quit()
    
    def clear_notebook(self):
        for child in self.notebook.get_children():
            self.notebook.remove_page(-1)
            child.destroy()
    
    def on_notebook_selection(self, notebook, page, page_num):
        notebook.get_nth_page(page_num).show()
            
    def on_maintree_select(self, item):
        self.clear_notebook()
        type = None
        if isinstance(item, stocktracker.objects.container.Portfolio):
            type = "portfolio"
        elif isinstance(item, stocktracker.objects.container.Tag):
            type = "tag"
        elif isinstance(item, stocktracker.objects.container.Watchlist):
            type = "watchlist"
        elif isinstance(item, stocktracker.objects.container.Index):
            type = "index"
        elif isinstance(item, Category):
            type = "category"
        if type == "portfolio" or type == "tag" or type == "watchlist":
            #self.notebook.append_page(OverviewTab(item), gtk.Label(_('Overview')))
            self.notebook.append_page(PositionsTab(item), gtk.Label(_('Positions')))
        if type == "portfolio" or type == "tag": 
            self.notebook.append_page(TransactionsTab(item), gtk.Label(_('Transactions')))
            #FIXME
            #self.notebook.append_page(DividendsTab(item), gtk.Label(_('Dividends')))
            self.notebook.append_page(chart_tab.ChartTab(item), gtk.Label(_('Charts')))
        if type == "index":
            self.notebook.append_page(IndexPositionsTab(item), gtk.Label(_('Positions')))
        if type == "category" and item.name == 'Indices':
            self.notebook.append_page(IndexTab(item), gtk.Label(_('Indices')))
        if not type == "category":
            self.notebook.append_page(NewsTab(item), gtk.Label(_('News')))

    def on_maintree_unselect(self):
        self.clear_notebook()

def check_path(path):
    if not os.path.isdir(path):
        os.mkdir(path)    

