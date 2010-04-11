#!/usr/bin/env python

import gtk, string,  logging, pytz
from stocktracker import model, config, pubsub

logger = logging.getLogger(__name__)


def to_local_time(date):
    if date is not None:
        date = date.replace(tzinfo = pytz.utc)
        date = date.astimezone(pytz.timezone(config.timezone))
        return date.replace(tzinfo = None)

def get_datetime_string(date):
    if date is not None:
        if date.hour == 0 and date.minute == 0 and date.second == 0:
            return datetime_format(to_local_time(date).date())
        else:
            return datetime_format(to_local_time(date))
    return ''
    
def datetime_format(date):
    if date is not None:
        return date.strftime("%d.%m.%Y %I:%M%p")
    return 'never'
    
def get_name_string(stock):
    return '<b>'+stock.name+'</b>' + '\n' + '<small>'+stock.yahoo_symbol+'</small>' + '\n' + '<small>'+stock.exchange.name+'</small>'
 

def get_green_red_string(num, string = None):
    if string is None:
        string = str(num)
    if num < 0.0:
        text = '<span foreground="red">'+ string + '</span>'
    else:
        text = '<span foreground="dark green">'+ string + '</span>'
    return text


class Tree(gtk.TreeView):
    def __init__(self):
        self.selected_item = None
        gtk.TreeView.__init__(self)
        pubsub.subscribe('clear!', self.clear)
    
    def create_column(self, name, attribute):
        column = gtk.TreeViewColumn(name)
        self.append_column(column)
        cell = gtk.CellRendererText()
        column.pack_start(cell, expand = True)
        column.add_attribute(cell, "markup", attribute)
        column.set_sort_column_id(attribute)
        return column, cell

    
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
