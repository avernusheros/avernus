import gtk, os
from stocktracker.treeviews import Tree, get_name_string, datetime_format, get_datetime_string
from stocktracker import pubsub, config, objects
from stocktracker.plot import ChartWindow
from stocktracker.dialogs import SellDialog, NewWatchlistPositionDialog, SplitDialog, BuyDialog
from stocktracker.session import session
from stocktracker.gui_utils import ContextMenu


class PositionContextMenu(ContextMenu):
    def __init__(self, position):
        ContextMenu.__init__(self)
        if isinstance(position, objects.PortfolioPosition):
            type = 0
            remove_string = 'Sell'
        else:
            type = 1
            remove_string = 'Remove'
        self.position = position
        
        self.add_item(remove_string+' position',  self.__remove_position, 'gtk-remove')
        self.add_item(_('Edit position'),  self.__edit_position, 'gtk-edit')
        self.add_item(_('Chart position'),  self.__chart_position, 'gtk-info')
        
        if type == 0:
            self.add_item(_('Split position'),  self.__split_position, 'gtk-cut')
    
    def __remove_position(self, *arg):
        pubsub.publish('position_menu.remove', self.position)
    
    def __edit_position(self, *arg):
        pubsub.publish('position_menu.edit', self.position)

    def __split_position(self, *arg):
        pubsub.publish('position_menu.split', self.position)
    
    def __chart_position(self, *arg):
        pubsub.publish('position_menu.chart', self.position)
    

class PositionsToolbar(gtk.Toolbar):
    def __init__(self, container):
        gtk.Toolbar.__init__(self)
        self.container = container
        self.conditioned = []
        
        button = gtk.ToolButton('gtk-add')
        button.connect('clicked', self.on_add_clicked)
        button.set_tooltip_text('Buy a new position') 
        self.insert(button,-1)
        
        button = gtk.ToolButton('gtk-delete')
        #button.set_label('Remove tag'
        button.connect('clicked', self.on_remove_clicked)
        button.set_tooltip_text('Sell selected position') 
        self.conditioned.append(button)
        self.insert(button,-1)
        
        button = gtk.ToolButton('gtk-edit')
        #button.set_label('Remove tag'
        button.connect('clicked', self.on_edit_clicked)
        button.set_tooltip_text('Edit selected position') 
        self.insert(button,-1)
        self.conditioned.append(button)
        button.set_sensitive(False)
        
        button = gtk.ToolButton('gtk-paste')
        button.connect('clicked', self.on_tag_clicked)
        button.set_tooltip_text('Tag selected position') 
        self.conditioned.append(button)
        self.insert(button,-1)
        
        button = gtk.ToolButton('gtk-cut')
        button.connect('clicked', self.on_split_clicked)
        button.set_tooltip_text('Split selected position') 
        self.conditioned.append(button)
        self.insert(button,-1) 
        
        button = gtk.ToolButton('gtk-info')
        button.connect('clicked', self.on_chart_clicked)
        button.set_tooltip_text('Chart selected position')
        self.conditioned.append(button) 
        self.insert(button,-1)        
        
        self.insert(gtk.SeparatorToolItem(),-1)
        
        button = gtk.ToolButton('gtk-refresh')
        button.connect('clicked', self.on_update_clicked)
        button.set_tooltip_text('Update stock quotes') 
        self.insert(button,-1)
        
        self.on_unselect()
        pubsub.subscribe('positionstree.unselect', self.on_unselect)
        pubsub.subscribe('positionstree.select', self.on_select)
        
    def on_unselect(self):
        for button in self.conditioned:
            button.set_sensitive(False)       
        
    def on_select(self, obj):
        for button in self.conditioned:
            button.set_sensitive(True)
           
    def on_add_clicked(self, widget):
        pubsub.publish('positionstoolbar.add')  
      
    def on_update_clicked(self, widget):
        pubsub.publish('positionstoolbar.update', self.container)
        
    def on_remove_clicked(self, widget):
        pubsub.publish('positionstoolbar.remove') 
    
    def on_tag_clicked(self, widget):
        pubsub.publish('positionstoolbar.tag')   
           
    def on_edit_clicked(self, widget):
        #TODO
        pubsub.publish('positionstoolbar.edit')
        
    def on_split_clicked(self, widget):
        pubsub.publish('positionstoolbar.split')
        
    def on_chart_clicked(self, widget):
        pubsub.publish('positionstoolbar.chart')


class PositionsTree(Tree):
    def __init__(self, container):
        self.container = container
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
                     'type': 14,
                     'pf_percent': 15
                      }
        
        def float_to_string(column, cell, model, iter, user_data):
            text =  str(round(model.get_value(iter, user_data), 2))
            cell.set_property('text', text)
        
        def float_to_red_green_string(column, cell, model, iter, user_data):
            num = round(model.get_value(iter, user_data), 2)
            if num < 0:
                markup =  '<span foreground="red">'+ str(num) + '</span>'
            elif num > 0:
                markup =  '<span foreground="dark green">'+ str(num) + '</span>'
            else:
                markup =  str(num)
            cell.set_property('markup', markup)
        
        self.set_model(gtk.TreeStore(int, object,str, str, str,float, float, int, float, float, str, float, float, float, str, float))
        
        if self.container.type != 'watchlist':
            self.create_column(_('Shares'), 7)
        self.create_column(_('Name'), 2)
        if self.container.type != 'watchlist':
            col, cell = self.create_column(_('Portfolio %'), self.cols['pf_percent'])
            col.set_cell_data_func(cell, float_to_string, self.cols['pf_percent'])
        self.create_column(_('Type'), self.cols['type'])
        self.create_column(_('Start'), 3)
        if self.container.type != 'watchlist':
            col, cell = self.create_column(_('Buy value'), 8)
            col.set_cell_data_func(cell, float_to_string, 8)
        self.create_column(_('Last price'), 4)
        col, cell = self.create_column(_('Change'), 5)
        col.set_cell_data_func(cell, float_to_red_green_string, 5)
        col, cell = self.create_column(_('Change %'), 13)
        col.set_cell_data_func(cell, float_to_red_green_string, 13)
        if self.container.type != 'watchlist':
            col, cell = self.create_column(_('Mkt value'), 9)
            col.set_cell_data_func(cell, float_to_string, 9)
        col, cell = self.create_column(_('Gain'), 6)
        col.set_cell_data_func(cell, float_to_red_green_string, 6)
        col, cell = self.create_column(_('Gain %'), 12)
        col.set_cell_data_func(cell, float_to_red_green_string, 12)
        if self.container.type != 'watchlist':
            col, cell = self.create_column(_('Day\'s gain'), 11)
            col.set_cell_data_func(cell, float_to_red_green_string, 11)
        col, cell = self.create_column(_('Tags'), 10)
        cell.set_property('editable', True)
        cell.connect('edited', self.on_tag_edited)
        
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
        
        self.get_model().set_sort_func(self.cols['start'], sort_start_price)
        self.get_model().set_sort_func(self.cols['last_price'], sort_current_price)

        self.set_rules_hint(True)
    
        self.load_positions()
        
        self.connect('button-press-event', self.on_button_press_event)
        self.connect('cursor_changed', self.on_cursor_changed)
        self.connect("destroy", self.on_destroy)
        
        self.subscriptions = (
            ('position.updated', self.on_position_updated),
            ('stock.updated', self.on_stock_updated),
            ('positionstoolbar.remove', self.on_remove_position),
            ('position_menu.remove', self.on_remove_position),
            ('positionstoolbar.add', self.on_add_position),
            ('position_menu.add', self.on_add_position),
            ('positionstoolbar.tag', self.on_tag),
            ('positionstoolbar.split', self.on_split),
            ('position_menu.split', self.on_split),
            ('positionstoolbar.chart', self.on_chart),
            ('position_menu.chart', self.on_chart),
            ('container.position.added', self.on_position_added),
            ('position.tags.changed', self.on_positon_tags_changed),
            ('container.position.removed', self.on_position_deleted),
            ('shortcut.update', self.on_update)
        )
        for topic, callback in self.subscriptions:
            pubsub.subscribe(topic, callback)
            
        self.selected_item = None
    
    def on_update(self):
        pubsub.publish('positionstoolbar.update', self.container)

    def on_button_press_event(self, widget, event):
        if event.button == 3:
            if self.selected_item is not None:
                obj, iter = self.selected_item
                PositionContextMenu(obj).show(event)

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
                row[self.cols['shares']] = item.quantity
    
    def on_positon_tags_changed(self, tags, item):
        row = self.find_position(item.id)
        if row:
            row[self.cols['tags']] = item.tags_string
    
    def on_stock_updated(self, item):
        row = self.find_position_from_stock(item.id)
        if row:
            row[self.cols['last_price']] = self.get_price_string(item)
            row[self.cols['change']] = row[1].current_change[0]
            row[self.cols['change_percent']] = row[1].current_change[1]
            row[self.cols['gain']] = row[1].gain[0]
            row[self.cols['gain_percent']] = row[1].gain[1]
            row[self.cols['days_gain']] = row[1].days_gain
            row[self.cols['mkt_value']] = round(row[1].cvalue,2)
                
    def on_position_added(self, item, container):
        if container.id == self.container.id:
            self.insert_position(item)
     
    def on_remove_position(self, position = None):
        if position is None:
            if self.selected_item is None:
                return
            position, iter = self.selected_item
        if self.container.type == 'watchlist':
            dlg = gtk.MessageDialog(None, 
                 gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION, 
                    gtk.BUTTONS_OK_CANCEL, _("Are you sure?"))
            response = dlg.run()
            dlg.destroy()
            if response == gtk.RESPONSE_OK:
                self.container.remove_position(position)
        elif self.container.type == 'portfolio':
            SellDialog(self.container, position)    
    
    def on_position_deleted(self, pos, pf):
        if pf.id == self.container.id:
            row = self.find_position(pos.id)
            if row is not None:
                self.get_model().remove(row.iter)   
       
    def on_add_position(self):
        if self.container.type == 'watchlist':
            NewWatchlistPositionDialog(self.container)  
        elif self.container.type == 'portfolio':
            BuyDialog(self.container)
    
    def on_split(self, position = None):
        if position is None:
            if self.selected_item is None:
                return
            position, iter = self.selected_item
        d = SplitDialog(position)
        
    def on_chart(self, position = None):
        if position is None:
            if self.selected_item is None:
                return
            position, iter = self.selected_item
        d = ChartWindow(position.stock)
        
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
            if isinstance(obj, objects.Position):
                pubsub.publish('positionstree.select', obj)
                return
        pubsub.publish('positionstree.unselect')
            
    def get_price_string(self, item):
        if item.price is None:
            return 'n/a'
        return str(round(item.price,2)) +'\n' +'<small>'+get_datetime_string(item.date)+'</small>'
        
    def insert_position(self, position):
        if position.quantity != 0:
            stock = session['model'].stocks[position.stock_id]
            gain = position.gain
            c_change = position.current_change
            self.get_model().append(None, [position.id, 
                                           position, 
                                           get_name_string(stock), 
                                           self.get_price_string(position), 
                                           self.get_price_string(stock), 
                                           c_change[0],
                                           gain[0],
                                           position.quantity,
                                           position.bvalue,
                                           position.cvalue,
                                           position.tags_string,
                                           position.days_gain,
                                           gain[1],
                                           c_change[1],
                                           position.type_string,
                                           100 * position.cvalue / self.container.total])

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
    def __init__(self, pf):
        gtk.VBox.__init__(self)
        self.pf = pf
        positions_tree = PositionsTree(pf)
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
        hbox.pack_start(label, expand = False, fill = False)
        
        if pf.type == 'watchlist' or pf.type == 'portfolio':
            hbox.pack_start(gtk.VSeparator(), expand = False, fill = False)
            self.last_update_label = label = gtk.Label()
            hbox.pack_start(label, expand = False, fill = False)
        sw = gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.add(positions_tree)
        self.pack_start(hbox, expand=False, fill=False)
        self.pack_start(sw)
        
        self.on_container_update(self.pf)
        pubsub.subscribe('container.updated', self.on_container_update)
       
        self.show_all()
        
    def on_container_update(self, container):
        if self.pf == container:
            text = '<b>' + _('Day\'s gain')+'</b>\n'+self.get_change_string(self.pf.current_change)
            self.today_label.set_markup(text)
            text = '<b>'+_('Gain')+'</b>\n'+self.get_change_string(self.pf.overall_change)
            self.overall_label.set_markup(text)
            
            if self.pf.type == 'portfolio':
                text = '<b>'+_('Investments')+'</b> :'+str(round(self.pf.total,2))
                text += '\n<b>'+_('Cash')+'</b> :'+str(round(self.pf.cash,2))
                self.total_label.set_markup(text)
            else:
                text = '<b>'+_('Total')+'</b>\n'+str(round(self.pf.total,2))
                self.total_label.set_markup(text)
            
            if self.pf.type == 'watchlist' or self.pf.type == 'portfolio':
                text = '<b>'+_('Last update')+'</b>\n'+datetime_format(self.pf.last_update)
                self.last_update_label.set_markup(text)
        
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
