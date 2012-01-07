from gi.repository import Gtk
from gi.repository import GObject

import logging
import threading, thread

logger = logging.getLogger(__name__)


threadlist = {}
current_id = 0


class GeneratorTask(object):

    def __init__(self, generator, loop_callback=None, complete_callback=None):
        self.generator = generator
        self.loop_callback = loop_callback
        self.complete_callback = complete_callback

        self.id = get_id()
        threadlist[self.id] = self

    def _start(self, *args, **kwargs):
        logger.debug("start thread")
        try:
            self._stopped = False
            for ret in self.generator(*args, **kwargs):
                if self._stopped:
                    self._terminate()
                    break
                GObject.idle_add(self._loop, ret)
            if self.complete_callback is not None:
                GObject.idle_add(self.complete_callback)
            logger.debug("finished thread")
        except:
            logger.debug("thread failed")
            self._terminate()
            GObject.idle_add(self.complete_callback)

    def _terminate(self):
        global threadlist
        try:
            del threadlist[self.id]
        except:
            return
        thread.exit()

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


def terminate_all():
    global threadlist
    for key, val in threadlist.iteritems():
        val.stop();

def get_id():
    global current_id
    current_id += 1
    return current_id
