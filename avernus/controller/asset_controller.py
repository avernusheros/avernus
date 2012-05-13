from avernus.objects.asset import Asset
from avernus.objects.asset import Quotation
from avernus.objects.asset import Dividend
from avernus.objects.asset import SourceInfo
from avernus.objects.asset import Transaction
from avernus.objects.container import Position, Container
# Session is the class, session the normal instance
from avernus.objects import Session, session, asset
from avernus import pubsub
from sqlalchemy import or_, desc
import datetime

datasource_manager = None

def check_asset_existance(source, isin, currency):
    return 0 < session.query(Asset).filter_by(isin = isin,
                                            source = source,
                                            currency = currency).count()

def get_all_used_assets():
    return Session().query(Asset).join(Position).distinct().all()

def get_asset_for_searchstring(searchstring):
    searchstring = '%' + searchstring + '%'
    return session.query(Asset).filter(or_(Asset.name.like(searchstring), Asset.isin.like(searchstring))).all()

def get_change_percent(asset):
    return asset.change * 100.0 / (asset.price - asset.change)

def get_date_of_newest_quotation(asset):
    quotation = Session().query(Quotation).filter_by(asset=asset)
    if quotation.count() > 0:
        return quotation.order_by(desc(Quotation.date)).first().date

def get_price_at_date(asset, t):
    quotation = Session().query(Quotation).filter_by(asset=asset, date=t).first()
    if quotation:
        return quotation.close

def get_buy_transaction(position):
    return session.query(Transaction).filter_by(position=position, type=1).first()

def get_sell_transactions(position):
    return Session().query(Transaction).filter_by(position=position, type=0).all()

def get_source_info(source, ass=None):
    return Session.query(SourceInfo).filter_by(asset=ass, source=source).all()

def get_ter(ass):
    if isinstance(ass, asset.Fund):
        return ass.ter
    return 0.0

def get_total_for_dividend(dividend):
    return dividend.price - dividend.cost

def get_total_for_transaction(transaction):
    if transaction.type==1:
        sign = -1
    else:
        sign = 1
    return sign * transaction.price * transaction.quantity + transaction.cost

def get_transaction_total(transaction):
    #FIXME declare types somewhere
    if transaction.type==1:
        sign = -1.0
    else:
        sign = 1.0
    return sign*transaction.price*transaction.quantity + transaction.cost

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

def new_quotation(stock, exchange, date, open, high, low, close, vol):
    qu = Quotation(asset=stock,
                   exchange=exchange,
                   date=date,
                   open=open,
                   high=high,
                   low=low,
                   close=close,
                   volume=vol)
    #only add it to the session if it is not present in another session
    currentSession = Session.object_session(qu)
    if not currentSession:
        Session().add(qu)
    return qu

def new_source_info(source, asset, info):
    si = SourceInfo(source = source, asset = asset, info = info)
    session.add(si)
    return si

def new_transaction(*args, **kwargs):
    ta = Transaction(**kwargs)
    session.add(ta)
    return ta

def update_all(*args):
    items = get_all_used_assets()
    itemcount = len(items)
    count = 0.0
    for item in datasource_manager.update_assets(items):
        count += 1.0
        yield count / itemcount
    for item in Session().query(Container).all():
        item.last_update = datetime.datetime.now()
    pubsub.publish("stocks.updated", item)
    Session().commit()
    yield 1

def update_asset(asset):
    datasource_manager.update_asset(asset)

def update_historical_prices(*args):
    assets = get_all_used_assets()
    l = len(assets)
    i = 0.0
    for asset in assets:
        for qt in datasource_manager.get_historical_prices(asset):
            yield i / l
        i += 1.0
        yield i / l
    Session().commit()
    yield 1

