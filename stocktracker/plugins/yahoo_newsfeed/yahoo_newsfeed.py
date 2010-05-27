#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gtk, feedparser
from webbrowser import open as web

class Main():
    
    configurable = False

    def activate(self):
        self.api.add_tab(NewsfeedTab, 'News', ['Portfolio', 'Watchlist', 'Index', 'Tag'])
                
    def deactivate(self):
        self.api.remove_tab(NewsfeedTab, 'News', ['Portfolio', 'Watchlist', 'Index', 'Tag'])


class NewsfeedTab(gtk.VBox):
    
    def __init__(self, container):
        gtk.VBox.__init__(self)
        self.container = container
        self.tree = NewsTree()
        sw = gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.add(self.tree)
        
        self.pack_start(sw)
        self.show_all()
    
    #on select container on show 
    def show(self):
        symbols = ''
        for pos in self.container:
            symbols+= pos.stock.yahoo_symbol+'+'
        symbols = symbols.strip('+')
        url = 'http://finance.yahoo.com/rss/headline?s=%s' % (symbols,)
        feed = feedparser.parse(url)
        for item in feed.entries:
            self.tree.insert_item(item)
        

class NewsTree(gtk.TreeView):
    def __init__(self):
        gtk.TreeView.__init__(self)
        self.set_model(gtk.TreeStore(str, str))
        
        column = gtk.TreeViewColumn("text")
        self.append_column(column)
        cell = gtk.CellRendererText()
        cell.props.wrap_width = 800
        column.pack_start(cell, expand = True)
        column.add_attribute(cell, "markup", 0)        

        self.set_rules_hint(True)
        self.set_headers_visible(False)
        self.connect('row-activated', self.on_row_activated)
                
    def insert_item(self, item):
        
        text = '<b>'+item.title+'</b>\t'
        if 'date' in dir(item):
            text += item.date
        text += '\n'+item.summary
        link = "No Link found"
        if "link" in dir(item):
            link = item.link
        self.get_model().append(None, [text, link])

    def on_row_activated(self, treeview, iter, path):
        web(treeview.get_model()[iter][1])
        
