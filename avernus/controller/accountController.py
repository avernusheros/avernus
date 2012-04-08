from avernus.config import avernusConfig
from avernus.objects import session
from avernus.objects.account import *

def get_all_account():
    res = session.query(Account).all()
    return res

def new_account(name):
    account = Account(name)
    session.add(account)
    session.commit()
    return account

def new_account_category(name, parent=None):
    cat = AccountCategory(name, parent)
    session.add(cat)
    return cat

def new_account_transaction(desc):
    transaction = AccountTransaction(desc)
    session.add(transaction)
    return transaction

def account_has_transaction(account, trans):
    return session.query(AccountTransaction).filter_by(account=account, description=trans['description'], amount=trans['amount'], date=trans['date']).count() > 0

def account_birthday(account):
    transactions = session.query(AccountTransaction).filter_by(account=account)
    if transactions.count() > 0:
        return transactions.order_by(AccountTransaction.date).first().date

def account_lastday(account):
    transactions = session.query(AccountTransaction).filter_by(account=account)
    if transactions.count() > 0:
        return transactions.order_by(AccountTransaction.date.desc()).first().date

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
