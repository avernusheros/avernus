from gi.repository import GObject

import logging
import threading
import thread

logger = logging.getLogger(__name__)


threadlist = {}
current_id = 0


class BackgroundTask():
    def __init__(self, function, complete_callback=None):
        self.function = function
        self.complete_callback = complete_callback
        threading.Thread(target=self.start).start()

    def start(self):
        self.function()
        if self.complete_callback is not None:
            self.complete_callback()


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
            if self.complete_callback is not None:
                GObject.idle_add(self.complete_callback)
        self._terminate()

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

    def __repr__(self):
        return str(self.generator)


def terminate_all():
    global threadlist
    logger.debug("there are %i threads running." % (len(threadlist),))
    for val in threadlist.itervalues():
        logger.debug("stop thread ", val)
        val.stop()


def get_id():
    global current_id
    current_id += 1
    return current_id
