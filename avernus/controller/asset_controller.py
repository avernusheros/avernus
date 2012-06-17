from avernus.objects.asset import Asset
from avernus.objects.asset import Quotation
from avernus.objects.asset import Dividend
from avernus.objects.asset import SourceInfo
from avernus.objects.asset import BuyTransaction, SellTransaction, Transaction
from avernus.objects.container import Position, Container, PortfolioPosition
from avernus.controller.object_controller import delete_object
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

def delete_quotations_from_asset(asset):
    for quotation in asset.quotations:
        Session().delete(quotation)
    Session().commit()

def get_all_assets():
    return session.query(Asset).all()

def get_all_used_assets():
    return Session().query(Asset).join(Position).distinct().all()

def is_asset_used(asset):
    return len(asset.positions) != 0

def get_all_used_assets_for_portfolio(portfolio):
    return Session().query(Asset).join(PortfolioPosition).filter(PortfolioPosition.portfolio==portfolio).distinct().all()

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
    close = Session().query(Quotation.close).filter_by(asset=asset, date=t).first()
    if close:
        return close[0]

def get_price_at_date(asset, t, min_t):
    close = Session().query(Quotation.close)\
            .filter(Quotation.asset==asset, Quotation.date>=min_t, Quotation.date<=t)\
            .order_by(desc(Quotation.date)).first()
    if close:
        return close[0]

def get_buy_transaction(position):
    return session.query(BuyTransaction).filter_by(position=position).first()

def get_sell_transactions(position):
    return Session().query(SellTransaction).filter_by(position=position).all()

def get_source_info(source, ass=None):
    return Session.query(SourceInfo).filter_by(asset=ass, source=source).all()

def get_ter(ass):
    if isinstance(ass, asset.Fund):
        return ass.ter
    return 0.0

def get_total_for_dividend(dividend):
    return dividend.price - dividend.cost

def get_dividend_yield(dividend):
    # div total / position buy value
    return (dividend.price - dividend.cost) / (dividend.position.quantity * dividend.position.price)

def get_total_for_transaction(transaction):
    if isinstance(transaction, BuyTransaction):
        sign = -1
    else:
        sign = 1
    return sign * transaction.price * transaction.quantity + transaction.cost

def get_transactions(portfolio, asset):
    return Session().query(Transaction).join(PortfolioPosition).filter(PortfolioPosition.portfolio==portfolio, Position.asset==asset).order_by(Transaction.date).all()

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
    # not needed, since already added to the session via cascade
    #Session().add(qu)
    return qu

def new_source_info(source, asset, info):
    si = SourceInfo(source = source, asset = asset, info = info)
    session.add(si)
    return si

def new_buy_transaction(*args, **kwargs):
    ta = BuyTransaction(**kwargs)
    return ta

def new_sell_transaction(*args, **kwargs):
    ta = SellTransaction(**kwargs)
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

