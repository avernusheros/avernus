# -*- coding: utf-8 -*-

import scrapy.core.manager as manager
from stocktracker.engine.finanzpartner.finanzpartner.spiders import onvistaSpider

class OnvistaPlugin():
    configurable = False
    
    def __init__(self):
        self.name = 'onvista.de'
        self.manager = manager.scrapymanager

    def activate(self):
        self.api.register_datasource(self, self.name)
        
                        
    def deactivate(self):
        self.api.deregister_datasource(self, self.name)
        
    def search(self, searchstring, callback):
        print "searching using ", self.name
        spider = onvistaSpider.OnvistaSpider()
        onvistaSpider.SPIDER = spider
        spider.setCallback(callback)
        spider.schedule_search(searchstring)
        self.manager.configure()
        self.manager.queue.append_spider(spider)
        self.manager.start()
