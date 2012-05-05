from avernus.config import avernusConfig
from avernus.objects import session, Session
from avernus.objects.account import *
from sqlalchemy import or_
import datetime


#FIXME decide where to put this object
class AllAccount():

    def __iter__(self):
        return self.transactions.__iter__()

    @property
    def transactions(self):
        return get_all_transactions()

    @property
    def balance(self):
        return sum([acc.balance for acc in get_all_account()])


def get_all_account():
    return session.query(Account).all()

def get_all_transactions():
    return Session().query(AccountTransaction).all()

def new_account(name):
    account = Account(name)
    session.add(account)
    session.commit()
    return account

def new_account_category(name, parent=None):
    cat = AccountCategory(name, parent)
    session.add(cat)
    return cat

def new_account_transaction(desc="", account=None, amount=0.0, date=datetime.date.today()):
    transaction = AccountTransaction(description = desc, account = account, amount=amount, date=date)
    session.add(transaction)
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

def get_all_categories():
    return session.query(AccountCategory).all()

def get_root_categories():
    return session.query(AccountCategory).filter_by(parent=None).all()

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

# Mordor from here

class AccountController:

    def __init__(self, account):
        self.account = account

    def get_transactions_by_category(self, category, base=None):
        if not base:
            base = self.account
        result = []
        config = avernusConfig()
        pre = config.get_option('categoryChildren', 'Account')
        pre = pre == "True"
        for trans in [t for t in base if not t.category == None]:
            if trans.category == category or \
            (pre and trans.category.is_parent(category)):
                    result.append(trans)
        return result

    def get_transactions_in_period(self, start_date, end_date, transfers=False, base=None):
        res = []
        if not base:
            base = self.account
        for trans in base:
            if trans.date >= start_date and trans.date <= end_date:
                res.append(trans)
        return res

    def get_transactions_by_period_category(self, start_date, end_date, category):
        result = self.get_transactions_in_period(start_date, end_date)
        result = self.get_transactions_by_category(category, result)
        return result
