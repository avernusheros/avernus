from gi.repository import GObject


class Page(GObject.GObject):

    __gsignals__ = {
        'update': (GObject.SIGNAL_RUN_LAST, None,
                      (object,))
    }

    def __init__(self):
        GObject.GObject.__init__(self)

    def get_info(self):
        return []

    def update_page(self, *args):
        self.emit("update", self)

GObject.type_register(Page)
