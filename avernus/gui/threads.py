from gi.repository import GObject

import logging
import threading

logger = logging.getLogger(__name__)



class BackgroundTask():
    def __init__(self, function, complete_callback=None):
        self.function = function
        self.complete_callback = complete_callback
        threading.Thread(target=self.start).start()

    def start(self):
        self.function()
        if self.complete_callback is not None:
            self.complete_callback()


class GeneratorTask(threading.Thread):

    def __init__(self, generator, loop_callback=None, complete_callback=None,  args=()):
        threading.Thread.__init__(self, group=None)
        self.generator = generator
        self.loop_callback = loop_callback
        self.complete_callback = complete_callback
        self.args = args

        #Thread event, stops the thread if it is set.
        self.stopthread = threading.Event()

    def run(self, *args, **kwargs):
        logger.debug("start thread")
        logger.debug(args)
        try:
            for ret in self.generator(self.args):
                if self.stopthread.isSet():
                    return

                if self.loop_callback:
                    if ret is None:
                        ret = ()
                    elif not isinstance(ret, tuple):
                        ret = (ret,)
                    GObject.idle_add( self.loop_callback, *ret)

            if self.complete_callback is not None:
                GObject.idle_add(self.complete_callback)
            logger.debug("finished thread")
        except:
            logger.debug("thread failed")
            import traceback
            traceback.print_exc()
            if self.complete_callback is not None:
                GObject.idle_add(self.complete_callback)

    def stop(self):
        """Stop method, sets the event to terminate the thread's main loop"""
        logger.debug("stopped thread")
        self.stopthread.set()

    def __repr__(self):
        return str(self.generator)


def terminate_all():
    threadlist = threading.enumerate()
    logger.debug("there are %i threads running." % (len(threadlist),))
    for val in threadlist:
        try:
            val.stop()
            val.join()
            logger.debug("stop thread " + str(val))
        except:
            logger.debug("unable to stop thread, started?")
    logger.debug("all threads terminated")


