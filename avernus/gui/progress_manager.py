import gtk
import gobject
from avernus import pubsub


class ProgressMonitor(gtk.Frame):
    """
        A progress monitor
    """
    def __init__(self,id, desc, icon):
        """
        Initializes the monitor
        """
        gtk.Frame.__init__(self)
        self.desc = desc
        self.icon = icon
        self.id = id
        self._setup_widgets()
        self.show_all()
        
    def progress_update(self, percent):
        """
        Called when the progress has been updated
        """
        gobject.idle_add(self.progress.set_fraction, float(percent) / 100)
        gobject.idle_add(self.progress.set_text, '%d%%' % percent)

    def progress_update_pulse(self, *args):
        gobject.idle_add(self.progress.pulse)
        return True
        
    def progress_update_auto(self):
        gobject.timeout_add(100, self.progress_update_pulse)

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
        self.set_shadow_type(gtk.SHADOW_NONE)
        desc = self.desc
        icon = self.icon

        box = gtk.VBox()
        box.set_border_width(3)
        label = gtk.Label(desc)
        label.set_use_markup(True)
        label.set_alignment(0, 0.5)
        label.set_padding(3, 0)

        box.pack_start(label, False, False)

        pbox = gtk.HBox()
        pbox.set_spacing(3)

        img = gtk.Image()
        img.set_from_stock(icon, gtk.ICON_SIZE_SMALL_TOOLBAR)
        img.set_size_request(32, 32)
        pbox.pack_start(img, False, False)

        ibox = gtk.VBox()
        l = gtk.Label()
        l.set_size_request(2, 2)
        ibox.pack_start(l, False, False)
        self.progress = gtk.ProgressBar()
        self.progress.set_text(' ')

        ibox.pack_start(self.progress, True, False)
        l = gtk.Label()
        l.set_size_request(2, 2)
        ibox.pack_start(l, False, False)
        pbox.pack_start(ibox, True, True)

        button = gtk.Button()
        img = gtk.Image()
        img.set_from_stock('gtk-stop', gtk.ICON_SIZE_SMALL_TOOLBAR)
        button.set_image(img)

        #pbox.pack_start(button, False, False)
        button.connect('clicked', self.stop)

        box.pack_start(pbox, True, True)
        self.add(box)


box = None
monitors = {}

def add_monitor(id, description, stock_icon):
    """
    Adds a progress box

    @param description: a description of the event
    @param stock_icon: the icon to display
    """
    if not monitors:
        box.show()
    monitor = ProgressMonitor(id, description, stock_icon)
    #self.box.add(monitor)
    box.pack_start(monitor, False, False)

    monitors[id] = monitor
    return monitor

def remove_monitor(id):
    """
    Removes a monitor from the manager
    """
    box.remove(monitors[id])
    del monitors[id]
    if not monitors:
        box.hide()
