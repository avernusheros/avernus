import gtk
from stocktracker.treeviews import Tree, get_name_string, get_datetime_string, get_green_red_string
from stocktracker import pubsub, dialogs

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
        button.connect('clicked', self.on_tag_clicked)
        self.insert(button,-1)
        
        button = gtk.ToolButton('gtk-cut')
        button.connect('clicked', self.on_split_clicked)
        self.insert(button,-1)        
        
        self.insert(gtk.SeparatorToolItem(),-1)
        
        button = gtk.ToolButton('gtk-refresh')
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
        #TODO
        pubsub.publish('positionstoolbar.edit')
        
    def on_split_clicked(self, widget):
        pubsub.publish('positionstoolbar.split')

class PositionsTree(Tree):
    def __init__(self, container, model, type):
        #type 0=wl 1=pf
        self.model = model
        self.container = container
        self.type = type
        Tree.__init__(self)
        self.cols = {'id':0,
                     'obj':1,
                     'name':2, 
                     'start':3, 
                     'last_price':4, 
                     'change':5, 
                     'gain':6,
                     'shares':7, 
                     'buy_value':8,
                     'mkt_value':9,
                     'tags':10,
                     'days_gain':11,
                     'gain_percent':12,
                     'change_percent':13,
                     'type': 14
                      }
        
        #id, object, name, price, change
        self.set_model(gtk.TreeStore(int, object,str, str, str,str, str, int, str, str, str, str, str, str, str))
        
        if type == 1 or type == 2:
            self.create_column(_('Shares'), 7)
        self.create_column(_('Name'), 2)
        self.create_column(_('Type'), self.cols['type'])
        self.create_column(_('Start'), 3)
        if type == 1 or type == 2:
            self.create_column(_('Buy value'), 8)
        self.create_column(_('Last price'), 4)
        self.create_column(_('Change'), 5)
        self.create_column(_('Change %'), 13)
        if type == 1 or type == 2:
            self.create_column(_('Mkt value'), 9)
        
        self.create_column(_('Gain'), 6)
        self.create_column(_('Gain %'), 12)
        if type == 1 or type == 2:
            self.create_column(_('Day\'s gain'), 11)
        col, cell = self.create_column(_('Tags'), 10)
        cell.set_property('editable', True)
        cell.connect('edited', self.on_tag_edited)
        
        def sort_string_float(model, iter1, iter2, col):
            item1 = float(model.get_value(iter1, col))
            item2 = float(model.get_value(iter2, col))
            if item1 == item2: return 0
            elif item1 < item2: return -1
            else: return 1
        
        def sort_start_price(model, iter1, iter2):
            item1 = model.get_value(iter1, self.cols['obj'])
            item2 = model.get_value(iter2, self.cols['obj'])
            if item1.price == item2.price: return 0
            elif item1.price < item2.price: return -1
            else: return 1
        
        def sort_current_price(model, iter1, iter2):
            item1 = model.get_value(iter1, self.cols['obj'])
            item2 = model.get_value(iter2, self.cols['obj'])
            if item1.current_price == item2.current_price: return 0
            elif item1.current_price < item2.current_price: return -1
            else: return 1
        
        def sort_days_gain(model, iter1, iter2):
            item1 = model.get_value(iter1, self.cols['obj'])
            item2 = model.get_value(iter2, self.cols['obj'])
            if item1.days_gain == item2.days_gain: return 0
            elif item1.days_gain < item2.days_gain: return -1
            else: return 1

        def sort_gain(model, iter1, iter2, i):
            item1 = model.get_value(iter1, self.cols['obj'])
            item2 = model.get_value(iter2, self.cols['obj'])
            if item1.gain[i] == item2.gain[i]: return 0
            elif item1.gain[i] < item2.gain[i]: return -1
            else: return 1
        
        def sort_change(model, iter1, iter2, i):
            item1 = model.get_value(iter1, self.cols['obj'])
            item2 = model.get_value(iter2, self.cols['obj'])
            if item1.current_change[i] == item2.current_change[i]: return 0
            elif item1.current_change[i] < item2.current_change[i]: return -1
            else: return 1
                
        self.get_model().set_sort_func(self.cols['buy_value'], sort_string_float, self.cols['buy_value'])
        self.get_model().set_sort_func(self.cols['mkt_value'], sort_string_float, self.cols['mkt_value'])
        self.get_model().set_sort_func(self.cols['days_gain'], sort_days_gain)
        self.get_model().set_sort_func(self.cols['gain'], sort_gain, 0)
        self.get_model().set_sort_func(self.cols['gain_percent'], sort_gain, 1)
        self.get_model().set_sort_func(self.cols['change'], sort_change, 0)
        self.get_model().set_sort_func(self.cols['change_percent'], sort_change, 1)
        self.get_model().set_sort_func(self.cols['start'], sort_start_price)
        self.get_model().set_sort_func(self.cols['last_price'], sort_current_price)

        self.load_positions()
        
        self.connect('cursor_changed', self.on_cursor_changed)
        self.connect("destroy", self.on_destroy)
        
        self.subscriptions = (
            ('position.updated', self.on_position_updated),
            ('stock.updated', self.on_stock_updated),
            ('positionstoolbar.remove', self.on_remove_position),
            ('positionstoolbar.add', self.on_add_position),
            ('positionstoolbar.tag', self.on_tag),
            ('positionstoolbar.tag', self.on_split),
            ('position.created', self.on_position_created),
            ('position.tags.changed', self.on_positon_tags_changed),
            ('container.position.removed', self.on_position_deleted)
        )
        for topic, callback in self.subscriptions:
            pubsub.subscribe(topic, callback)
            
        self.selected_item = None

    def on_destroy(self, x):
        for topic, callback in self.subscriptions:
            pubsub.unsubscribe(topic, callback)

    def load_positions(self):
        for pos in self.container:
            self.insert_position(pos)
    
    def on_tag_edited(self, cellrenderertext, path, new_text):
        if self.selected_item is None:
            return
        obj, iter = self.selected_item
        obj.tag(new_text.split())
    
    def on_position_updated(self, item):
        row = self.find_position(item.id)
        if row:
            if item.quantity == 0:
                self.get_model().remove(row.iter)
            else:
                row[self.cols['quantity']] = item.quantity
    
    def on_positon_tags_changed(self, tags, item):
        row = self.find_position(item.id)
        if row:
            row[self.cols['tags']] = item.tags_string
    
    def on_stock_updated(self, item):
        row = self.find_position_from_stock(item.id)
        if row:
            row[self.cols['last_price']] = self.get_price_string(item)
            row[self.cols['change']] = get_green_red_string(row[1].current_change[0])
            row[self.cols['change_percent']] = get_green_red_string(row[1].current_change[1])
            row[self.cols['gain']] = get_green_red_string(row[1].gain[0])
            row[self.cols['gain_percent']] = get_green_red_string(row[1].gain[1])
            row[self.cols['days_gain']] = get_green_red_string(row[1].days_gain)
            row[self.cols['mkt_value']] = str(round(row[1].cvalue,2))
                
    def on_position_created(self, item):
        if item.container_id == self.container.id:
            self.insert_position(item)
     
    def on_remove_position(self):
        if self.selected_item is None:
            return
        obj, iter = self.selected_item
        if self.type == 0:
            dlg = gtk.MessageDialog(None, 
                 gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION, 
                    gtk.BUTTONS_OK_CANCEL, _("Are you sure?"))
            response = dlg.run()
            dlg.destroy()
            if response == gtk.RESPONSE_OK:
                self.container.remove_position(obj)
        elif self.type == 1:
            dialogs.SellDialog(self.container, obj)    
    
    def on_position_deleted(self, pos, pf):
        if pf.id == self.container.id:
            row = self.find_position(pos.id)
            if row is not None:
                self.get_model().remove(row.iter)   
       
    def on_add_position(self):
        if self.type == 0:
            dialogs.NewWatchlistPositionDialog(self.container, self.model)  
        elif self.type == 1:
            dialogs.BuyDialog(self.container, self.model)
    
    def on_split(self):
        if self.selected_item is None:
            return
        obj, iter = self.selected_item
        d = dialogs.SplitDialog(obj)
        
    def on_tag(self):
        if self.selected_item is None:
            return
        path, col = self.get_cursor()
        obj, iter = self.selected_item
        cell = self.get_column(8).get_cell_renderers()[0]
        self.set_cursor(path, focus_column = self.get_column(8), start_editing=True)
        #self.grab_focus()
        
    def on_cursor_changed(self, widget):
        #Get the current selection in the gtk.TreeView
        selection = widget.get_selection()
        # Get the selection iter
        model, selection_iter = selection.get_selected()
        if (selection_iter and model):
            #Something is selected so get the object
            obj = model.get_value(selection_iter, 1)
            self.selected_item = obj, selection_iter
            pubsub.publish('watchlistpositionstree.selection', obj)   
            
    def get_price_string(self, item):
        if item.price is None:
            return 'n/a'
        return str(round(item.price,2)) +'\n' +'<small>'+get_datetime_string(item.date)+'</small>'
        
    def insert_position(self, position):
        if position.quantity != 0:
            stock = self.model.stocks[position.stock_id]
            gain = position.gain
            c_change = position.current_change
            self.get_model().append(None, [position.id, 
                                           position, 
                                           get_name_string(stock), 
                                           self.get_price_string(position), 
                                           self.get_price_string(stock), 
                                           get_green_red_string(c_change[0]),
                                           get_green_red_string(gain[0]),
                                           position.quantity,
                                           str(round(position.bvalue,2)),
                                           str(round(position.cvalue,2)),
                                           position.tags_string,
                                           get_green_red_string(position.days_gain),
                                           get_green_red_string(gain[1]),
                                           get_green_red_string(c_change[1]),
                                           position.type_string])

    def find_position_from_stock(self, sid):
        def search(rows):
            if not rows: return None
            for row in rows:
                if row[1].stock_id == sid:
                    return row 
                result = search(row.iterchildren())
                if result: return result
            return None
        return search(self.get_model())
        
    def find_position(self, pid):
        def search(rows):
            if not rows: return None
            for row in rows:
                if row[0] == pid:
                    return row 
                result = search(row.iterchildren())
                if result: return result
            return None
        return search(self.get_model())
        
    def __del__(self):
        pass



class PositionsTab(gtk.VBox):
    def __init__(self, pf, model, type):
        gtk.VBox.__init__(self)
        self.pf = pf
        positions_tree = PositionsTree(pf, model, type)
        hbox = gtk.HBox()
        tb = PositionsToolbar(pf)
        hbox.pack_start(tb, expand = True, fill = True)
        
        self.total_label = label = gtk.Label()
        hbox.pack_start(label)
        hbox.pack_start(gtk.VSeparator(), expand = False, fill = False)
        self.today_label = label = gtk.Label()
        hbox.pack_start(label)
        hbox.pack_start(gtk.VSeparator(), expand = False, fill = False)
        self.overall_label = label = gtk.Label()
        hbox.pack_start(label)
        sw = gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.add(positions_tree)
        self.pack_start(hbox, expand=False, fill=False)
        self.pack_start(sw)
        
        self.on_stock_update()
        pubsub.subscribe('stock.updated', self.on_stock_update)
       
        self.show_all()
        
    def on_stock_update(self, item = None):
        text = '<b>' + _('Day\'s gain')+'</b>\n'+self.get_change_string(self.pf.current_change)
        self.today_label.set_markup(text)
        text = '<b>'+_('Gain')+'</b>\n'+self.get_change_string(self.pf.overall_change)
        self.overall_label.set_markup(text)
        text = '<b>'+_('Total')+'</b>\n'+str(round(self.pf.total,2))
        self.total_label.set_markup(text)
        
    def get_change_string(self, item):
        change, percent = item
        if change is None:
            return 'n/a'
        text = str(percent) + '%' + ' | ' + str(round(change,2))
        if change < 0.0:
            text = '<span foreground="red">'+ text + '</span>'
        else:
            text = '<span foreground="dark green">'+ text + '</span>'
        return text