import gtk, pytz
from stocktracker import config


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
    text =  str(round(model.get_value(iter, user_data), 2))
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
    return '<b>'+stock.name+'</b>' + '\n' + '<small>'+stock.yahoo_symbol+'</small>' + '\n' + '<small>'+stock.exchange.name+'</small>'
 

def get_green_red_string(num, string = None):
    if string is None:
        string = str(num)
    if num < 0.0:
        text = '<span foreground="red">'+ string + '</span>'
    else:
        text = '<span foreground="dark green">'+ string + '</span>'
    return text
    
def datetime_format(date):
    if date is not None:
        return date.strftime("%d.%m.%Y %I:%M%p")
    return 'never'


def get_datetime_string(date):
    if date is not None:
        if date.hour == 0 and date.minute == 0 and date.second == 0:
            return datetime_format(to_local_time(date).date())
        else:
            return datetime_format(to_local_time(date))
    return ''
