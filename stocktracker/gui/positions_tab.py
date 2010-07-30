#!/usr/bin/env python

import gtk,sys
from stocktracker import pubsub
from stocktracker.gui.plot import ChartWindow
from stocktracker.gui.dialogs import SellDialog, NewWatchlistPositionDialog, SplitDialog, BuyDialog, EditPositionDialog
from stocktracker.gui.gui_utils import Tree, ContextMenu, float_to_red_green_string, float_to_string, get_name_string, datetime_format, get_datetime_string

gain_thresholds = {
                   (-sys.maxint,-0.5):'arrow_down',
                   (-0.5,-0.2):'arrow_med_down',
                   (-0.2,0.2):'arrow_right',
                   (0.2,0.5):'arrow_med_up',
                   (0.5,sys.maxint):'arrow_up'
                   }

def get_arrow_icon(perc):
    for (min,max),name in gain_thresholds.items():
        if min<=perc and max>=perc:
            return name

def start_price_markup(column, cell, model, iter, user_data):
    pos = model.get_value(iter, 0)
    markup = str(round(model.get_value(iter, user_data),2)) +'\n' +'<small>'+get_datetime_string(pos.date)+'</small>'
    cell.set_property('markup', markup)

def current_price_markup(column, cell, model, iter, user_data):
    stock = model.get_value(iter, 0).stock
    markup = str(round(model.get_value(iter, user_data),2)) +'\n' +'<small>'+get_datetime_string(stock.date)+'</small>'
    cell.set_property('markup', markup)


class PositionContextMenu(ContextMenu):
    def __init__(self, actiongroup):
        ContextMenu.__init__(self)
        
        for action in ['edit', 'chart', 'remove']:
            self.add(actiongroup.get_action(action).create_menu_item())
        

class PositionsTree(Tree):
    def __init__(self, container, actiongroup):
        self.container = container
        self.actiongroup = actiongroup
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
                     'gain_icon':12, 
                     'change_percent':13,
                     'type': 14,
                     'pf_percent': 15
                      }
        
        self.set_model(gtk.ListStore(object,str, float, float,float, float, int, float, float, str, float, float,str, float, str, float))
        
        self.watchlist = False
        if container.__name__ == 'Watchlist':
            self.watchlist = True

        if not self.watchlist:
            self.create_column('#', self.cols['shares'])
        self.create_column(_('Name'), self.cols['name'])
        self.create_icon_column(_('Type'), self.cols['type'])
        if not self.watchlist:
            self.create_column(_('Pf %'), self.cols['pf_percent'], func=float_to_string)
        self.create_column(_('Start'), self.cols['start'], func=start_price_markup)
        if not self.watchlist:
            self.create_column(_('Buy value'), self.cols['buy_value'], func=float_to_string)
        self.create_column(_('Last price'), self.cols['last_price'], func=current_price_markup)
        self.create_column(_('Change'), self.cols['change'], func=float_to_red_green_string)
        self.create_column('%', self.cols['change_percent'], func=float_to_red_green_string)
        if not self.watchlist:
            self.create_column(_('Mkt value'), self.cols['mkt_value'], float_to_string)
        self.create_column(_('Gain'), self.cols['gain'], float_to_red_green_string)
        self.create_icon_text_column('%', self.cols['gain_icon'], self.cols['gain_percent'], func2=float_to_red_green_string)
        if not self.watchlist:
            self.create_column(_('Today'), self.cols['days_gain'], float_to_red_green_string)
        col, cell = self.create_column(_('Tags'), self.cols['tags'])
        cell.set_property('editable', True)
        cell.connect('edited', self.on_tag_edited)

        self.set_rules_hint(True)
        self.load_positions()
        
        self.connect('button-press-event', self.on_button_press_event)
        self.connect('cursor_changed', self.on_cursor_changed)
        self.connect("destroy", self.on_destroy)
        
        self.subscriptions = (
            ('stocks.updated', self.on_stocks_updated),
            ('position.tags.changed', self.on_positon_tags_changed),
            ('container.position.added', self.on_position_added)
        )
        for topic, callback in self.subscriptions:
            pubsub.subscribe(topic, callback)
            
        self.selected_item = None
        
        actiongroup.add_actions([
                ('add',    gtk.STOCK_ADD,     'add',    None, _('Add new position'),         self.on_add),      
                ('edit' ,  gtk.STOCK_EDIT,    'edit',   None, _('Edit selected position'),   self.on_edit),
                ('remove', gtk.STOCK_DELETE,  'remove', None, _('Delete selected position'), self.on_remove),
                ('chart',  None,              'chart',  None, _('Chart selected position'),  self.on_chart),
                #('split',  None            , 'split...', None, _('Split selected position'), self.on_remove),
                ('tag',    None,              'tag',    None, _('Tag selected position'),    self.on_tag),
                ('update', gtk.STOCK_REFRESH, 'update', None, _('Update positions'),         lambda x: self.container.update_positions())
                                ])
        actiongroup.get_action('chart').set_icon_name('stocktracker')
        actiongroup.get_action('tag').set_icon_name('tag')
        accelgroup = gtk.AccelGroup()
        for action in actiongroup.list_actions():
            action.set_accel_group(accelgroup)
        self.on_unselect()
    
    def on_button_press_event(self, widget, event):
        if event.button == 3:
            if self.selected_item is not None:
                PositionContextMenu(self.actiongroup).show(event)

    def on_unselect(self):
        for action in ['edit', 'remove', 'chart', 'tag']:
            self.actiongroup.get_action(action).set_sensitive(False)       
        
    def on_select(self, obj):
        for action in ['edit', 'remove', 'chart', 'tag']:
            self.actiongroup.get_action(action).set_sensitive(True)

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
        for tag in new_text.split():
            pubsub.publish('position.newTag',position=obj,tagText=tag)
   
    def on_positon_tags_changed(self, tags, item):
        row = self.find_position(item.id)
        if row:
            row[self.cols['tags']] = item.tags_string
    
    def on_stocks_updated(self, container):
        if container.name == self.container.name:
            for row in self.get_model():
                item = row[0]
                gain, gain_percent = item.gain
                row[self.cols['last_price']] = item.stock.price
                row[self.cols['change']] = item.current_change[0]
                row[self.cols['change_percent']] = item.current_change[1]
                row[self.cols['gain']] = gain
                row[self.cols['gain_percent']] = gain_percent
                row[self.cols['gain_icon']] = get_arrow_icon(gain_percent)
                row[self.cols['days_gain']] = item.days_gain
                row[self.cols['mkt_value']] = round(item.cvalue,2)
                row[self.cols['pf_percent']] = postion.portfolio_fraction
                
    def on_position_added(self, container, item):
        if container.id == self.container.id:
            self.insert_position(item)
            #update portfolio fractions
            for row in self.get_model():
                row[self.cols['pf_percent']] = row[self.cols['obj']].portfolio_fraction
     
    def on_remove(self, widget):
        position, iter = self.selected_item
        if self.watchlist:
            dlg = gtk.MessageDialog(None, 
                 gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION, 
                    gtk.BUTTONS_OK_CANCEL, _("Are you sure?"))
            response = dlg.run()
            dlg.destroy()
            if response == gtk.RESPONSE_OK:
                position.delete()
                self.get_model().remove(iter)
        else:
            d = SellDialog(self.container, position)
            if d.response == gtk.RESPONSE_ACCEPT:
                if position.quantity == 0:
                    self.get_model().remove(iter)
                else:
                    self.get_model()[iter][self.cols['shares']] = position.quantity    
    
    def on_add(self, widget):
        if self.watchlist:
            NewWatchlistPositionDialog(self.container)  
        else:
            BuyDialog(self.container)
        
    def on_tag(self, widget):
        path, col = self.get_cursor()
        self.set_cursor(path, focus_column = self.get_column(13), start_editing=True)
    
    def on_chart(self, widget):
        ChartWindow(self.selected_item[0].stock)
    
    def on_edit(self, widget):
        position, iter = self.selected_item
        EditPositionDialog(position)
        self.update_position_after_edit(position, iter)
    
    def update_position_after_edit(self, pos, iter):
        m = self.get_model()
        row = m[iter]
        col = 0
        for item in self._get_row(pos):
            m.set_value(iter, col, item)    
            col+=1
        
    def on_cursor_changed(self, widget):
        #Get the current selection in the gtk.TreeView
        selection = widget.get_selection()
        # Get the selection iter
        treestore, selection_iter = selection.get_selected()
        if (selection_iter and treestore):
            #Something is selected so get the object
            obj = treestore.get_value(selection_iter, 0)
            self.selected_item = obj, selection_iter
            self.on_select(obj)
            return
        self.on_unselect()
            
    def _get_row(self, position):
        stock = position.stock
        gain = position.gain
        gain_icon = get_arrow_icon(gain[1])
        c_change = position.current_change
        #FIXME etf need an icon
        icons = ['F', 'A', 'F']
        return [position, 
               get_name_string(stock), 
               position.price, 
               stock.price, 
               c_change[0],
               gain[0],
               position.quantity,
               position.bvalue,
               position.cvalue,
               position.tagstring,
               position.days_gain,
               gain[1],
               gain_icon,
               c_change[1],
               icons[position.stock.type],
               position.portfolio_fraction]
            
    def insert_position(self, position):
        if position.quantity != 0:
            self.get_model().append(self._get_row(position))

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
        

class InfoBar(gtk.HBox):
    def __init__(self, container):
        gtk.HBox.__init__(self)
        self.container = container
        self.total_label = label = gtk.Label()
        self.pack_start(label)
        self.pack_start(gtk.VSeparator(), expand = False, fill = False)
            
        self.today_label = label = gtk.Label()
        self.pack_start(label)
        self.pack_start(gtk.VSeparator(), expand = True, fill = True)
        self.overall_label = label = gtk.Label()
        self.pack_start(label, expand = False, fill = False)
        
        if container.__name__ == 'Portfolio' or container.__name__ == 'Watchlist':
            self.pack_start(gtk.VSeparator(), expand = True, fill = True)
            self.last_update_label = label = gtk.Label()
            self.pack_start(label, expand = True, fill = False)
            
        self.on_container_update(self.container)
        pubsub.subscribe('position.created', self.on_container_update)
        pubsub.subscribe('stocks.updated', self.on_container_update)
        pubsub.subscribe('container.updated', self.on_container_update)
        pubsub.subscribe('container.position.added', self.on_container_update)

    def on_container_update(self, container, position=None):
        if self.container == container:
            text = '<b>' + _('Day\'s gain')+'</b>\n'+self.get_change_string(self.container.current_change)
            self.today_label.set_markup(text)
            text = '<b>'+_('Gain')+'</b>\n'+self.get_change_string(self.container.overall_change)
            self.overall_label.set_markup(text)
            
            if container.__name__ == 'Portfolio':
                text = '<b>'+_('Investments')+'</b> :'+str(round(self.container.cvalue,2))
                text += '\n<b>'+_('Cash')+'</b> :'+str(round(self.container.cash,2))
                self.total_label.set_markup(text)
            else:
                text = '<b>'+_('Total')+'</b>\n'+str(round(self.container.cvalue,2))
                self.total_label.set_markup(text)
            
            if container.__name__ == 'Portfolio' or container.__name__ == 'Watchlist':
                text = '<b>'+_('Last update')+'</b>\n'+datetime_format(self.container.last_update, False)
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


class PositionsTab(gtk.VBox):
    def __init__(self, container):
        gtk.VBox.__init__(self)
        actiongroup = gtk.ActionGroup('position_tab')
        positions_tree = PositionsTree(container, actiongroup)
        hbox = gtk.HBox()
        
        tb = gtk.Toolbar()
        
        if container.__name__ == 'Portfolio':
            buttons = ['add', 'remove', 'edit', 'tag', 'chart', '---', 'update']
        elif container.__name__ == 'Watchlist' or container.__name__ == 'Tag':
            buttons = ['add', 'remove', 'edit', 'chart', '---', 'update']
        
        for action in buttons:
            if action == '---':
                tb.insert(gtk.SeparatorToolItem(),-1)
            else: 
                button = actiongroup.get_action(action).create_tool_item()
                tb.insert(button, -1) 
        
        self.pack_start(tb, expand = False, fill = True)
        
        sw = gtk.ScrolledWindow()
        sw.set_property('hscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.set_property('vscrollbar-policy', gtk.POLICY_AUTOMATIC)
        sw.add(positions_tree)
        self.pack_start(InfoBar(container), expand=False, fill=True)
        self.pack_start(sw)
        self.show_all()        
