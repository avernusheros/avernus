from avernus import objects
from gi.repository import GObject
from sqlalchemy import or_, desc
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, \
    DateTime, Unicode
from sqlalchemy.orm import reconstructor, relationship, backref
import datetime
from bisect import bisect_left



class Asset(objects.Base, GObject.GObject):
    __tablename__ = 'asset'

    type = Column('type', String(20))

    __mapper_args__ = {'polymorphic_on': type}

    id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    date = Column(DateTime, default=datetime.datetime(1970, 1, 1))
    isin = Column(String, default="")
    exchange = Column(String(24))
    currency = Column(String(8))
    price = Column(Float, default=1.0)
    source = Column(String(16))
    change = Column(Float, default=0.0)

    __gsignals__ = {
        'updated': (GObject.SIGNAL_RUN_LAST, None, ())
    }

    def __init__(self, *args, **kwargs):
        GObject.GObject.__init__(self)
        objects.Base.__init__(self, *args, **kwargs)
        self.update_quotation_keys()
    
    @reconstructor
    def _init(self):
        GObject.GObject.__init__(self)
        self.update_quotation_keys()

    def __repr__(self):
        return self.name + " " + self.isin

    def update_quotation_keys(self):
        self.quotation_keys = [q.date for q in self.quotations]
        
    def get_source_info(self, source):
        return [si for si in self.source_info if si.source==source]
        
    @property
    def is_used(self):
        if self.positions:
            return True
        return False

    @property
    def change_percent(self):
        return self.change / (self.price - self.change)

    def delete_quotations(self):
        for quotation in self.quotations:
            quotation.delete()
        objects.Session().commit()

    def get_date_of_newest_quotation(self):
        quotation = objects.Session().query(Quotation).filter_by(asset=self)
        if quotation.count() > 0:
            return quotation.order_by(desc(Quotation.date)).first().date

    def get_price_at_date(self, t):
        if not self.quotations:
            return None
        if len(self.quotations) != len(self.quotation_keys):
            self.update_quotation_keys()
        
        pos = bisect_left(self.quotation_keys, t)
        try:
            return self.quotations[pos].close
        except:
            return self.quotations[-1].close

    def get_quotations(self, start_date):
        return objects.session.query(Quotation).filter(Quotation.asset == self,
                                        Quotation.date >= start_date)\
                                 .order_by(Quotation.date).all()


GObject.type_register(Asset)


class Dividend(objects.Base):
    __tablename__ = 'dividend'
    id = Column(Integer, primary_key=True)
    price = Column(Float)
    cost = Column(Float)
    date = Column(Date)
    position_id = Column(Integer, ForeignKey('position.id'))
    position = relationship('Position', backref=backref('dividends',
                                             cascade="all,delete"))

    @property
    def total(self):
        return self.price - self.cost

    @property
    def dividend_yield(self):
        # div total / position buy value
        return (self.price - self.cost) / self.position.price


class Fund(Asset):
    __tablename__ = 'fund'
    __mapper_args__ = {'polymorphic_identity': 'fund'}
    id = Column(Integer, ForeignKey('asset.id'), primary_key=True)
    ter = Column(Float, default=0.0)
    
    type_str = _("Fund")


class Etf(Asset):
    __tablename__ = 'etf'
    __mapper_args__ = {'polymorphic_identity': 'etf'}
    id = Column(Integer, ForeignKey('asset.id'), primary_key=True)
    ter = Column(Float, default=0.0)
    type_str = _("ETF")


class Bond(Asset):
    # commented so no extra table is generated for bonds
    #__tablename__ = 'bond'
    #id = Column(Integer, ForeignKey('asset.id'), primary_key=True)
    __mapper_args__ = {'polymorphic_identity': 'bond'}
    type_str = _("Bond")

class Quotation(objects.Base):
    __tablename__ = 'quotation'

    id = Column(Integer, primary_key=True)
    exchange = Column(String)
    date = Column(Date)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)
    asset_id = Column(Integer, ForeignKey('asset.id'))
    asset = relationship('Asset', backref=backref('quotations', lazy="immediate",
                    cascade="all,delete", order_by="Quotation.date"))


class SourceInfo(objects.Base):
    __tablename__ = 'source_info'

    id = Column(Integer, primary_key=True)
    source = Column(String)
    info = Column(String)
    asset_id = Column(Integer, ForeignKey('asset.id'))
    asset = relationship('Asset', backref=backref('source_info', lazy="immediate",
                                                 cascade="all,delete"))


class Stock(Asset):
    # commented so no extra table is generated for stocks
    #__tablename__ = 'stock'
    #id = Column(Integer, ForeignKey('asset.id'), primary_key=True)
    __mapper_args__ = {'polymorphic_identity': 'stock'}
    type_str = _("Stock")
    
    
def get_all_assets():
    return objects.session.query(Asset).all()


def get_asset_for_searchstring(searchstring):
    searchstring = unicode('%' + searchstring + '%')
    return objects.session.query(Asset)\
            .filter(or_(Asset.name.like(searchstring),
                     Asset.isin.like(searchstring))).all()
