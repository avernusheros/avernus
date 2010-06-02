# -*- coding: utf-8 -*-

import gtk
from stocktracker.engine import engine
from scrapy.core.manager import ExecutionManager
from stocktracker.engine.finanzpartner.finanzpartner.spiders import onvistaSpider

class OnvistaPlugin():
    configurable = False
    
    def __init__(self):
        self.name = 'onvista.de'
        self.manager = ExecutionManager()
        self.manager.configure()

    def activate(self):
        self.api.register_datasource(self, self.name)
        
                        
    def deactivate(self):
        self.api.deregister_datasource(self, self.name)
        
    def search(self, searchstring, callback):
        print "searching using ", self.name
        spider = onvistaSpider.SPIDER
        spider.setCallback(callback)
        spider.schedule_search(searchstring)
        self.manager.queue.append_spider(spider)
        self.manager.start()
