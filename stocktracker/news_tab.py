#!/usr/bin/env python

import gtk, feedparser
from stocktracker.treeviews import Tree
from webbrowser import open as web

class NewsTab(gtk.VBox):
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
     
    def show(self):
        symbols = ''
        for pos in self.container.positions:
            symbols+= pos.stock.yahoo_symbol+'+'
        symbols = symbols.strip('+')
        url = 'http://finance.yahoo.com/rss/headline?s=%s' % (symbols,)
        feed = feedparser.parse(url)
        for item in feed.entries:
            self.tree.insert_item(item)
        

class NewsTree(Tree):
    def __init__(self):
        Tree.__init__(self)
        self.set_model(gtk.TreeStore(str, str))
        col, cell = self.create_column("text", 0)
        cell.props.wrap_width = 800

        self.set_rules_hint(True)
        self.set_headers_visible(False)
        self.connect('row-activated', self.on_row_activated)
        #self.connect('cursor_changed', self.on_cursor_changed)
                
    def insert_item(self, item):
        text = '<b>'+item.title+'</b>\t'+item.date+'\n'+item.summary
        self.get_model().append(None, [text, item.link])

    def on_row_activated(self, treeview, iter, path):
        web(treeview.get_model()[iter][1])
        
