from avernus import objects
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship, backref


class Transaction(objects.Base):
    __tablename__ = 'portfolio_transaction'
    type = Column('type', String(20))
    __mapper_args__ = {'polymorphic_on': type}

    id = Column(Integer, primary_key=True)
    date = Column(Date)
    quantity = Column(Float)
    price = Column(Float)
    cost = Column(Float)
    position_id = Column(Integer, ForeignKey('portfolio_position.id'))
    position = relationship('PortfolioPosition',
                         backref=backref('transactions', cascade="all,delete"))


class SellTransaction(Transaction):
    __tablename__ = 'portfolio_sell_transaction'
    __mapper_args__ = {'polymorphic_identity': 'portfolio_sell_transaction'}
    id = Column(Integer, ForeignKey('portfolio_transaction.id'),
                primary_key=True)

    def __init__(self, **kwargs):
        Transaction.__init__(self, **kwargs)
        self.position.portfolio.emit("positions_changed")

    def __str__(self):
        return _("sell")

    @property
    def total(self):
        return self.price * self.quantity + self.cost


class BuyTransaction(Transaction):
    __tablename__ = 'portfolio_buy_transaction'
    __mapper_args__ = {'polymorphic_identity': 'portfolio_buy_transaction'}
    id = Column(Integer, ForeignKey('portfolio_transaction.id'),
                primary_key=True)

    def __init__(self, **kwargs):
        Transaction.__init__(self, **kwargs)
        self.position.portfolio.emit("positions_changed")

    def __str__(self):
        return _("buy")

    @property
    def total(self):
        return -1.0 * self.price * self.quantity + self.cost
