import gtk, pytz
from stocktracker import config, pubsub


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
            #Something is selected so get the object
            obj = treestore.get_value(selection_iter, 0)
            return obj, selection_iter 
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

    def create_icon_column(self, name, attribute):
        column = gtk.TreeViewColumn(name)
        self.append_column(column)
        cell = gtk.CellRendererPixbuf()
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
        
    def find_item(self, id, type = None):
        def search(rows):
            if not rows: return None
            for row in rows:
                if row[0] == id and (type is None or type == row[1].type):
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


def float_to_red_green_string(column, cell, model, iter, user_data):
    num = round(model.get_value(iter, user_data), 2)
    if num < 0:
        markup =  '<span foreground="red">'+ str(num) + '</span>'
    elif num > 0:
        markup =  '<span foreground="dark green">'+ str(num) + '</span>'
    else:
        markup =  str(num)
    cell.set_property('markup', markup)


def float_to_string(column, cell, model, iter, user_data):
    text = str(round(model.get_value(iter, user_data), 2))
    cell.set_property('text', text)

def float_to_string_ignore_dot_zero(column, cell, model, iter, user_data):
    num = model.get_value(iter, user_data)
    if num % 1 == 0.0:
        text = str(int(num))
    else:
        text = str(round(num, 2))
    cell.set_property('text', text)

def get_price_string(item):
    if item.price is None:
        return 'n/a'
    return str(round(item.price,2)) +'\n' +'<small>'+get_datetime_string(item.date)+'</small>'


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
    
def datetime_format(date, nl = True):
    if date is not None:
        if nl:
            return date.strftime("%d.%m.%Y\n%I:%M%p")
        else: 
            return date.strftime("%d.%m.%Y %I:%M%p")
    return 'never'


def get_datetime_string(date):
    if date is not None:
        if date.hour == 0 and date.minute == 0 and date.second == 0:
            return date.strftime("%d.%m.%Y")
        else:
            return datetime_format(to_local_time(date))
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
    store = treeview.get_model()
    iter = store.get_iter_first()
    while iter and store.iter_is_valid(iter):
            store.row_changed(store.get_path(iter), iter)
            iter = store.iter_next(iter)
            treeview.set_size_request(0,-1)
