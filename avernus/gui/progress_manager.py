from gi.repository import Gtk
from gi.repository import GObject


class ProgressMonitor(Gtk.Frame):

    def __init__(self, progress_id, desc, icon):
        Gtk.Frame.__init__(self)
        self.desc = desc
        self.icon = icon
        self.id = progress_id
        self._setup_widgets()
        self.show_all()

    def progress_update(self, percent):
        GObject.idle_add(self.progress.set_fraction, percent)
        GObject.idle_add(self.progress.set_text, self.desc + '%d%%' % int(100 * percent))

    def progress_update_pulse(self, *args):
        GObject.idle_add(self.progress.pulse)
        return True

    def progress_update_auto(self):
        GObject.timeout_add(100, self.progress_update_pulse)

    def stop(self, *e):
        remove_monitor(self.id)

    def _setup_widgets(self):
        icon = self.icon

        pbox = Gtk.HBox()
        pbox.set_spacing(3)

        img = Gtk.Image()
        img.set_from_stock(icon, Gtk.IconSize.SMALL_TOOLBAR)
        img.set_size_request(32, 32)
        pbox.pack_start(img, False, False, 0)

        self.progress = Gtk.ProgressBar()
        self.progress.set_text(self.desc)
        self.progress.set_show_text(True)

        pbox.pack_start(self.progress, True, True, 0)

        #button = Gtk.Button()
        #img = Gtk.Image()
        #img.set_from_stock('gtk-stop', Gtk.IconSize.SMALL_TOOLBAR)
        #button.set_image(img)

        #pbox.pack_start(button, False, False)
        #button.connect('clicked', self.stop)

        self.add(pbox)


box = None
monitors = {}


def add_monitor(progress_id, description, stock_icon):
    """
    Adds a progress box

    @param description: a description of the event
    @param stock_icon: the icon to display
    """
    if not monitors:
        box.show()
    monitor = ProgressMonitor(progress_id, description, stock_icon)
    #self.box.add(monitor)
    box.pack_start(monitor, False, False, 0)

    monitors[progress_id] = monitor
    return monitor


def remove_monitor(progress_id):
    """
    Removes a monitor from the manager
    """
    box.remove(monitors[progress_id])
    del monitors[progress_id]
    if not monitors:
        box.hide()
