# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/topics/item-pipeline.html

import sys
sys.path.append("../../../")

class FinanzpartnerPipeline(object):
    def process_item(self, domain, item):
        print "[MAGIC] Processing: ", item, domain
        return item
    
from stocktracker import pubsub
    
class PublishSearchResultItem(object):
    def process_item(self, domain, item):
        pubsub.publish("OnvistaSearchItem", item=item)
        return item
