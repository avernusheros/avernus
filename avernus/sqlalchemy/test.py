from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, Date, Boolean
from sqlalchemy import create_engine
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import sessionmaker

from csvimporter import CsvImporter

# base for the objects
Base = declarative_base()

class Account(Base):
    
    __tablename__ = 'account'
    
    name = Column(String, primary_key=True)
    type = Column(Integer)
    balance = Column(Float)
    transactions = relationship('AccountTransaction', backref='account')
    
    def __init__(self, name):
        self.name = name
        self.balance = 0.0
        self.type = 1
        
    def __repr__(self):
        return "Account<%s>" % self.name
        
class AccountCategory(Base):
    
    __tablename__ = 'account_category'
    
    name = Column(String, primary_key=True)
    parent_name = Column(Integer, ForeignKey('account_category.name'))
    parent = relationship('AccountCategory', remote_side=[name], backref='children')
    filters = relationship('CategoryFilter', backref='category')
    
    def __init__(self, name):
        self.name = name
        
    def __repr__(self):
        return "AccountCategory<%s>" % self.name
        
class AccountTransaction(Base):
    
    __tablename__ = 'account_transaction'
    
    description = Column(String, primary_key=True)
    amount = Column(Float, primary_key=True)
    date = Column(Date, primary_key=True)
    account_name = Column(Integer, ForeignKey('account.name'))
    
    def __init__(self, description):
        self.description = description
        
    def __repr__(self):
        return "AccountTransaction<"+str(self.date) +"|"+str(self.amount)+">"
        
class AssetDimensionValue(Base):
    
    __tablename__ = 'asset_dimension_value'
    
    id = Column(Integer, primary_key=True)
    value = Column(Float)
    
       
class Benchmark(Base):
    
    __tablename__ = 'benchmark'
    
    percentage = Column(Float, primary_key=True)
    portfolio_name = Column(String, ForeignKey('portfolio.name'), primary_key=True)

class CategoryFilter(Base):
    
    __tablename__ = 'category_filter'
    
    rule = Column(String, primary_key=True)
    active = Column(Boolean)
    priority = Column(Integer)
    category_name = Column(String, ForeignKey('account_category.name'))
    
    def __repr__(self):
        return self.rule
        
class Dimension(Base):
    
    __tablename__ = 'dimension'
    
    name = Column(String, primary_key=True)
    values = relationship('DimensionValue', backref='dimension')
    
class DimensionValue(Base):
    
    __tablename__ = 'dimension_value'
    
    name = Column(String, primary_key=True)
    dimension_name = Column(String, ForeignKey('dimension.name'), primary_key=True)
        
class Portfolio(Base):
    
    __tablename__ = 'portfolio'
    
    name = Column(String, primary_key=True)
    last_update = Column(Date)
    comment = Column(String) # ? is that used ?
    benchmarks = relationship('Benchmark', backref='portfolio')
        
class Stock(Base):
    
    __tablename__ = 'stock'
    
    isin = Column(String, primary_key=True)
    currency = Column(String, primary_key=True)
    source = Column(String, primary_key=True)
    type = Column(Integer)
    name = Column(String)
    exchance = Column(String)
    price = Column(Float)
    date = Column(Date)
    change = Column(Float)
    ter = Column(Float) # ?? Wozu brauchen wir das in jedem Stock??
    

    
    
# connect to the database
engine = create_engine('sqlite:///sqlite.db', echo=True)     
# create the tables, if not there already
Base.metadata.create_all(engine)
# get a session
Session = sessionmaker(bind=engine)
session = Session()

#acc = Account("hans")
#session.add(acc)

# query for the present objects
accounts = session.query(Account).all()
print accounts

session.commit()
