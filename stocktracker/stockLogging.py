'''
Created on Apr 11, 2010

@author: bastian
'''

import logging
import logging.handlers
import time

logger = logging.getLogger('StockTracker')
name = "log/" + str(time.time()) + ".log"
logger.setLevel(logging.DEBUG)
handler = logging.handlers.WatchedFileHandler(name)
handler.setFormatter(logging.Formatter("%(levelname)s %(module)s.%(funcName)s %(asctime)s: %(message)s"))
logger.addHandler(handler)