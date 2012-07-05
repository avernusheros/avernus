from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from avernus.objects import Base


TYPES = {
        0: _('Savings'),
        1: _('Checking'),
        2: _('Trading'),
        }


class Account(Base):

    __tablename__ = 'account'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    type = Column(Integer, default=1)
    balance = Column(Float, default=0.0)
    transactions = relationship('AccountTransaction', backref='account', cascade="all,delete")

    def __iter__(self):
        return self.transactions.__iter__()

    def __repr__(self):
        return "Account<%s>" % self.name


class AccountCategory(Base):

    __tablename__ = 'account_category'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    parent_id = Column(Integer, ForeignKey('account_category.id'))
    parent = relationship('AccountCategory', remote_side=[id], backref='children')

    def __repr__(self):
        return "AccountCategory<%s>" % self.name


class AccountTransaction(Base):

    __tablename__ = 'account_transaction'

    id = Column(Integer, primary_key=True)
    description = Column(String)
    amount = Column(Float)
    date = Column(Date)
    account_id = Column(Integer, ForeignKey('account.id'))
    transfer_id = Column(Integer, ForeignKey('account_transaction.id'))
    transfer = relationship('AccountTransaction', remote_side=[id], uselist=False,post_update=True)
    category_id = Column(String, ForeignKey('account_category.id'))
    category = relationship('AccountCategory', remote_side=[AccountCategory.id])

    def __repr__(self):
        return "AccountTransaction<"+str(self.date) +"|"+str(self.amount)+">"


class CategoryFilter(Base):

    __tablename__ = 'category_filter'

    id = Column(Integer, primary_key=True)
    rule = Column(String)
    active = Column(Boolean)
    priority = Column(Integer)
    category_id = Column(String, ForeignKey('account_category.id'))
    category = relationship('AccountCategory', remote_side=[AccountCategory.id])

    def __repr__(self):
        return self.rule
