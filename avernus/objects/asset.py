from avernus.objects import Base
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship, backref


class Asset(Base):
    __tablename__ = 'asset'

    type = Column('type', String(20))

    __mapper_args__ = {'polymorphic_on': type}

    id = Column(Integer, primary_key=True)
    name = Column(String)
    date = Column(DateTime)
    isin = Column(String)
    exchange = Column(String)
    currency = Column(String)
    price = Column(Float)
    source = Column(String)
    change = Column(Float)


class Dividend(Base):
    __tablename__ = 'dividend'
    id = Column(Integer, primary_key=True)
    price = Column(Float)
    cost = Column(Float)
    date = Column(Date)
    position_id = Column(Integer, ForeignKey('position.id'))
    position = relationship('Position', backref=backref('dividends', cascade="all,delete"))


class Fund(Asset):
    __tablename__ = 'fund'
    __mapper_args__ = {'polymorphic_identity': 'fund'}
    id = Column(Integer, ForeignKey('asset.id'), primary_key=True)
    ter = Column(Float)


class Etf(Asset):
    __tablename__ = 'etf'
    __mapper_args__ = {'polymorphic_identity': 'etf'}
    id = Column(Integer, ForeignKey('asset.id'), primary_key=True)
    ter = Column(Float)


class Bond(Asset):
    __tablename__ = 'bond'
    __mapper_args__ = {'polymorphic_identity': 'bond'}
    id = Column(Integer, ForeignKey('asset.id'), primary_key=True)


class Quotation(Base):
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
    asset = relationship('Asset', backref=backref('quotations', cascade="all,delete"))


class SourceInfo(Base):
    __tablename__ = 'source_info'

    id = Column(Integer, primary_key=True)
    source = Column(String)
    info = Column(String)
    asset_id = Column(Integer, ForeignKey('asset.id'))
    asset = relationship('Asset', backref=backref('source_info', cascade="all,delete"))


class Stock(Asset):
    __tablename__ = 'stock'
    __mapper_args__ = {'polymorphic_identity': 'stock'}
    id = Column(Integer, ForeignKey('asset.id'), primary_key=True)


class Transaction(Base):
    __tablename__ = 'portfolio_transaction'
    id = Column(Integer, primary_key=True)
    date = Column(Date)
    quantity = Column(Float)
    price = Column(Float)
    cost = Column(Float)
    type = Column(Integer)
    position_id = Column(Integer, ForeignKey('portfolio_position.id'))
    position = relationship('PortfolioPosition', backref=backref('transactions', cascade="all,delete"))