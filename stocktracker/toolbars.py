#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gtk
from stocktracker import dialogs, pubsub


class PositionsToolbar(gtk.Toolbar):
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
        button.set_sensitive(False)
        
        button = gtk.ToolButton('gtk-paste')
        #button.set_label('Remove tag'
        button.connect('clicked', self.on_tag_clicked)
        self.insert(button,-1)
        
        self.insert(gtk.SeparatorToolItem(),-1)
        
        button = gtk.ToolButton('gtk-refresh')
        #button.set_label('Remove tag'
        button.connect('clicked', self.on_update_clicked)
        self.insert(button,-1)
        
           
    def on_add_clicked(self, widget):
        pubsub.publish('positionstoolbar.add')  
      
    def on_update_clicked(self, widget):
        pubsub.publish('positionstoolbar.update')
        
    def on_remove_clicked(self, widget):
        pubsub.publish('positionstoolbar.remove') 
    
    def on_tag_clicked(self, widget):
        pubsub.publish('positionstoolbar.tag')   
           
    def on_edit_clicked(self, widget):
        print "todo"


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
