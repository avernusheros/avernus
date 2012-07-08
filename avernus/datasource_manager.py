#!/usr/bin/env python

from avernus.controller import asset_controller
from avernus import data_sources
from avernus.gui import threads
import datetime, re
import logging


logger = logging.getLogger(__name__)

sources = data_sources.sources


class DatasourceManager():

    def __init__(self):
        self.current_searches = []
        self.search_callback = None

    def get_source_count(self):
        return len(sources.items())

    def search(self, searchstring, callback=None, complete_cb=None, threaded=True):
        self.stop_search()
        self.search_callback = callback
        for name, source in sources.iteritems():
            #check whether search function exists
            func = getattr(source, "search", None)
            if func:
                if threaded:
                    try:
                        task = threads.GeneratorTask(func, self._item_found_callback, complete_cb, args=searchstring)
                        self.current_searches.append(task)
                        task.start()
                    except:
                        import traceback
                        traceback.print_exc()
                        logger.error("data source " + name + " not working")
                else:
                    for res in func(searchstring):
                        item, source, source_info = res
                        self._item_found_callback(item, source, source_info)

    def stop_search(self):
        for search in self.current_searches:
            search.stop()
        self.current_searches = []

    def _item_found_callback(self, item, source, source_info=None):
        #mandatory: isin, type, name
        if not self.validate_isin(item['isin']):
            return
        new = False
        asset = asset_controller.check_asset_existance(source=source.name,
                                                       isin = item['isin'],
                                                       currency = item['currency'])
        if not asset:
            new = True
            item['source'] = source.name
            asset = asset_controller.new_asset(**item)
        if source_info is not None:
            asset_controller.new_source_info(source=source.name, asset=asset, info=source_info)
        if new and self.search_callback:
            self.search_callback(asset, 'source')

    def validate_isin(self, isin):
        return re.match('^[A-Z]{2}[A-Z0-9]{9}[0-9]$', isin)

    def update_assets(self, stocks):
        if len(stocks) == 0:
            return
        for name, source in sources.iteritems():
            temp = filter(lambda s: s.source == name, stocks)
            if len(temp) > 0:
                logger.debug("updating %s using %s" % (temp, source.name))
                for ret in source.update_stocks(temp):
                    ret.emit("updated")
                    yield 1

    def update_asset(self, asset):
        self.update_assets([asset])

    def get_historical_prices(self, stock, start_date=None, end_date=None):
        if end_date is None:
            end_date = datetime.date.today() - datetime.timedelta(days=1)
        start_date = asset_controller.get_date_of_newest_quotation(stock)
        if start_date is None:
            start_date = datetime.date(end_date.year - 20, end_date.month, end_date.day)
        if start_date < end_date:
            for qt in sources[stock.source].update_historical_prices(stock, start_date, end_date):
                #qt : (stock, exchange, date, open, high, low, close, vol)
                if qt is not None:
                    yield asset_controller.new_quotation(stock=qt[0], exchange=qt[1], \
                            date=qt[2], open=qt[3], high=qt[4], \
                            low=qt[5], close=qt[6], vol=qt[7])
        #needed to run as generator thread
        yield 1

    def update_historical_prices(self, stock):
        end_date = datetime.date.today() - datetime.timedelta(days=1)
        start_date = asset_controller.get_date_of_newest_quotation(stock)
        if start_date == None:
            start_date = datetime.date(end_date.year - 20, end_date.month, end_date.day)
        yield self.get_historical_prices(stock, start_date, end_date)
