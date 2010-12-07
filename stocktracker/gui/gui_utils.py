import gtk, pytz
from stocktracker import config, pubsub
import locale


class Tree(gtk.TreeView):
    def __init__(self):
        self.selected_item = None
        gtk.TreeView.__init__(self)
        pubsub.subscribe('clear!', self.clear)
    
    def get_selected_item(self):
        #Get the current selection in the gtk.TreeView
        selection = self.get_selection()
        # Get the selection iter
        treestore, selection_iter = selection.get_selected()
        if (selection_iter and treestore):
            return treestore[selection_iter][0], selection_iter 
        return None, None
        
    def create_column(self, name, attribute, func=None):
        column = gtk.TreeViewColumn(name)
        self.append_column(column)
        cell = gtk.CellRendererText()
        column.pack_start(cell, expand = True)
        column.add_attribute(cell, "markup", attribute)
        if func is not None:
            column.set_cell_data_func(cell, func, attribute)
        column.set_sort_column_id(attribute)
        return column, cell

    def create_icon_column(self, name, attribute, size=None):
        #gtk.ICON_SIZE_MENU, gtk.ICON_SIZE_SMALL_TOOLBAR, gtk.ICON_SIZE_LARGE_TOOLBAR, gtk.ICON_SIZE_BUTTON, gtk.ICON_SIZE_DND and gtk.ICON_SIZE_DIALOG.
        column = gtk.TreeViewColumn(name)
        self.append_column(column)
        cell = gtk.CellRendererPixbuf()
        if size:
            cell.set_property('stock-size', size)
        column.pack_start(cell, expand = True)
        column.set_attributes(cell, icon_name=attribute)
        return column, cell
        
    def create_icon_text_column(self, name, attribute1, attribute2, func1=None, func2=None):
        column = gtk.TreeViewColumn(name)
        self.append_column(column)
        cell1 = gtk.CellRendererPixbuf()
        cell2 = gtk.CellRendererText()
        column.pack_start(cell1, expand = False)
        column.pack_start(cell2, expand = True)     
        column.set_attributes(cell1, icon_name=attribute1)
        column.add_attribute(cell2, "markup", attribute2)
        if func1 is not None:
            column.set_cell_data_func(cell1, func1, attribute1)
        if func2 is not None:
            column.set_cell_data_func(cell2, func2, attribute2)
        return column, cell2
    
    def create_check_column(self, name, attribute):
        column = gtk.TreeViewColumn(name)
        self.append_column(column)
        cell = gtk.CellRendererToggle()
        column.pack_start(cell, expand = True)
        column.add_attribute(cell, 'active', attribute)
        return column, cell    
        
    def find_item(self, row0, type = None):
        def search(rows):
            if not rows: return None
            for row in rows:
                if row[0] == row0 and (type is None or type == row[1].type):
                    return row 
                result = search(row.iterchildren())
                if result: return result
            return None
        return search(self.get_model())

    def clear(self):
        self.get_model().clear()


class ContextMenu(gtk.Menu):
    def __init__(self):
        gtk.Menu.__init__(self)
    
    def show(self, event):
        self.show_all()
        self.popup(None, None, None, event.button, event.get_time())

    def add_item(self, label, func = None, icon = None):
        if label == '----':
            self.add(gtk.SeparatorMenuItem())
        else:
            if icon is not None:
                item = gtk.ImageMenuItem(icon)
                item.get_children()[0].set_label(label)
            else:
                item = gtk.MenuItem(label) 
            if func is not None:
                item.connect("activate", func)
            self.add(item)
            return item 

def float_format(column, cell_renderer, tree_model, iter, user_data):
     number = tree_model.get_value(iter, user_data)
     cell_renderer.set_property('text', get_string_from_float(number))
     return

def get_string_from_float(number):
    return locale.format('%g', round(number,2), grouping=True, monetary=True)

def float_to_red_green_string(column, cell, model, iter, user_data):
    num = model.get_value(iter, user_data)
    text = get_string_from_float(num)
    if num < 0:
        markup =  '<span foreground="red">'+ text + '</span>'
    elif num > 0:
        markup =  '<span foreground="dark green">'+ text + '</span>'
    else:
        markup =  text
    cell.set_property('markup', markup)


def float_to_string(column, cell, model, iter, user_data):
    cell.set_property('text', get_string_from_float(model.get_value(iter, user_data)))
    
def get_price_string(item):
    if item.price is None:
        return 'n/a'
    return get_string_from_float(item.price) +'\n' +'<small>'+get_datetime_string(item.date)+'</small>'

def to_local_time(date):
    if date is not None:
        date = date.replace(tzinfo = pytz.utc)
        date = date.astimezone(pytz.timezone(config.timezone))
        return date.replace(tzinfo = None)

def get_name_string(stock):
    return '<b>'+stock.name+'</b>' + '\n' + '<small>'+stock.isin+'</small>' + '\n' + '<small>'+stock.exchange+'</small>' 

def get_green_red_string(num, string = None):
    if string is None:
        string = str(num)
    if num < 0.0:
        text = '<span foreground="red">'+ string + '</span>'
    else:
        text = '<span foreground="dark green">'+ string + '</span>'
    return text
    
def datetime_format(datetime, nl = True):
    if datetime is not None:
        if not nl:
            return datetime.strftime(locale.nl_langinfo(locale.D_T_FMT))
        else: 
            return get_date_string(datetime.date())+'\n'+datetime.time().strftime(locale.nl_langinfo(locale.T_FMT))
    return 'never'

def get_date_string(date):
    return date.strftime(locale.nl_langinfo(locale.D_FMT))

def get_datetime_string(datetime):
    if datetime is not None:
        if datetime.hour == 0 and datetime.minute == 0 and datetime.second == 0:
            return get_date_string(datetime)
        else:
            return datetime_format(to_local_time(datetime))
    return ''

def resize_wrap(scroll, allocation, treeview, column, cell):
    otherColumns = (c for c in treeview.get_columns() if c != column)
    newWidth = allocation.width - sum(c.get_width() for c in otherColumns)
    newWidth -= treeview.style_get_property("horizontal-separator") * 4
    if cell.props.wrap_width == newWidth or newWidth <= 0:
            return
    if newWidth < 300:
            newWidth = 300
    cell.props.wrap_width = newWidth
    column.set_property('min-width', newWidth )
    column.set_property('max-width', newWidth )
    store = treeview.model
    iter = store.get_iter_first()
    while iter and store.iter_is_valid(iter):
            store.row_changed(store.get_path(iter), iter)
            iter = store.iter_next(iter)
            treeview.set_size_request(0,-1)


if __name__ == '__main__':
    print locale.format('%g', 12111.3, grouping=True, monetary=True)
