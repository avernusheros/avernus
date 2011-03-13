from avernus import pubsub
from avernus.objects.model import SQLiteEntity
from dateutil.rrule import *
import datetime
import calendar


class Account(SQLiteEntity):

    __primaryKey__ = 'id'
    __tableName__ = "account"
    __columns__ = {
                   'id': 'INTEGER',
                   'name': 'VARCHAR',
                   'type': 'INTEGER',
                   'amount': 'FLOAT',
                  }

    def on_delete(self, **kwargs):
        self.controller.deleteAllAccountTransaction(self)

    def on_update(self, **kwargs):
        pubsub.publish('account.updated', self)

    __callbacks__ = {
                     'onDelete':on_delete,
                     'onUpdate':on_update,
                    }

    def __iter__(self):
        return self.controller.getTransactionsForAccount(self).__iter__()

    def __len__(self):
        return self.transaction_count

    def has_transaction(self, transaction):
        return self.controller.check_duplicate(AccountTransaction, account=self.id, **transaction)

    @property
    def transaction_count(self):
        return len(self.controller.getTransactionsForAccount(self))

    def yield_matching_transfer_tranactions(self, transaction):
        for trans in self:
            if transaction.amount == -trans.amount:
                if trans.transfer is None or trans.transfer == transaction:
                    fivedays = datetime.timedelta(5)
                    if transaction.date-fivedays < trans.date and transaction.date+fivedays > trans.date:
                        yield trans

    def get_transactions_in_period(self, start_date, end_date, transfers=False):
        res = []
        for trans in self:
            if trans.date >= start_date and trans.date <= end_date:
                res.append(trans)
        return res

    def yield_earnings_in_period(self, start_date, end_date, transfers=False):
        for trans in self:
            if transfers or trans.transfer is None:
                if trans.date >= start_date and trans.date <= end_date and trans.amount >= 0.0:
                    yield trans

    def yield_spendings_in_period(self, start_date, end_date, transfers=False):
        for trans in self:
            if transfers or trans.transfer is None:
                if trans.date >= start_date and trans.date <= end_date and trans.amount < 0.0:
                    yield trans

    def get_balance_over_time(self, start_date):
        today = datetime.date.today()
        one_day = datetime.timedelta(days=1)
        amount = self.amount
        res = [(today, amount)]
        for change, date in self.controller.getAccountChangeInPeriodPerDay(self, start_date, today):
            #print date, change
            res.append((date, amount))
            amount -= change
        res.reverse()
        return res

    def get_sum_in_period_by_category(self, start_date, end_date, parent_category=None, b_earnings=False, transfers=False):
        #sum for all categories including subcategories
        if parent_category:
            parent_category_id = parent_category.id
        else:
            parent_category_id = None
        hierarchy = self.controller.getAllAccountCategoriesHierarchical()
        cats = {}
        sums = {}

        def get_child_categories(parent):
            if parent in hierarchy:
                res = []
                for cat in hierarchy[parent]:
                    res.append(cat)
                    res += get_child_categories(cat)
                return res
            return []

        if parent_category in hierarchy:
            for cat in hierarchy[parent_category]:
                cats[cat] = [cat] + get_child_categories(cat)
                sums[cat] = 0.0

        cats['None'] = [parent_category]
        sums['None'] = 0.0

        for trans in self:
            if transfers or trans.transfer is None:
                if trans.isEarning() == b_earnings:
                    for cat, subcats in cats.items():
                        if trans.category in subcats:
                            sums[cat] += trans.amount
        return sums

    def get_earnings_summed(self, end_date, start_date, period='monthly', transfers=False):
        return self._get_earnings_or_spendings_summed(start_date, end_date, period, earnings=True)

    def get_spendings_summed(self, end_date, start_date, period='monthly', transfers=False):
        return self._get_earnings_or_spendings_summed(start_date, end_date, period, earnings=False, transfers=False)

    def _get_earnings_or_spendings_summed(self, start_date, end_date, period='monthly', earnings=True, transfers=False):
        if period == 'monthly':
            #last day of month
            days = list(rrule(MONTHLY, dtstart = start_date, until = end_date, bymonthday=-1))
        elif period == 'yearly':
            days = list(rrule(YEARLY, dtstart = start_date, until = end_date, bymonthday=-1, bymonth=12))
        elif period == 'daily':
            days = list(rrule(DAILY, dtstart = start_date, until = end_date))
        elif period == 'weekly':
            days = list(rrule(WEEKLY, dtstart = start_date, until = end_date, byweekday=SU))
        ret = []
        for day in days+[end_date]:
            ret.append(self.controller.getEarningsOrSpendingsSummedInPeriod(self, start_date, day, earnings=earnings, transfers=transfers))
            start_date = day
        return ret

    @property
    def birthday(self):
        if self.transaction_count>0:
            return min(t.date for t in self)
        return datetime.date.today()

    @property
    def lastday(self):
        if self.transaction_count>0:
            return max(t.date for t in self)
        return datetime.date.today()


class AccountCategory(SQLiteEntity):
    __primaryKey__ = 'id'
    __tableName__ = "accountcategory"
    __columns__ = {
                   'id': 'INTEGER',
                   'name': 'VARCHAR',
                   'parentid': 'INTEGER'
                  }

    def __cmp__(self, other):
        if other is None:
            return 1
        return cmp(self.name,other.name)

    def __repr__(self):
        return SQLiteEntity.__repr__(self) + self.name

    def get_parent(self):
        if self.parentid != -1:
            return self.getByPrimaryKey(self.parentid)
        return None

    def get_parents(self):
        erg = []
        current = self
        while not current.parentid == -1:
            p = current.get_parent()
            erg.append(p)
            current = p
        return erg

    parents = property(get_parents)

    def set_parent(self, parent):
        if parent:
            self.parentid = parent.id
        else:
            self.parentid = -1

    parent = property(get_parent, set_parent)

    def is_parent(self, category):
        if category == self:
            return True
        if self.parent == category:
            return True
        if self.parent is not None:
            return self.parent.is_parent(category)
        return False


class AccountTransaction(SQLiteEntity):
    __primaryKey__ = 'id'
    __tableName__ = "accounttransaction"
    __columns__ = {
                   'id': 'INTEGER',
                   'description': 'VARCHAR',
                   'amount': 'FLOAT',
                   'date' :'DATE',
                   'account': Account,
                   'category': AccountCategory,
                   'transferid': 'INTEGER'
                  }
    __comparisonPositives__ = ['amount', 'date', 'account']

    def isEarning(self):
        return self.amount >= 0

    def get_transfer(self):
        if self.transferid != -1:
            return self.getByPrimaryKey(self.transferid)
        return None

    def set_transfer(self, transaction):
        if transaction:
            self.transferid = transaction.id
        else:
            self.transferid = -1

    def is_transfer(self):
        return (self.transfer is not None)

    def has_category(self):
        return (self.category is not None)

    transfer = property(get_transfer, set_transfer)
