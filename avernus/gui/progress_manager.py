from gi.repository import Gtk
from gi.repository import GObject
from avernus import pubsub


class ProgressMonitor(Gtk.Frame):
    """
        A progress monitor
    """
    def __init__(self, progress_id, desc, icon):
        """
        Initializes the monitor
        """
        Gtk.Frame.__init__(self)
        self.desc = desc
        self.icon = icon
        self.id = progress_id
        self._setup_widgets()
        self.show_all()
        
    def progress_update(self, percent):
        """
        Called when the progress has been updated
        """
        GObject.idle_add(self.progress.set_fraction, float(percent) / 100)
        GObject.idle_add(self.progress.set_text, '%d%%' % percent)

    def progress_update_pulse(self, *args):
        GObject.idle_add(self.progress.pulse)
        return True
        
    def progress_update_auto(self):
        GObject.timeout_add(100, self.progress_update_pulse)

    def stop(self, *e):
        """
        Stops this monitor, removes it from the progress area
        """
        pubsub.publish("progress.cancel", self.id)
        remove_monitor(self.id)

    def _setup_widgets(self):
        """
        Sets up the various widgets for this object
        """
        self.set_shadow_type(Gtk.ShadowType.NONE)
        desc = self.desc
        icon = self.icon

        box = Gtk.VBox()
        box.set_border_width(3)
        label = Gtk.Label(label=desc)
        label.set_use_markup(True)
        label.set_alignment(0, 0.5)
        label.set_padding(3, 0)

        box.pack_start(label, False, False, 0)

        pbox = Gtk.HBox()
        pbox.set_spacing(3)

        img = Gtk.Image()
        img.set_from_stock(icon, Gtk.IconSize.SMALL_TOOLBAR)
        img.set_size_request(32, 32)
        pbox.pack_start(img, False, False, 0)

        ibox = Gtk.VBox()
        l = Gtk.Label()
        l.set_size_request(2, 2)
        ibox.pack_start(l, False, False, 0)
        self.progress = Gtk.ProgressBar()
        self.progress.set_text(' ')

        ibox.pack_start(self.progress, True, False, 0)
        l = Gtk.Label()
        l.set_size_request(2, 2)
        ibox.pack_start(l, False, False, 0)
        pbox.pack_start(ibox, True, True, 0)

        button = Gtk.Button()
        img = Gtk.Image()
        img.set_from_stock('gtk-stop', Gtk.IconSize.SMALL_TOOLBAR)
        button.set_image(img)

        #pbox.pack_start(button, False, False)
        button.connect('clicked', self.stop)

        box.pack_start(pbox, True, True, 0)
        self.add(box)


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
