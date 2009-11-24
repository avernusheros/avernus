#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/stocktracker
#    stocktracker.py: Copyright 2009 Wolfgang Steitz <wsteitz(at)gmail.com>
#
#    This file is part of stocktracker.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.



try:
    import pygtk
    pygtk.require("2.0")
except:
    raise Exception("PyGTK Version >=2.0 required")

import logging, gtk,os #, gobject
from stocktracker import treeviews, persistent_store, objects, config, pubsub, chart_tab, dialogs
from stocktracker.positions_tab import PositionsTab
from stocktracker.overview_tab import OverviewTab
from webbrowser import open as web
import stocktracker

logger = logging.getLogger(__name__)



class AboutDialog(gtk.AboutDialog):
    def __init__(self):
        gtk.AboutDialog.__init__(self)
        
        self.set_name(stocktracker.__appname__)
        self.set_version(stocktracker.__version__)
        self.set_copyright(stocktracker.__copyright__)
        self.set_comments(stocktracker.__description__)
        self.set_license(stocktracker.__license__)
        self.set_authors(stocktracker.__authors__)
        self.set_website(stocktracker.__url__)
        #self.set_logo(gtk.gdk.pixbuf_new_from_file("xyz.png"))
        
        self.run()
        self.hide()


class MenuBar(gtk.MenuBar):
    def __init__(self, model, parent=None):
        self.model = model
        
        gtk.MenuBar.__init__(self)
        file_menu_items  = (('----'  , None, None),
                           (_("Quit"), gtk.STOCK_QUIT, parent.on_destroy),
                           )
        tools_menu_items = ( (_("Merge two positions"), None, self.on_merge),
                           )                   
        help_menu_items  = (#("Help"  , gtk.STOCK_HELP, None),
                            (_("Website"), None, lambda x:web("https://launchpad.net/stocktracker")),
                            (_("Request a Feature"), None, lambda x:web("https://blueprints.launchpad.net/stocktracker")),
                            (_("Report a Bug"), None, lambda x:web("https://bugs.launchpad.net/stocktracker")),
                            ('----', None, None),
                            (_("About"), gtk.STOCK_ABOUT , self.on_about),
                           )

        filemenu = gtk.MenuItem(_("File"))
        filemenu.set_submenu(self.build_menu(file_menu_items))
        
        toolsmenu = gtk.MenuItem(_('Tools'))
        toolsmenu.set_submenu(self.build_menu(tools_menu_items))

        helpmenu = gtk.MenuItem(_("Help"))
        helpmenu.set_submenu(self.build_menu(help_menu_items))

        self.append(filemenu)
        self.append(toolsmenu)
        self.append(helpmenu)
        
    def build_menu(self, menu_items):
        menu = gtk.Menu()
        
        for label,icon, func in menu_items:
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

    def on_about(self, widget):
        AboutDialog()
    
    def on_merge(self, widget):
        d = dialogs.MergeDialog(self.model)
    
class TransactionsTab(gtk.ScrolledWindow):
    def __init__(self, item, model):
        gtk.ScrolledWindow.__init__(self)
        transactions_tree = treeviews.TransactionsTree(item, model)
        self.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        self.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        self.add(transactions_tree)
        self.show_all()

class MainTreeToolbar(gtk.Toolbar):
    def __init__(self, model):
        self.model = model
        gtk.Toolbar.__init__(self)
        
        button = gtk.ToolButton('gtk-add')
        button.connect('clicked', self.on_add_clicked)
        self.insert(button,-1)
        
        button = gtk.ToolButton('gtk-delete')
        #button.set_label('Remove tag'
        button.connect('clicked', self.on_remove_clicked)
        self.insert(button,-1)
        
        button = gtk.ToolButton('gtk-edit')
        #button.set_label('Remove tag'
        button.connect('clicked', self.on_edit_clicked)
        self.insert(button,-1)
         
             
    def on_add_clicked(self, widget):
        dialogs.NewContainerDialog(self.model)
    
    def on_remove_clicked(self, widget):
        pubsub.publish('maintoolbar.remove')  
           
    def on_edit_clicked(self, widget):
        pubsub.publish('maintoolbar.edit')


class MainWindow(gtk.Window):
    
    def __init__(self, model):
        self.model = model
        
        # Create the toplevel window
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
        vbox.pack_start(MenuBar(model, parent = self), expand=False, fill=False)
        
        hpaned = gtk.HPaned()
        hpaned.set_position(int(width*0.15))
        vbox.pack_start(hpaned)

        main_tree_vbox = gtk.VBox()
        main_tree = treeviews.MainTree(self.model)
        main_tree_vbox.pack_start(main_tree)
        main_tree_toolbar = MainTreeToolbar(self.model)
        main_tree_vbox.pack_start(main_tree_toolbar, expand=False, fill=False)
        
        hpaned.pack1(main_tree_vbox)
        
        self.notebook = gtk.Notebook()
        hpaned.pack2(self.notebook)
        
        self.notebook.connect('switch-page', self.on_notebook_selection)
        #subscribe
        self.connect("destroy", lambda x: gtk.main_quit())
        pubsub.subscribe('maintree.selection', self.on_maintree_selection)
        
        #display everything    
        self.show_all()
        
        
    def quit(self, widget, data=None):
        """quit - signal handler for closing the StocktrackerWindow"""
        self.destroy()

    def on_destroy(self, widget, data=None):
        """on_destroy - called when the StocktrackerWindow is close. """
        #clean up code for saving application state should be added here

        gtk.main_quit()
    
    def clear_notebook(self):
        for child in self.notebook.get_children():
            self.notebook.remove_page(-1)
            child.destroy()
    
    def on_notebook_selection(self, notebook, page, page_num):
        notebook.get_nth_page(page_num).show()
            
    def on_maintree_selection(self, item):
        self.clear_notebook()
        if isinstance(item, objects.Watchlist):
            type = 0
        elif isinstance(item, objects.Portfolio):
            type = 1
        elif isinstance(item, objects.Tag):
            type = 2
        else:
            type = -1

        if type == 0 or type == 1 or type == 2:
            self.notebook.append_page(OverviewTab(item, self.model, type), gtk.Label(_('Overview')))
            self.notebook.append_page(PositionsTab(item, self.model, type), gtk.Label(_('Positions')))
        
        if type == 1 or type == 2:
            self.notebook.append_page(TransactionsTab(item, self.model), gtk.Label(_('Transactions')))
            self.notebook.append_page(chart_tab.ChartTab(item, self.model), gtk.Label(_('Charts')))

def check_path(path):
    if not os.path.isdir(path):
        os.mkdir(path)    
    
