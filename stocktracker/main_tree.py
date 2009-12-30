import gtk
from stocktracker.treeviews import Tree
from stocktracker import pubsub, objects
from stocktracker.gui_utils import ContextMenu
from session import session

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
        #id, object, icon, name
        self.set_model(gtk.TreeStore(int, object,gtk.gdk.Pixbuf, str))
        
        self.set_headers_visible(False)
             
        column = gtk.TreeViewColumn()
        # Icon Renderer
        renderer = gtk.CellRendererPixbuf()
        column.pack_start(renderer, expand = False)
        column.add_attribute(renderer, "pixbuf", 2)
        # Text Renderer
        renderer = gtk.CellRendererText()
        column.pack_start(renderer, expand = True)
        column.add_attribute(renderer, "markup", 3)
        self.append_column(column)
        self.on_clear()
        
        self.connect('button-press-event', self.on_button_press_event)
        self.connect('cursor_changed', self.on_cursor_changed)
        pubsub.subscribe("watchlist.created", self.insert_watchlist)
        pubsub.subscribe("portfolio.created", self.insert_portfolio)
        pubsub.subscribe("container.updated.name", self.on_updated)
        pubsub.subscribe("tag.created", self.insert_tag)
        pubsub.subscribe("maintoolbar.remove", self.on_remove)
        pubsub.subscribe("maincontextmenu.remove", self.on_remove)
        pubsub.subscribe('maintoolbar.edit', self.on_edit)
        pubsub.subscribe('maincontextmenu.edit', self.on_edit)
        pubsub.subscribe("model.database.loaded", self.on_database_loaded)
                
        pubsub.subscribe('clear!', self.on_clear)
    
    def on_clear(self):
        self.insert_categories()
        self.selected_item = None

    def on_button_press_event(self, widget, event):
        if event.button == 3:
            if self.selected_item is not None:
                obj, iter = self.selected_item
                ContainerContextMenu(obj).show(event)

    def insert_categories(self):
        self.pf_iter = self.get_model().append(None, [-1, Category('Portfolios'),None,_("<b>Portfolios</b>")])
        self.wl_iter = self.get_model().append(None, [-1, Category('Watchlists'),None,_("<b>Watchlists</b>")])
        self.tag_iter = self.get_model().append(None, [-1, Category('Tags'),None,_("<b>Tags</b>")])

    def insert_watchlist(self, item):
        self.get_model().append(self.wl_iter, [item.id, item, None, item.name])
    
    def insert_portfolio(self, item):
        self.get_model().append(self.pf_iter, [item.id, item, None, item.name])
         
    def insert_tag(self, item):
        self.get_model().append(self.tag_iter, [item.id, item, None, item.name])
         
    def on_remove(self):
        if self.selected_item is None:
            return
        obj, iter = self.selected_item
        if isinstance(obj, objects.Watchlist) or isinstance(obj, objects.Portfolio) or isinstance(obj, objects.Tag):
            dlg = gtk.MessageDialog(None, 
                 gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION, 
                 gtk.BUTTONS_OK_CANCEL, 
                 _("Permanently delete ")+obj.type+' '+obj.name+'?')
            response = dlg.run()
            dlg.destroy()
            if response == gtk.RESPONSE_OK:
                session['model'].remove(obj)
                self.get_model().remove(iter)  
    
    def on_updated(self, item):
        row = self.find_item(item.id, item.type)
        if row: 
            row[1] = item
            row[3] = item.name
    
    def on_cursor_changed(self, widget):
        #Get the current selection in the gtk.TreeView
        selection = widget.get_selection()
        # Get the selection iter
        model, selection_iter = selection.get_selected()
        if (selection_iter and model):
            #Something is selected so get the object
            obj = model.get_value(selection_iter, 1)
            if not isinstance(obj, Category):
                self.selected_item = obj, selection_iter
                pubsub.publish('maintree.selection', obj)        
        
    def on_edit(self):
        if self.selected_item is None:
            return
        obj, iter = self.selected_item
        if isinstance(obj, objects.Watchlist):
            EditWatchlist(obj)
        elif isinstance(obj, objects.Portfolio):
            EditPortfolio(obj)

    def on_database_loaded(self):
        self.expand_all()
    


class MainTreeToolbar(gtk.Toolbar):
    def __init__(self):
        gtk.Toolbar.__init__(self)
        
        button = gtk.ToolButton('gtk-add')
        button.connect('clicked', self.on_add_clicked)
        button.set_tooltip_text('Add a new portfolio or watchlist') 
        self.insert(button,-1)
        
        button = gtk.ToolButton('gtk-delete')
        #button.set_label('Remove tag'
        button.connect('clicked', self.on_remove_clicked)
        button.set_tooltip_text('Delete selected portfolio or watchlist') 
        self.insert(button,-1)
        
        button = gtk.ToolButton('gtk-edit')
        #button.set_label('Remove tag'
        button.connect('clicked', self.on_edit_clicked)
        button.set_tooltip_text('Edit Selected portfolio or watchlist') 
        self.insert(button,-1)
         
             
    def on_add_clicked(self, widget):
        NewContainerDialog()
    
    def on_remove_clicked(self, widget):
        pubsub.publish('maintoolbar.remove')  
           
    def on_edit_clicked(self, widget):
        pubsub.publish('maintoolbar.edit')


class EditWatchlist(gtk.Dialog):
    def __init__(self, wl):
        gtk.Dialog.__init__(self, _("Edit..."), session['main']
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
        self.destroy()


class EditPortfolio(gtk.Dialog):
    def __init__(self, pf):
        gtk.Dialog.__init__(self, _("Edit..."), session['main']
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
        self.cash_entry = gtk.SpinButton(gtk.Adjustment(lower=-9999999999, upper=9999999999, step_incr=1, value = pf.cash), digits=2)
        table.attach(self.cash_entry,1,2,1,2)
        
        self.show_all()
        self.name_entry.connect("activate", self.process_result)
        response = self.run()  
        self.process_result(response = response)

    def process_result(self, widget=None, response = gtk.RESPONSE_ACCEPT):
        if response == gtk.RESPONSE_ACCEPT:
            self.pf.name = self.name_entry.get_text()
            self.pf.cash = self.cash_entry.get_value()    
        self.destroy()

class NewContainerDialog(gtk.Dialog):
    def __init__(self):
        gtk.Dialog.__init__(self, _("Create..."), session['main']
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
                session['model'].create_portfolio(name)
            else:
                #create wathclist
                session['model'].create_watchlist(name)

class ContainerContextMenu(ContextMenu):
    def __init__(self, container):
        ContextMenu.__init__(self)
        
        mi = gtk.MenuItem(_('Remove ')+container.type)
        mi.connect('activate',  self.__remove_container)
        self.append(mi)
        
        mi = gtk.MenuItem(_('Edit ')+container.type)
        mi.connect('activate',  self.__edit_container)
        self.append(mi)

    def __remove_container(self, *arg):
        pubsub.publish('maincontextmenu.remove')
        
    def __edit_container(self, *arg):
        pubsub.publish('maincontextmenu.edit')
