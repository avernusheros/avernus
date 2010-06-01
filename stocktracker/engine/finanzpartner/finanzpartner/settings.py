# Scrapy settings for finanzpartner project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#
# Or you can copy and paste them from where they're defined in Scrapy:
# 
#     scrapy/conf/default_settings.py
#
EXTENSIONS_BASE = {}
BOT_NAME = 'finanzpartner'
BOT_VERSION = '1.0'
SPIDER_MODULES = ['stocktracker.engine.finanzpartner.finanzpartner.spiders']
NEWSPIDER_MODULE = 'stocktracker.engine.finanzpartner.finanzpartner.spiders'
DEFAULT_ITEM_CLASS = 'stocktracker.engine.finanzpartner.finanzpartner.items.StockInfoItem'
USER_AGENT = '%s/%s' % (BOT_NAME, BOT_VERSION)

ITEM_PIPELINES = ['stocktracker.engine.finanzpartner.finanzpartner.pipelines.PublishSearchResultItem']