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

    @property
    def price_per_share(self):
        return self.price / self.quantity


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
        return self.price - self.cost


class BuyTransaction(Transaction):
    __tablename__ = 'portfolio_buy_transaction'
    __mapper_args__ = {'polymorphic_identity': 'portfolio_buy_transaction'}
    id = Column(Integer, ForeignKey('portfolio_transaction.id'),
                primary_key=True)

    def __init__(self, **kwargs):
        Transaction.__init__(self, **kwargs)
        self.position.portfolio.emit("positions_changed")

    @property
    def gain(self):
        if self.position.asset:
            change = self.position.asset.price - self.price_per_share
        else:
            return 0, 0
        absolute = change * self.quantity
        if self.price == 0:
            percent = 0.0
        else:
            percent = absolute / self.price
        return absolute, percent

    @property
    def buy_value(self):
        return self.price

    @property
    def current_value(self):
        return self.quantity * self.position.asset.price

    @property
    def current_change(self):
        return self.position.asset.change, self.position.asset.change_percent

    @property
    def days_gain(self):
        return self.position.asset.change * self.quantity

    def __str__(self):
        return _("buy")

    @property
    def total(self):
        return -self.price - self.cost
