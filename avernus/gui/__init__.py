import os
from gi.repository import Gtk


def get_ui_file(filename):
    current_rep = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_rep, filename)

builder = None


def get_avernus_builder():
    global builder
    if not builder:
        builder = Gtk.Builder()
        builder.add_from_file(get_ui_file("avernus.glade"))
    return builder
