import dbus, gobject
from dbus.mainloop.glib import DBusGMainLoop
from stocktracker import pubsub


NM_STATE_UNKNOWN = 0
NM_STATE_ASLEEP = 1
NM_STATE_CONNECTING = 2
NM_STATE_CONNECTED = 3
NM_STATE_DISCONNECTED = 4


class DBusNetwork(object):

    def __init__(self):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SystemBus()
        try:
            self.nm = dbus.Interface(self.bus.get_object('org.freedesktop.NetworkManager','/org/freedesktop/NetworkManager'),'org.freedesktop.NetworkManager')
            pubsub.publish("network", self.is_online())
            self.bus.add_signal_receiver(self.signal_device_active, signal_name=None, dbus_interface="org.freedesktop.NetworkManager.Connection.Active")
        except:
            pubsub.publish("network", True)

    def signal_device_active(self, data=None):
        if data is not None and data[dbus.String("State")] == NM_STATE_CONNECTING: 
            pubsub.publish("network", True)
        else:
            pubsub.publish("network", False)

    def is_online(self):
        if self.nm.state() == NM_STATE_CONNECTED:
            return True
        return False

if __name__ == '__main__':
    d = DBusNetwork()
    import gtk
    gtk.main()
