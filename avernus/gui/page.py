from gi.repository import GObject
from gi.repository import Gtk


class Page(Gtk.VBox):

    __gsignals__ = {
        'update': (GObject.SIGNAL_RUN_LAST, None,
                      (object,))
    }

    def __init__(self):
        Gtk.VBox.__init__(self)

    def get_info(self):
        return []

    def update_page(self, *args):
        self.emit("update", self)

GObject.type_register(Page)
