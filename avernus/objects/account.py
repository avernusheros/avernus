from avernus import objects
from gi.repository import GObject
from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey, \
    event, or_, Unicode
from sqlalchemy.orm import reconstructor, relationship
import datetime

TYPES = {
        0: _('Savings'),
        1: _('Checking'),
        2: _('Trading'),
        }


class AllAccount(GObject.GObject):

    __gsignals__ = {
        'balance_changed': (GObject.SIGNAL_RUN_LAST, None,
                      (float,)),
        'transaction_added': (GObject.SIGNAL_RUN_LAST, None,
                      (object,))
    }

    def __init__(self):
        GObject.GObject.__init__(self)
        for acc in get_all_accounts():
            acc.connect("balance_changed", self.on_balance_changed)
            acc.connect("transaction_added", self.on_transaction_added)

    def __iter__(self):
        return self.transactions.__iter__()

    @property
    def transactions(self):
        return get_all_transactions()

    @property
    def balance(self):
        return sum([acc.balance for acc in get_all_accounts()])

    def on_balance_changed(self, *args):
        self.emit("balance_changed", self.balance)

    def on_transaction_added(self, account, transaction):
        self.emit("transaction_added", transaction)


class Account(objects.Base, GObject.GObject):

    __tablename__ = 'account'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    type = Column(Integer, default=1)
    balance = Column(Float, default=0.0)
    transactions = relationship('AccountTransaction', backref='account', cascade="all,delete")

    __gsignals__ = {
        'balance_changed': (GObject.SIGNAL_RUN_LAST, None,
                      (float,)),
        'transaction_added': (GObject.SIGNAL_RUN_LAST, None,
                      (object,))
    }

    def __init__(self, *args, **kwargs):
        GObject.GObject.__init__(self)
        objects.Base.__init__(self, *args, **kwargs)

    @reconstructor
    def _init(self):
        GObject.GObject.__init__(self)

    def __iter__(self):
        return self.transactions.__iter__()

    def __repr__(self):
        return "Account<%s>" % self.name

    def on_balance_changed(self, val, old_val, initiator):
        self.emit("balance_changed", val)

    @property
    def birthday(self):
        if self.transactions:
            return min([t.date for t in self])
        else:
            return datetime.date.today()

    @property
    def lastday(self):
        if self.transactions:
            return max([t.date for t in self])

    def has_transaction(self, trans):
        return objects.session.query(AccountTransaction)\
                .filter_by(account=self, description=trans['description'], amount=trans['amount'], date=trans['date'])\
                .count() > 0


event.listen(Account.balance, 'set', Account.on_balance_changed)
GObject.type_register(Account)


class AccountCategory(objects.Base):

    __tablename__ = 'account_category'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    parent_id = Column(Integer, ForeignKey('account_category.id'))
    parent = relationship('AccountCategory', remote_side=[id], backref='children')

    def __repr__(self):
        return "AccountCategory<%s>" % self.name

    def __str__(self):
        return self.name

    def get_parent_categories(self):
        ret = []
        current = self
        while current.parent:
            p = current.parent
            ret.append(p)
            current = p
        return ret


def get_all_categories():
    return objects.session.query(AccountCategory)\
            .order_by(AccountCategory.name).all()


def get_root_categories():
    return objects.session.query(AccountCategory)\
                     .filter_by(parent=None)\
                     .order_by(AccountCategory.name)\
                     .all()


class AccountTransaction(objects.Base):

    __tablename__ = 'account_transaction'

    id = Column(Integer, primary_key=True)
    description = Column(String)
    amount = Column(Float, default=0.0)
    date = Column(Date)
    account_id = Column(Integer, ForeignKey('account.id'))
    # just to prevent some warnings
    account = None
    transfer_id = Column(Integer, ForeignKey('account_transaction.id'))
    transfer = relationship('AccountTransaction', remote_side=[id], uselist=False, post_update=True)
    category_id = Column(Integer, ForeignKey('account_category.id'))
    category = relationship('AccountCategory', remote_side=[AccountCategory.id])

    def __init__(self, ** kwargs):
        objects.Base.__init__(self, **kwargs)
        # adjust balance of account
        self.account.balance += self.amount
        self.account.emit("transaction_added", self)

    def __repr__(self):
        return "AccountTransaction<%i> %s|%.2f" % (self.id, str(self.date), self.amount)

    def yield_matching_transfer_transactions(self):
        res = objects.session.query(AccountTransaction) \
                .filter(AccountTransaction.account != self.account,
                        AccountTransaction.amount == -self.amount,
                        or_(AccountTransaction.transfer == None,
                            AccountTransaction.transfer == self))
        fivedays = datetime.timedelta(5)
        for trans in res:
            if self.date - fivedays < trans.date and self.date + fivedays > trans.date:
                yield trans


class CategoryFilter(objects.Base):

    __tablename__ = 'category_filter'

    id = Column(Integer, primary_key=True)
    rule = Column(Unicode, default=u"")
    active = Column(Boolean, default=False)
    priority = Column(Integer, default=1)
    category_id = Column(Integer, ForeignKey('account_category.id'))
    category = relationship('AccountCategory', remote_side=[AccountCategory.id])

    def __repr__(self):
        return self.rule


def get_all_transactions():
    return objects.Session().query(AccountTransaction).all()


def yield_account_types():
    for type_id in sorted(TYPES.keys(), key=TYPES.get):
        yield type_id, TYPES[type_id]


def get_all_accounts():
    return objects.session.query(Account).all()
