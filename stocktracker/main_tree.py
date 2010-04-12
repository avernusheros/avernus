#!/usr/bin/env python

import gtk
from stocktracker.treeviews import Tree
from stocktracker import pubsub, model
from stocktracker.gui_utils import ContextMenu
from datetime import datetime


class Category(object):
    def __init__(self, name):
        self.name = name

class MainTreeBox(gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self)

        main_tree = MainTree()
        self.pack_start(main_tree)
        main_tree_toolbar = MainTreeToolbar()
        self.pack_start(main_tree_toolbar, expand=False, fill=False)


class MainTree(Tree):
    def __init__(self):
        Tree.__init__(self)
        #object, icon, name
        self.set_model(gtk.TreeStore(object,str, str))
        
        self.set_headers_visible(False)
             
        column = gtk.TreeViewColumn()
        # Icon Renderer
        renderer = gtk.CellRendererPixbuf()
        column.pack_start(renderer, expand = False)
        column.add_attribute(renderer, "pixbuf", 1)
        column.set_attributes(renderer, stock_id=1)

        # Text Renderer
        renderer = gtk.CellRendererText()
        column.pack_start(renderer, expand = True)
        column.add_attribute(renderer, "markup", 2)
        self.append_column(column)
        self.on_clear()
        
        self.connect('button-press-event', self.on_button_press_event)
        self.connect('cursor_changed', self.on_cursor_changed)
        pubsub.subscribe("watchlist.created", self.insert_watchlist)
        pubsub.subscribe("portfolio.created", self.insert_portfolio)
        pubsub.subscribe("container.edited", self.on_updated)
        pubsub.subscribe("tag.created", self.insert_tag)
        pubsub.subscribe("tag.updated", self.on_updated)
        pubsub.subscribe("maintoolbar.remove", self.on_remove)
        pubsub.subscribe("maincontextmenu.remove", self.on_remove)
        pubsub.subscribe('maintoolbar.edit', self.on_edit)
        pubsub.subscribe('maincontextmenu.edit', self.on_edit)
        pubsub.subscribe('clear!', self.on_clear)
        
        #loading portfolios...
        for pf in model.Portfolio.query.all():
            self.insert_portfolio(pf)
        for wl in model.Watchlist.query.all():
            self.insert_watchlist(wl)
        for tag in model.Tag.query.all():
            self.insert_tag(tag)
        for index in model.Index.query.all():
            self.insert_index(index)
        self.expand_all()
        
    
    def on_clear(self):
        self.insert_categories()
        self.selected_item = None

    def on_button_press_event(self, widget, event):
        if event.button == 3:
            if self.selected_item is not None:
                obj, iter = self.selected_item
                ContainerContextMenu(obj).show(event)

    def insert_categories(self):
        self.pf_iter = self.get_model().append(None, [Category('Portfolios'),'gtk-dnd-multiple', _("<b>Portfolios</b>")])
        self.wl_iter = self.get_model().append(None, [Category('Watchlists'),'gtk-dnd-multiple', _("<b>Watchlists</b>")])
        self.tag_iter = self.get_model().append(None, [Category('Tags'),'gtk-dnd-multiple', _("<b>Tags</b>")])
        self.index_iter = self.get_model().append(None, [Category('Indices'),'gtk-dnd-multiple', _("<b>Indices</b>")])

    def insert_watchlist(self, item):
        self.get_model().append(self.wl_iter, [item, 'gtk-dnd', item.name])
    
    def insert_portfolio(self, item):
        self.get_model().append(self.pf_iter, [item, 'gtk-dnd', item.name])
         
    def insert_tag(self, item):
        self.get_model().append(self.tag_iter, [item, 'gtk-dnd', item.name])
    
    def insert_index(self, item):
        self.get_model().append(self.index_iter, [item, 'gtk-dnd', item.name])
         
    def on_remove(self):
        if self.selected_item is None:
            return
        obj, iter = self.selected_item
        if isinstance(obj, model.Container):
            dlg = gtk.MessageDialog(None, 
                 gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION, 
                 gtk.BUTTONS_OK_CANCEL, 
                 _("Permanently delete ")+obj.name+'?')
            response = dlg.run()
            dlg.destroy()
            if response == gtk.RESPONSE_OK:
                obj.delete()
                self.get_model().remove(iter)  
    
    def on_updated(self, item):
        obj, iter = self.selected_item
        row = self.get_model()[iter]
        if row: 
            #row[1] = item
            row[2] = item.name

    def on_cursor_changed(self, widget):
        #Get the current selection in the gtk.TreeView
        selection = widget.get_selection()
        # Get the selection iter
        treestore, selection_iter = selection.get_selected()
        if (selection_iter and treestore):
            #Something is selected so get the object
            obj = treestore.get_value(selection_iter, 0)
            if not isinstance(obj, Category):
                if self.selected_item is None or self.selected_item[0] != obj:
                    self.selected_item = obj, selection_iter
                    pubsub.publish('maintree.select', obj)   
                return
        self.selected_item = None
        return pubsub.publish('maintree.unselect')
        
    def on_edit(self):
        if self.selected_item is None:
            return
        obj, row = self.selected_item
        if isinstance(obj, model.Portfolio):
            EditPortfolio(obj)
        elif isinstance(obj, model.Watchlist):# or obj.type == 'tag':
            EditWatchlist(obj)

       


class MainTreeToolbar(gtk.Toolbar):
    def __init__(self):
        gtk.Toolbar.__init__(self)
        self.conditioned = []
        
        button = gtk.ToolButton('gtk-add')
        button.connect('clicked', self.on_add_clicked)
        button.set_tooltip_text('Add a new portfolio or watchlist') 
        self.insert(button,-1)
        
        button = gtk.ToolButton('gtk-delete')
        #button.set_label('Remove tag'
        button.connect('clicked', self.on_remove_clicked)
        button.set_tooltip_text('Delete selected portfolio or watchlist')
        self.conditioned.append(button) 
        self.insert(button,-1)
        
        button = gtk.ToolButton('gtk-edit')
        #button.set_label('Remove tag'
        button.connect('clicked', self.on_edit_clicked)
        button.set_tooltip_text('Edit Selected portfolio or watchlist')
        self.conditioned.append(button) 
        self.insert(button,-1)
        
        self.on_unselect()
        pubsub.subscribe('maintree.unselect', self.on_unselect)
        pubsub.subscribe('maintree.select', self.on_select)
         
    def on_unselect(self):
        for button in self.conditioned:
            button.set_sensitive(False)       
        
    def on_select(self, obj):
        for button in self.conditioned:
            button.set_sensitive(True)
             
    def on_add_clicked(self, widget):
        NewContainerDialog()
    
    def on_remove_clicked(self, widget):
        pubsub.publish('maintoolbar.remove')  
           
    def on_edit_clicked(self, widget):
        pubsub.publish('maintoolbar.edit')


class EditWatchlist(gtk.Dialog):
    def __init__(self, wl):
        gtk.Dialog.__init__(self, _("Edit..."), None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        
        self.wl = wl
        vbox = self.get_content_area()
        
        #name entry
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        label = gtk.Label(_('Name:'))
        hbox.pack_start(label)
        self.name_entry = gtk.Entry()
        self.name_entry.set_text(wl.name)
        hbox.pack_start(self.name_entry)

        self.show_all()
        self.name_entry.connect("activate", self.process_result)
        response = self.run()  
        self.process_result(response = response)

    def process_result(self, widget=None, response = gtk.RESPONSE_ACCEPT):
        if response == gtk.RESPONSE_ACCEPT:
            self.wl.name = self.name_entry.get_text()   
            pubsub.publish("container.edited", self.wl) 
        self.destroy()


class EditPortfolio(gtk.Dialog):
    def __init__(self, pf):
        gtk.Dialog.__init__(self, _("Edit..."), None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        
        self.pf = pf
        vbox = self.get_content_area()
        table = gtk.Table()
        vbox.pack_start(table)
        
        #name entry
        label = gtk.Label(_('Name:'))
        table.attach(label, 0,1,0,1)
        self.name_entry = gtk.Entry()
        self.name_entry.set_text(pf.name)
        table.attach(self.name_entry,1,2,0,1)
        
        #cash entry
        label = gtk.Label(_('Cash:'))
        table.attach(label, 0,1,1,2)
        self.cash_entry = gtk.SpinButton(gtk.Adjustment(lower=-999999999, upper=999999999,step_incr=10, value = pf.cash), digits=2)
        table.attach(self.cash_entry,1,2,1,2)
        
        self.show_all()
        self.name_entry.connect("activate", self.process_result)
        response = self.run()  
        self.process_result(response = response)

    def process_result(self, widget=None, response = gtk.RESPONSE_ACCEPT):
        if response == gtk.RESPONSE_ACCEPT:
            self.pf.name = self.name_entry.get_text()
            self.pf.cash = self.cash_entry.get_value()
            pubsub.publish("container.edited", self.pf)       
        self.destroy()


class NewContainerDialog(gtk.Dialog):
    def __init__(self):
        gtk.Dialog.__init__(self, _("Create..."), None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        vbox = self.get_content_area()
        
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        self.radiobutton = button = gtk.RadioButton(None, _("Portfolio"))
        hbox.pack_start(button, True, True, 0)
        
        button = gtk.RadioButton(button, _("Watchlist"))
        hbox.pack_start(button, True, True, 0)
               
        #name entry
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        label = gtk.Label(_('Name:'))
        hbox.pack_start(label)
        self.name_entry = gtk.Entry()
        hbox.pack_start(self.name_entry)

        self.show_all()
        response = self.run()  
        self.process_result(response)
        
        self.destroy()

    def process_result(self, response):
        if response == gtk.RESPONSE_ACCEPT:
            #grab the name
            name = self.name_entry.get_text()
            if self.radiobutton.get_active():
                model.Portfolio(name = name, cash=0.0)
            else:
                #create wathclist
                model.Watchlist(name = name)

class ContainerContextMenu(ContextMenu):
    def __init__(self, container):
        ContextMenu.__init__(self)
        self.container = container
        
        self.add_item(_('Remove '),  self.__remove_container, 'gtk-remove')
        self.add_item(_('Edit '),  self.__edit_container, 'gtk-edit')
        self.add_item('----')
        
        if isinstance(container, model.Portfolio):
            self.add_item(_('Deposit cash'),  self.__deposit_cash, 'gtk-add')
            self.add_item(_('Withdraw cash'),  self.__withdraw_cash, 'gtk-remove')

    def __remove_container(self, *arg):
        pubsub.publish('maincontextmenu.remove')
        
    def __edit_container(self, *arg):
        pubsub.publish('maincontextmenu.edit')
        
    def __deposit_cash(self, *arg):
        CashDialog(self.container, 0)
        
    def __withdraw_cash(self, *arg):
        CashDialog(self.container, 1)        


class CashDialog(gtk.Dialog):
    def __init__(self, pf, type = 0):  #0 deposit, 1 withdraw
        self.action_type = type
        if type == 0:
            text = _("Deposit cash")
        else: text = _("Withdraw cash")
        gtk.Dialog.__init__(self, text, None
                            , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        
        self.pf = pf
        vbox = self.get_content_area()
        
        hbox = gtk.HBox()
        vbox.pack_start(hbox)
        hbox.pack_start(gtk.Label(_('Amount:')))
        self.amount_entry = gtk.SpinButton(gtk.Adjustment(lower=0, upper=100000,step_incr=0.1, value = 1.0), digits=2)
        hbox.pack_start(self.amount_entry)
        
        self.calendar = gtk.Calendar()
        vbox.pack_start(self.calendar)

        self.show_all()
        response = self.run()  
        self.process_result(response = response)
        self.destroy()

    def process_result(self, widget=None, response = gtk.RESPONSE_ACCEPT):
        if response == gtk.RESPONSE_ACCEPT:
            amount = self.amount_entry.get_value()  
            year, month, day = self.calendar.get_date()
            date = datetime(year, month+1, day)
            if self.action_type == 0:
                self.pf.cash += amount
                ta = model.PortfolioTransaction(date=date, portfolio=self.pf, type=3, price=amount)
            else:
                self.pf.cash -= amount
                ta = model.PortfolioTransaction(date=date, portfolio=self.pf, type=4, price=amount)
            pubsub.publish('portfolio.transaction.added', self.pf, ta)
