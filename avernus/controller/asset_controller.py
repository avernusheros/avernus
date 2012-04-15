from avernus.objects.asset import Asset
from avernus.objects.asset import Quotation
from avernus.objects.asset import SourceInfo
from avernus.objects.container import Position
from avernus.objects import session, asset
from avernus import pubsub
from sqlalchemy import or_
import datetime

datasource_manager = None

def check_asset_existance(source, isin, currency):
    return 0 < session.query(Asset).filter(Asset.isin == isin,
                                     Asset.source == source,
                                     Asset.currency == currency).count()

def get_all_used_assets():
    return session.query(Asset).join(Position).distinct().all()

def get_asset_for_searchstring(searchstring):
    searchstring = '%' + searchstring + '%'
    return session.query(Asset).filter(or_(Asset.name.like(searchstring), Asset.isin.like(searchstring))).all()

def get_change_percent(asset):
    return asset.change * 100.0 / (asset.price - asset.change)

def get_quotations_for_asset(asset, start_date):
    print "TODO"
    #TODO
    
def get_source_info(source, ass=None):
    return session.query(SourceInfo).filter_by(asset=ass, source=source).all()
    
def get_ter(ass):
    if isinstance(ass, asset.Fund):
        return ass.ter
    return 0.0

def new_asset(assettype = Asset, name = "", isin=0, source="",
                currency="", exchange="", price=1.0,
                change=0.0, date=datetime.datetime.now(), **kwargs):
    asset = assettype(name=name, isin=isin, source=source,
                        currency=currency,
                        exchange=exchange,
                        price=price,
                        change=change,
                        date=date)
    session.add(asset)
    return asset

def new_dividend(price=0.0, cost=0.0, date=datetime.date.today(), position=None):
    div = Dividend(price=price, cost=cost, date=date, position=position)
    session.add(div)
    return div

def new_transaction(*args, **kwargs):
    print "TODO"
    #TODO
    
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

def new_transaction(*args, **kwargs):
    print "TODO"
    #TODO

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

def update_asset(asset):
    datasource_manager.update_asset(asset)
    

