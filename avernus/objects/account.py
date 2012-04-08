from avernus.objects import Base
from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship, backref

class Account(Base, object):
    
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
        
class CategoryFilter(Base):
    
    __tablename__ = 'category_filter'
    
    rule = Column(String, primary_key=True)
    active = Column(Boolean)
    priority = Column(Integer)
    category_name = Column(String, ForeignKey('account_category.name'))
    
    def __repr__(self):
        return self.rule
