from gi.repository import Gtk
import pytz
from avernus import config, pubsub
import locale
from gi.repository import GObject
import threading
import thread



class GeneratorTask(object):
    """
    http://unpythonic.blogspot.com/2007/08/using-threads-in-pyGtk.html
    Thanks!
    """
    def __init__(self, generator, loop_callback=None, complete_callback=None):
        self.generator = generator
        self.loop_callback = loop_callback
        self.complete_callback = complete_callback

    def _start(self, *args, **kwargs):
        self._stopped = False
        for ret in self.generator(*args, **kwargs):
            if self._stopped:
                thread.exit()
            GObject.idle_add(self._loop, ret)
        if self.complete_callback is not None:
            GObject.idle_add(self.complete_callback)

    def _loop(self, ret):
        if ret is None:
            ret = ()
        if not isinstance(ret, tuple):
            ret = (ret,)
        if self.loop_callback:
            self.loop_callback(*ret)

    def start(self, *args, **kwargs):
        threading.Thread(target=self._start, args=args, kwargs=kwargs).start()

    def stop(self):
        self._stopped = True


class BackgroundTask():

    def __init__(self, function, complete_callback=None):
        self.function = function
        self.complete_callback = complete_callback
        threading.Thread(target=self.start).start()

    def start(self):
        self.function()
        if self.complete_callback is not None:
            GObject.idle_add(self.complete_callback)


class Tree(Gtk.TreeView):
    
    def __init__(self):
        self.selected_item = None
        Gtk.TreeView.__init__(self)
        pubsub.subscribe('clear!', self.clear)

    def get_selected_item(self):
        #Get the current selection in the Gtk.TreeView
        selection = self.get_selection()
        # Get the selection iter
        treestore, selection_iter = selection.get_selected()
        if (selection_iter and treestore):
            return treestore[selection_iter][0], selection_iter
        return None, None

    def create_column(self, name, attribute, func=None, expand=False):
        #FIXME keyword expand is unused
        cell = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(name, cell)
        self.append_column(column)
        if func is not None:
            column.set_cell_data_func(cell, func, attribute)
        else:
            column.add_attribute(cell, "markup", attribute)
        column.set_sort_column_id(attribute)
        column.set_expand(expand)
        return column, cell

    def create_icon_column(self, name, attribute, size=None):
        #Gtk.IconSize.MENU, Gtk.IconSize.SMALL_TOOLBAR, Gtk.IconSize.LARGE_TOOLBAR, Gtk.IconSize.BUTTON, Gtk.IconSize.DND and Gtk.IconSize.DIALOG.
        column = Gtk.TreeViewColumn(name)
        self.append_column(column)
        cell = Gtk.CellRendererPixbuf()
        if size:
            cell.set_property('stock-size', size)
        column.pack_start(cell, False)
        column.add_attribute(cell, "icon_name", attribute)
        return column, cell

    def create_icon_text_column(self, name, attribute1, attribute2, func1=None, func2=None):
        column = Gtk.TreeViewColumn(name)
        self.append_column(column)
        cell1 = Gtk.CellRendererPixbuf()
        cell2 = Gtk.CellRendererText()
        column.pack_start(cell1, False)
        column.pack_start(cell2, True)
        column.add_attribute(cell1, "icon_name", attribute1)
        column.add_attribute(cell2, "markup", attribute2)
        column.set_sort_column_id(attribute2)
        if func1 is not None:
            column.set_cell_data_func(cell1, func1, attribute1)
        if func2 is not None:
            column.set_cell_data_func(cell2, func2, attribute2)
        return column, cell2

    def create_check_column(self, name, attribute):
        column = Gtk.TreeViewColumn(name)
        self.append_column(column)
        cell = Gtk.CellRendererToggle()
        column.pack_start(cell, False)
        column.add_attribute(cell, 'active', attribute)
        return column, cell

    def find_item(self, row0, itemtype = None):
        def search(rows):
            if not rows: return None
            for row in rows:
                if row[0] == row0 and (itemtype is None or itemtype == row[1].type):
                    return row
                result = search(row.iterchildren())
                if result: return result
            return None
        return search(self.get_model())

    def clear(self):
        self.get_model().clear()


class ContextMenu(Gtk.Menu):
    
    def __init__(self):
        Gtk.Menu.__init__(self)

    def run(self, event):
        self.show_all()
        self.popup(None, None, None, None, event.button, event.time)

    def add_item(self, label, func = None, icon = None):
        if label == '----':
            self.append(Gtk.SeparatorMenuItem())
        else:
            if icon is not None:
                item = Gtk.ImageMenuItem()
                item.set_label(icon)
                item.set_use_stock(True)
                item.get_children()[0].set_label(label)
            else:
                item = Gtk.MenuItem()
                item.set_label(label)
            if func is not None:
                item.connect("activate", func)
            self.append(item)
            return item

def float_format(column, cell_renderer, tree_model, iterator, user_data):
    number = tree_model.get_value(iterator, user_data)
    cell_renderer.set_property('text', get_string_from_float(number))
    return

def percent_format(column, cell_renderer, tree_model, iterator, user_data):
    number = tree_model.get_value(iterator, user_data)
    cell_renderer.set_property('text', get_string_from_float(number)+'%')
    return

def currency_format(column, cell_renderer, tree_model, iterator, user_data):
    number = tree_model.get_value(iterator, user_data)
    cell_renderer.set_property('text', get_currency_format_from_float(number))
    return

def get_string_from_float(number):
    return locale.format('%g', round(number,2), grouping=False, monetary=True)

def get_currency_format_from_float(number):
    try:
        return locale.currency(number)
    except:
        return str(round(number,2))

def float_to_red_green_string_currency(column, cell, model, iterator, user_data):
    num = model.get_value(iterator, user_data)
    text = get_currency_format_from_float(num)
    cell.set_property('markup', get_green_red_string(num, text))

def float_to_red_green_string(column, cell, model, iterator, user_data):
    num = model.get_value(iterator, user_data)
    text = get_string_from_float(num)
    cell.set_property('markup', get_green_red_string(num, text))

def float_to_red_green_string_percent(column, cell, model, iterator, user_data):
    num = model.get_value(iterator, user_data)
    text = get_string_from_float(num)+'%'
    cell.set_property('markup', get_green_red_string(num, text))

def sort_by_time(model, iter1, iter2, data=None):
    #why is d2 None?
    d1 = model.get_value(iter1, data)
    d2 = model.get_value(iter2, data)
    if not d1 or not d2:
        return 1
    elif d1 < d2:
        return -1
    elif d1 > d2:
        return 1
    return 0

def date_to_string(column, cell, model, iterator, user_data):
    item = model.get_value(iterator, user_data)
    cell.set_property('text', get_date_string(item))

def get_price_string(item):
    if item.price is None:
        return 'n/a'
    return get_string_from_float(item.price) +'\n<small>'+get_datetime_string(item.date)+'</small>'

def to_local_time(date):
    if date is not None:
        date = date.replace(tzinfo = pytz.utc)
        date = date.astimezone(pytz.timezone(config.timezone))
        return date.replace(tzinfo = None)

def get_name_string(stock):
    return '<b>%s</b>\n<small>%s\n%s</small>' % (GObject.markup_escape_text(stock.name),
                                                 GObject.markup_escape_text(stock.isin),
                                                 GObject.markup_escape_text(stock.exchange))

def get_green_red_string(num, text = None):
    if text is None:
        text = str(num)
    if num < 0.0:
        text = '<span foreground="red">'+ text + '</span>'
    elif num > 0.0:
        text = '<span foreground="dark green">'+ text + '</span>'
    return text

def datetime_format(datetime, nl = True):
    if datetime is not None:
        if not nl:
            return datetime.strftime(locale.nl_langinfo(locale.D_T_FMT))
        else:
            return get_date_string(datetime.date())+'\n'+datetime.time().strftime(locale.nl_langinfo(locale.T_FMT))
    return 'never'

def get_date_string(date):
    if date is None:
        return ''
    try:
        return date.strftime(locale.nl_langinfo(locale.D_FMT))
    except:
        return str(date)

def get_datetime_string(datetime):
    if datetime is not None:
        if datetime.hour == 5 and datetime.minute == 0 and datetime.second == 0:
            return get_date_string(datetime)
        else:
            return datetime_format(to_local_time(datetime))
    return ''


def transaction_desc_markup(column, cell, model, iterator, user_data):
    text = model.get_value(iterator, user_data)
    markup =  '<span size="small">%s</span>' % (GObject.markup_escape_text(text),)
    cell.set_property('markup', markup)

#FIXME horizontal scrollbars are always shown
#without the "+10" it crashes sometimes
def resize_wrap(scroll, allocation, treeview, column, cell):
    newWidth = allocation.width - sum(c.get_width() for c in treeview.get_columns() if c != column)
    newWidth -= treeview.style_get_property("horizontal-separator") * 4
    if cell.props.wrap_width == newWidth or newWidth <= 0:
        return
    if newWidth < 300:
        newWidth = 300
    cell.props.wrap_width = newWidth
    column.set_property('min-width', newWidth + 10)
    column.set_property('max-width', newWidth + 10)
    store = treeview.model
    iterator = store.get_iter_first()
    while iterator and store.iter_is_valid(iterator):
            store.row_changed(store.get_path(iterator), iterator)
            iterator = store.iter_next(iterator)
            treeview.set_size_request(0,-1)


if __name__ == '__main__':
    print locale.format('%g', 12111.3, grouping=True, monetary=True)
