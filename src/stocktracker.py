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
import treeviews, toolbars, persistent_store, objects, config, pubsub
from webbrowser import open as web
if __name__ == "__main__":
    import __init__

logger = logging.getLogger(__name__)



__appname__ = 'stocktracker'
__version__ = '0.2'
__description__ = _('A lightweight program to easily track your investments.')
__url__='https://launchpad.net/stocktracker'
__authors__ = ['Wolfgang Steitz (wsteitz(at)gmail.com)']
__mail__ = 'wsteitz(at)gmail.com'
__copyright__ = '''\
Copyright (c) 2008-2009 Wolfgang Steitz

'''
__license__='''\
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
'''




class AboutDialog(gtk.AboutDialog):
    def __init__(self):
        gtk.AboutDialog.__init__(self)
        
        self.set_name(__appname__)
        self.set_version(__version__)
        self.set_copyright(__copyright__)
        self.set_comments(__description__)
        self.set_license(__license__)
        self.set_authors(__authors__)
        self.set_website(__url__)
        #self.set_logo(gtk.gdk.pixbuf_new_from_file("xyz.png"))
        
        self.run()
        self.hide()


class MenuBar(gtk.MenuBar):
    def __init__(self, parent):
        gtk.MenuBar.__init__(self)
        file_menu_items = (('----'  , None, None),
                           (_("Quit"), gtk.STOCK_QUIT, lambda x: parent.destroy()),
                           )
        help_menu_items = (#("Help"  , gtk.STOCK_HELP, None),
                            (_("Website"), None, lambda x:web("https://launchpad.net/stocktracker")),
                            (_("Request a Feature"), None, lambda x:web("https://blueprints.launchpad.net/stocktracker")),
                            (_("Report a Bug"), None, lambda x:web("https://bugs.launchpad.net/stocktracker")),
                            ('----', None, None),
                            (_("About"), gtk.STOCK_ABOUT , self.on_about),
                           )

        filemenu = gtk.MenuItem(_("File"))
        filemenu.set_submenu(self.build_menu(file_menu_items))

        helpmenu = gtk.MenuItem(_("Help"))
        helpmenu.set_submenu(self.build_menu(help_menu_items))

        self.append(filemenu)
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


class PositionsTab(gtk.VBox):
    def __init__(self, pf, model, type):
        gtk.VBox.__init__(self)
        
        positions_tree = treeviews.PositionsTree(pf, model, type)
        hbox = gtk.HBox()
        tb = toolbars.PositionsToolbar(pf)
        hbox.pack_start(tb)
        
        text = '<b>' + _('Performance Today')+'</b>\n'+treeviews.get_change_string(pf.current_change)
        label = gtk.Label()
        label.set_markup(text)
        hbox.pack_start(label)
        hbox.pack_start(gtk.VSeparator())
        text = '<b>'+_('Overall')+'</b>\n'+treeviews.get_change_string(pf.overall_change)
        label = gtk.Label()
        label.set_markup(text)
        hbox.pack_start(label)
        
        self.pack_start(hbox, expand=False, fill=False)
        self.pack_start(positions_tree)
        self.show_all()
        


class MainWindow(gtk.Window):
    
    def __init__(self, model):
        self.model = model
        
        # Create the toplevel window
        gtk.Window.__init__(self)
        
        self.set_title(__appname__)

        # Use two thirds of the screen by default
        screen = self.get_screen()
        monitor = screen.get_monitor_geometry(0)
        width = int(monitor.width * 0.8)
        height = int(monitor.height * 0.66)
        self.set_default_size(width, height)

        vbox = gtk.VBox()
        self.add(vbox)
        
        #the main menu
        vbox.pack_start(MenuBar(self), expand=False, fill=False)
        
        hpaned = gtk.HPaned()
        hpaned.set_position(int(width*0.15))
        vbox.pack_start(hpaned)

        main_tree_vbox = gtk.VBox()
        main_tree = treeviews.MainTree(self.model)
        main_tree_vbox.pack_start(main_tree)
        main_tree_toolbar = toolbars.MainTreeToolbar(self.model)
        main_tree_vbox.pack_start(main_tree_toolbar, expand=False, fill=False)
        
        hpaned.pack1(main_tree_vbox)
        
        self.notebook = gtk.Notebook()
        hpaned.pack2(self.notebook)
        
        
        #subscribe
        self.connect("destroy", lambda x: gtk.main_quit())
        pubsub.subscribe('maintree.selection', self.on_maintree_selection)
        
        #display everything    
        self.show_all()

    def clear_notebook(self):
        for child in self.notebook.get_children():
            self.notebook.remove_page(-1)
            child.destroy()
            
    def on_maintree_selection(self, item):
        self.clear_notebook()
        if isinstance(item, objects.Watchlist):
            type = 0
        elif isinstance(item, objects.Portfolio):
            type = 1
        else:
            type = -1

        if type == 0 or type == 1:
            self.notebook.append_page(PositionsTab(item, self.model, type), gtk.Label(_('Positions')))
            
        if type == 1:
            transactions_tree = treeviews.TransactionsTree(item, self.model)
            transactions_tree.show_all()
            self.notebook.append_page(transactions_tree, gtk.Label(_('Transactions')))


def check_path(path):
    if not os.path.isdir(path):
        os.mkdir(path)    
    
    
def start():
    check_path(config.config_path)
    store = persistent_store.Store(config.db_file)
    model = objects.Model(store)
    store.model = model
    
    main_window = MainWindow(model)
    model.initialize()
    
    #gobject.threads_init()
    gtk.main()    

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, 
         format="%(levelname)s %(asctime)s %(funcName)s %(lineno)d %(message)s")
    start()

