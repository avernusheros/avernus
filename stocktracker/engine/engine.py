#!/usr/bin/env python
#First, import os and set the settings module relative to the root dir of the project.
#It is important that this is done before importing execute
#make the project root known. This has to be adjusted according from where this is called.
import sys
sys.path.append("finanzpartner")
import os
os.environ.setdefault('SCRAPY_SETTINGS_MODULE', 'stocktracker.engine.finanzpartner.finanzpartner.settings')

#import the execute function and invoke it with the appropriate commands
from scrapy.cmdline import execute 

from stocktracker.engine.finanzpartner.finanzpartner.spiders import onvistaSpider

def onvista_search(string, callback, only = True):
    spider = onvistaSpider.SPIDER
    spider.setCallback(callback)
    spider.schedule_search(string, only=only)
    execute(['start.py','crawl','onvistaSearch'])
    print "Finished Search"
#execute(['start.py','crawl','finanzpartner.de'])
