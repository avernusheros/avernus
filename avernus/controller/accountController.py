from avernus.config import avernusConfig
from avernus.objects import session
from avernus.objects.account import Account

def get_all_account():
    res = session.query(Account).all()
    return res

def new_account(name):
    account = Account(name)
    session.add(account)
    session.commit()
    return account

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
