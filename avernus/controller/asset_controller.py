from avernus.objects.asset import Asset
from avernus.objects.asset import Quotation
from avernus.objects.asset import SourceInfo
from avernus.objects import session
from sqlalchemy import or_

datasource_manager = None


def get_asset_for_searchstring(searchstring):
    searchstring = '%' + searchstring + '%'
    return session.query(Asset).filter(or_(Asset.name.like(searchstring), Asset.isin.like(searchstring))).all()

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

def update_price(asset):
    datasource_manager.update_asset(asset)


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
