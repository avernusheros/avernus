import datetime
from gi.repository import GObject

from avernus.objects import session, Session
from avernus.objects import TYPES
from avernus.objects import Account, AccountTransaction, AccountCategory
from sqlalchemy import or_


class AllAccount(GObject.GObject):

    __gsignals__ = {
        'balance_changed': (GObject.SIGNAL_RUN_LAST, None,
                      (float,)),
        'transaction_added': (GObject.SIGNAL_RUN_LAST, None,
                      (object,))
    }

    def __init__(self):
        GObject.GObject.__init__(self)
        for acc in get_all_account():
            acc.connect("balance_changed", self.on_balance_changed)
            acc.connect("transaction_added", self.on_transaction_added)

    def __iter__(self):
        return self.transactions.__iter__()

    @property
    def transactions(self):
        return get_all_transactions()

    @property
    def balance(self):
        return sum([acc.balance for acc in get_all_account()])

    def on_balance_changed(self, *args):
        self.emit("balance_changed", self.balance)

    def on_transaction_added(self, account, transaction):
        self.emit("transaction_added", transaction)

def get_all_account():
    return session.query(Account).all()

def get_all_transactions():
    return Session().query(AccountTransaction).all()

def new_account(name):
    account = Account(name=name)
    session.add(account)
    session.commit()
    return account

def new_account_category(name, parent=None):
    cat = AccountCategory(name=name, parent=parent)
    session.add(cat)
    return cat

def new_account_transaction(desc="", account=None, amount=0.0, date=datetime.date.today(), category=None):
    transaction = AccountTransaction(description = desc, account = account, amount=amount, date=date, category=category)
    session.add(transaction)
    #adjust balance of account
    account.balance += amount
    account.emit("transaction_added", transaction)
    return transaction

def account_has_transaction(account, trans):
    return session.query(AccountTransaction).filter_by(account=account, description=trans['description'], amount=trans['amount'], date=trans['date']).count() > 0

def account_birthday(account):
    if len(account.transactions) > 0:
        return min([t.date for t in account])
    else:
        return datetime.date.today()

def account_lastday(account):
    if len(account.transactions) > 0:
        return max([t.date for t in account])

def yield_account_types():
    for type_id in sorted(TYPES.keys(), key=TYPES.get):
        yield type_id, TYPES[type_id]

def get_all_categories():
    return session.query(AccountCategory).order_by(AccountCategory.name).all()

def get_root_categories():
    return session.query(AccountCategory).filter_by(parent=None).order_by(AccountCategory.name).all()

def get_parent_categories(category):
    ret = []
    current = category
    while current.parent:
        p = current.parent
        ret.append(p)
        current = p
    return ret

def yield_matching_transfer_transactions(transaction):
    res = session.query(AccountTransaction) \
            .filter(AccountTransaction.account!=transaction.account,
                    AccountTransaction.amount == -transaction.amount,
                    or_(AccountTransaction.transfer == None,
                        AccountTransaction.transfer == transaction))
    #FIXME maybe do this directly in sqlalchemy
    fivedays = datetime.timedelta(5)
    for trans in res:
        if transaction.date-fivedays < trans.date and transaction.date+fivedays > trans.date:
            yield trans
