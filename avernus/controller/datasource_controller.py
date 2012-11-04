from avernus import data_sources, objects
from avernus.gui import threads
from avernus.objects import asset as asset_m, container, position
import datetime
import logging
import re


logger = logging.getLogger(__name__)
sources = data_sources.sources
current_searches = []
search_callback = None

ASSET_TYPES = {
               asset_m.Bond: _('Bond'),
               asset_m.Etf: _('ETF'),
               asset_m.Fund: _('Fund'),
               asset_m.Stock: _('Stock'),
               }


def get_source_count():
    return len(sources.items())


def search(searchstring, callback=None, complete_cb=None, threaded=True):
    stop_search()
    global search_callback
    search_callback = callback
    for name, source in sources.iteritems():
        # check whether search function exists
        func = getattr(source, "search", None)
        if func:
            if threaded:
                try:
                    task = threads.GeneratorTask(func, _item_found_callback, complete_cb, args=searchstring)
                    current_searches.append(task)
                    task.start()
                except:
                    import traceback
                    traceback.print_exc()
                    logger.error("data source " + name + " not working")
            else:
                for res in func(searchstring):
                    item, source, source_info = res
                    _item_found_callback(item, source, source_info)


def stop_search():
    global current_searches
    for search in current_searches:
        search.stop()
    current_searches = []


def _item_found_callback(item, source, source_info=None):
    # mandatory: isin, type, name
    if not validate_isin(item['isin']):
        return
    new = False
    new_asset = check_asset_existance(source=source.name,
                                                   isin=item['isin'],
                                                   currency=item['currency'])
    # FIXME ugly
    if not new_asset:
        new = True
        item['source'] = source.name
        assettype = item['assettype']
        del item['assettype']
        del item['yahoo_id']
        new_asset = assettype(**item)
        if source_info is not None:
            asset_m.SourceInfo(source=source.name,
                               asset=new_asset,
                               info=source_info)
    if new and search_callback:
        search_callback(new_asset, 'source')


def validate_isin(isin):
    return re.match('^[A-Z]{2}[A-Z0-9]{9}[0-9]$', isin)


def update_assets(assets):
    if not assets:
        return
    for name, source in sources.iteritems():
        temp = filter(lambda s: s.source == name, assets)
        if temp:
            logger.debug("updating %s using %s" % (temp, source.name))
            for ret in source.update_stocks(temp):
                ret.emit("updated")
                yield ret


def update_asset(asset):
    update_assets([asset])


def get_historical_prices(asset, start_date=None, end_date=None):
    if end_date is None:
        end_date = datetime.date.today() - datetime.timedelta(days=1)
    start_date = asset.get_date_of_newest_quotation()
    if start_date is None:
        start_date = datetime.date(end_date.year - 20, end_date.month, end_date.day)
    if start_date < end_date:
        for qt in sources[asset.source].update_historical_prices(asset, start_date, end_date):
            # qt : (stock, exchange, date, open, high, low, close, vol)
            if qt is not None:
                yield asset.Quotation(asset=qt[0], exchange=qt[1], \
                        date=qt[2], open=qt[3], high=qt[4], \
                        low=qt[5], close=qt[6], vol=qt[7])
    # needed to run as generator thread
    yield 1


def update_historical_prices_asset(asset):
    end_date = datetime.date.today() - datetime.timedelta(days=1)
    start_date = asset.get_date_of_newest_quotation()
    if start_date == None:
        start_date = datetime.date(end_date.year - 20, end_date.month, end_date.day)
    yield get_historical_prices(asset, start_date, end_date)


def check_asset_existance(source, isin, currency):
    return 0 < objects.session.query(asset_m.Asset).filter_by(isin=isin,
                                            source=source,
                                            currency=currency).count()


def update_all(*args):
    items = position.get_all_used_assets()
    itemcount = len(items)
    count = 0.0
    for item in update_assets(items):
        count += 1
        yield count / itemcount
    for item in objects.Session().query(container.Container).all():
        item.last_update = datetime.datetime.now()
    objects.Session().commit()
    yield 1


def update_historical_prices(*args):
    assets = position.get_all_used_assets()
    l = len(assets)
    i = 0.0
    for asset in assets:
        for qt in get_historical_prices(asset):
            yield i / l
        i += 1.0
        yield i / l
    objects.Session().commit()
    yield 1


def update_positions(portfolio):
    items = set(pos.asset for pos in portfolio if pos.quantity > 0)
    itemcount = len(items)
    count = 0.0
    for i in update_assets(items):
        count += 1
        yield count / itemcount
    portfolio.last_update = datetime.datetime.now()
    portfolio.emit("updated")
    yield 1