from avernus.objects.asset import Asset
from avernus.objects.asset import Quotation
from avernus.objects.asset import SourceInfo
from avernus.objects.container import Position
from avernus.objects import session
from avernus import pubsub
from sqlalchemy import or_
import datetime

datasource_manager = None


def get_asset_for_searchstring(searchstring):
    searchstring = '%' + searchstring + '%'
    return session.query(Asset).filter(or_(Asset.name.like(searchstring), Asset.isin.like(searchstring))).all()

def get_quotations_for_asset(asset, start_date):
    print "TODO"
    #TODO

def new_asset(assettype = Asset, name = "", isin=0, source="",
                currency="", exchange="", **kwargs):
    asset = assettype(name=name, isin=isin, source=source,
                        currency=currency,
                        exchange=exchange)
    session.add(asset)
    return asset

def new_dividend(*args, **kwargs):
    print "TODO"
    #TODO

def new_transaction(*args, **kwargs):
    print "TODO"
    #TODO

def check_asset_existance(source, isin, currency):
    return 0 < session.query(Asset).filter(Asset.isin == isin,
                                     Asset.source == source,
                                     Asset.currency == currency).count()

def update_asset(asset):
    datasource_manager.update_asset(asset)


def get_all_used_assets():
    return session.query(Asset).join(Position).distinct().all()

def update_all(*args):
    items = get_all_used_assets()
    itemcount = len(items)
    count = 0.0
    for item in datasource_manager.update_assets(items):
        count += 1.0
        yield count / itemcount
    for container in getAllPortfolio() + getAllWatchlist():
        container.last_update = datetime.datetime.now()
    pubsub.publish("stocks.updated")
    yield 1


def new_quotation(stock, exchange, date, open, high, low, close, vol):
    qu = Quotation(stock=stock,
                   exchange=exchange,
                   date=date,
                   open=open,
                   high=high,
                   low=low,
                   close=close,
                   volume=vol)
    session.add(qu)
    return qu

def new_source_info(source, asset, info):
    si = SourceInfo(source = source, asset = asset, info = info)
    session.add(si)
    return si
