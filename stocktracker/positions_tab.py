#!/usr/bin/env python

import gtk
from stocktracker.treeviews import Tree
from stocktracker import pubsub, model
from stocktracker.plot import ChartWindow
from stocktracker.dialogs import SellDialog, NewWatchlistPositionDialog, SplitDialog, BuyDialog
from stocktracker.gui_utils import ContextMenu, float_to_red_green_string, float_to_string, get_price_string, get_name_string, datetime_format

class PositionContextMenu(ContextMenu):
    def __init__(self, position):
        ContextMenu.__init__(self)
        if isinstance(position, model.PortfolioPosition):
            type = 0
            remove_string = 'Sell'
        else:
            type = 1
            remove_string = 'Remove'
        self.position = position
        
        self.add_item(remove_string+' position',  self.__remove_position, 'gtk-remove')
        self.add_item(_('Edit position'),  self.__edit_position, 'gtk-edit')
        self.add_item(_('Chart position'),  self.on_chart_position, 'gtk-info')
        
        if type == 0:
            self.add_item(_('Split position'),  self.__split_position, 'gtk-cut')
    
    def __remove_position(self, *arg):
        pubsub.publish('position_menu.remove', self.position)
    
    def __edit_position(self, *arg):
        pubsub.publish('position_menu.edit', self.position)

    def __split_position(self, *arg):
        pubsub.publish('position_menu.split', self.position)
    
    def on_chart_position(self, *arg):
        ChartWindow(self.position.stock)
    

class PositionsToolbar(gtk.Toolbar):
    def __init__(self, container, tree):
        gtk.Toolbar.__init__(self)
        self.container = container
        self.tree = tree
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
        self.container.update_positions()
        
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
        if self.tree.selected_item is None:
            return
        position, iter = self.tree.selected_item
        d = ChartWindow(position.stock)


class PositionsTree(Tree):
    def __init__(self, container):
        self.container = container
        Tree.__init__(self)
        self.cols = {'obj':0,
                     'name':1, 
                     'start':2, 
                     'last_price':3, 
                     'change':4, 
                     'gain':5,
                     'shares':6, 
                     'buy_value':7,
                     'mkt_value':8,
                     'tags':9,
                     'days_gain':10,
                     'gain_percent':11,
                     'change_percent':12,
                     'type': 13,
                     'pf_percent': 14
                      }
        
        
        self.set_model(gtk.TreeStore(object,str, str, str,float, float, int, float, float, str, float, float, float, str, float))
        
        if not isinstance(self.container, model.Watchlist):
            self.create_column(_('Shares'), self.cols['shares'])
        self.create_column(_('Name'), self.cols['name'])
        if not isinstance(self.container, model.Watchlist):
            col, cell = self.create_column(_('Portfolio %'), self.cols['pf_percent'])
            col.set_cell_data_func(cell, float_to_string, self.cols['pf_percent'])
        self.create_column(_('Type'), self.cols['type'])
        self.create_column(_('Start'), self.cols['start'])
        if not isinstance(self.container, model.Watchlist):
            col, cell = self.create_column(_('Buy value'), self.cols['buy_value'])
            col.set_cell_data_func(cell, float_to_string, self.cols['buy_value'])
        self.create_column(_('Last price'), self.cols['last_price'])
        col, cell = self.create_column(_('Change'), self.cols['change'])
        col.set_cell_data_func(cell, float_to_red_green_string, self.cols['change'])
        col, cell = self.create_column(_('Change %'), self.cols['change_percent'])
        col.set_cell_data_func(cell, float_to_red_green_string, self.cols['change_percent'])
        if not isinstance(self.container, model.Watchlist):
            col, cell = self.create_column(_('Mkt value'), self.cols['mkt_value'])
            col.set_cell_data_func(cell, float_to_string, self.cols['mkt_value'])
        col, cell = self.create_column(_('Gain'), self.cols['gain'])
        col.set_cell_data_func(cell, float_to_red_green_string, self.cols['gain'])
        col, cell = self.create_column(_('Gain %'), self.cols['gain_percent'])
        col.set_cell_data_func(cell, float_to_red_green_string, self.cols['gain_percent'])
        if not isinstance(self.container, model.Watchlist):
            col, cell = self.create_column(_('Day\'s gain'), self.cols['days_gain'])
            col.set_cell_data_func(cell, float_to_red_green_string, self.cols['days_gain'])
        col, cell = self.create_column(_('Tags'), self.cols['tags'])
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
            ('stocks.updated', self.on_stocks_updated),
            ('positionstoolbar.remove', self.on_remove_position),
            ('position_menu.remove', self.on_remove_position),
            ('positionstoolbar.add', self.on_add_position),
            ('position_menu.add', self.on_add_position),
            ('positionstoolbar.tag', self.on_tag),
            ('positionstoolbar.split', self.on_split),
            ('position_menu.split', self.on_split),
            ('container.position.added', self.on_position_added),
            ('position.tags.changed', self.on_positon_tags_changed),
            ('shortcut.update', self.on_update)
        )
        for topic, callback in self.subscriptions:
            pubsub.subscribe(topic, callback)
            
        self.selected_item = None
    
    def on_update(self):
        self.container.update_positions()

    def on_button_press_event(self, widget, event):
        if event.button == 3:
            if self.selected_item is not None:
                obj, iter = self.selected_item
                PositionContextMenu(obj).show(event)

    def on_destroy(self, x):
        for topic, callback in self.subscriptions:
            pubsub.unsubscribe(topic, callback)

    def load_positions(self):
        for pos in self.container.positions:
            self.insert_position(pos)
    
    def on_tag_edited(self, cellrenderertext, path, new_text):
        if self.selected_item is None:
            return
        obj, iter = self.selected_item
        obj.tags = new_text.split()
    
   
    def on_positon_tags_changed(self, tags, item):
        row = self.find_position(item.id)
        if row:
            row[self.cols['tags']] = item.tags_string
    
    def on_stocks_updated(self, container):
        if container.name == self.container.name:
            for row in self.get_model():
                item = row[0]
                row[self.cols['last_price']] = get_price_string(item)
                row[self.cols['change']] = item.current_change[0]
                row[self.cols['change_percent']] = item.current_change[1]
                row[self.cols['gain']] = item.gain[0]
                row[self.cols['gain_percent']] = item.gain[1]
                row[self.cols['days_gain']] = item.days_gain
                row[self.cols['mkt_value']] = round(item.cvalue,2)
                
    def on_position_added(self, container, item):
        if container.name == self.container.name:
            self.insert_position(item)
     
    def on_remove_position(self, position = None):
        if position is None:
            if self.selected_item is None:
                return
            position, iter = self.selected_item
        if isinstance(self.container, model.Watchlist):
            dlg = gtk.MessageDialog(None, 
                 gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION, 
                    gtk.BUTTONS_OK_CANCEL, _("Are you sure?"))
            response = dlg.run()
            dlg.destroy()
            if response == gtk.RESPONSE_OK:
                position.delete()
        elif isinstance(self.container, model.Portfolio):
            d = SellDialog(self.container, position)
            if d.response == gtk.RESPONSE_ACCEPT:
                if position.quantity == 0:
                    self.get_model().remove(iter)
                else:
                    self.get_model()[iter][self.cols['shares']] = position.quantity    
    
    def on_add_position(self):
        if isinstance(self.container, model.Watchlist):
            NewWatchlistPositionDialog(self.container)  
        elif isinstance(self.container, model.Portfolio):
            BuyDialog(self.container)
    
    def on_split(self, position = None):
        if position is None:
            if self.selected_item is None:
                return
            position, iter = self.selected_item
        d = SplitDialog(position)
        
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
        treestore, selection_iter = selection.get_selected()
        if (selection_iter and treestore):
            #Something is selected so get the object
            obj = treestore.get_value(selection_iter, 0)
            self.selected_item = obj, selection_iter
            if isinstance(obj, model.Position):
                pubsub.publish('positionstree.select', obj)
                return
        pubsub.publish('positionstree.unselect')
            
    def insert_position(self, position):
        if position.quantity != 0:
            stock = position.stock
            gain = position.gain
            c_change = position.current_change
            if self.container.cvalue == 0:
                change = 0
            else:
                change = 100 * position.cvalue / self.container.cvalue
            self.get_model().append(None, [position, 
                                           get_name_string(stock), 
                                           get_price_string(position), 
                                           get_price_string(stock), 
                                           c_change[0],
                                           gain[0],
                                           position.quantity,
                                           position.bvalue,
                                           position.cvalue,
                                           position.tagstring,
                                           position.days_gain,
                                           gain[1],
                                           c_change[1],
                                           position.type_string,
                                           change])

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
        tb = PositionsToolbar(pf, positions_tree)
        self.pack_start(tb, expand = False, fill = True)
        
        self.total_label = label = gtk.Label()
        hbox.pack_start(label)
        hbox.pack_start(gtk.VSeparator(), expand = False, fill = False)
            
        self.today_label = label = gtk.Label()
        hbox.pack_start(label)
        hbox.pack_start(gtk.VSeparator(), expand = True, fill = True)
        self.overall_label = label = gtk.Label()
        hbox.pack_start(label, expand = False, fill = False)
        
        if isinstance(pf, model.Watchlist) or isinstance(pf, model.Portfolio):
            hbox.pack_start(gtk.VSeparator(), expand = True, fill = True)
            self.last_update_label = label = gtk.Label()
            hbox.pack_start(label, expand = True, fill = False)
        sw = gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.add(positions_tree)
        self.pack_start(hbox, expand=False, fill=True)
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
            
            if isinstance(container, model.Portfolio):
                text = '<b>'+_('Investments')+'</b> :'+str(round(self.pf.cvalue,2))
                text += '\n<b>'+_('Cash')+'</b> :'+str(round(self.pf.cash,2))
                self.total_label.set_markup(text)
            else:
                text = '<b>'+_('Total')+'</b>\n'+str(round(self.pf.cvalue,2))
                self.total_label.set_markup(text)
            
            if isinstance(container, model.Portfolio) or isinstance(container, model.Watchlist):
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
