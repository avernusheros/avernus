from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, Date
from sqlalchemy import create_engine
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref

engine = create_engine('sqlite:///:memory:', echo=True)
Base = declarative_base()

class Account(Base):
	
	__tablename__ = 'account'
	
	name = Column(String)
	id = Column(Integer, primary_key=True)
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
	
	id = Column(Integer, primary_key=True)
	name = Column(String)
	parent_id = Column(Integer, ForeignKey('account_category.id'))
	parent = relationship('AccountCategory', remote_side=[id], backref='children')
	
	
	def __init__(self, name):
		self.name = name
		
	def __repr__(self):
		return "AccountCategory<%s>" % self.name
		
class AccountTransaction(Base):
	
	__tablename__ = 'account_transaction'
	
	id = Column(Integer, primary_key=True)
	description = Column(String)
	amount = Column(Float)
	date = Column(Date)
	account_id = Column(Integer, ForeignKey('account.id'))
	
	def __init__(self, description):
		self.description = description
	
		
Base.metadata.create_all(engine)

from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)

session = Session()

account = Account("PSD")
session.add(account)
cat1 = AccountCategory('fix')
cat2 = AccountCategory('versicherung')
session.add_all([cat1, cat2])
tran1 = AccountTransaction("eine trans")
tran2 = AccountTransaction("noch trans")
session.add_all([tran1, tran2])
tran1.account = account
tran2.account = account
cat2.parent = cat1
session.commit()


print cat1.children
print tran1.account
print account.transactions
