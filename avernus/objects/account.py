from avernus.objects.model import SQLiteEntity
from avernus import pubsub
import datetime
from dateutil.relativedelta import relativedelta


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
    
    def has_transaction(self, transaction):
        return self.controller.check_duplicate(AccountTransaction, account=self.id, **transaction)

    @property
    def transaction_count(self):
        count = 0
        for ta in self:
            count+=1
        return count

    def yield_matching_transfer_tranactions(self, transaction):
        for trans in self:
            if transaction.amount == -trans.amount:
                if trans.transfer is None or trans.transfer == transaction:
                    threedays = datetime.timedelta(3)
                    if transaction.date-threedays < trans.date and transaction.date+threedays > trans.date:
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

    def get_earnings_summed(self, end_date, start_date, period='month', transfers=False):
        return self._get_earnings_or_spendings_summed(start_date, end_date, period, earnings=True)
    
    def get_spendings_summed(self, end_date, start_date, period='month', transfers=False):
        return self._get_earnings_or_spendings_summed(start_date, end_date, period, earnings=False, transfers=False)

    def _get_earnings_or_spendings_summed(self, start_date, end_date, period='month', earnings=True, transfers=False):
        if period == 'month':
            delta = relativedelta(months=+1)
        elif period == 'year':
            delta = relativedelta(years=+1)
        elif period == 'day':
            delta = relativedelta(days=+1)
        elif period == 'week':
            delta = relativedelta(weeks=+1)
        ret = []
        while start_date < end_date:
            temp = start_date+delta
            ret.append(self.controller.getEarningsOrSpendingsSummedInPeriod(self, start_date, temp, earnings=earnings, transfers=transfers))
            start_date += delta
        return ret

    def birthday(self):
        if not 'birthday_cache' in dir(self):
            self.birthday_cache = None
        if self.birthday_cache:
            return self.birthday_cache
        else:
            birthday = datetime.date.today()
            for t in self:
                birthday = min(t.date, birthday)
            self.birthday_cache = birthday
            return birthday


class AccountCategory(SQLiteEntity):
    __primaryKey__ = 'id'
    __tableName__ = "accountcategory"
    __columns__ = {
                   'id': 'INTEGER',
                   'name': 'VARCHAR',
                   'parentid': 'INTEGER'
                  }

    def get_parent(self):
        if self.parentid != -1:
            return self.getByPrimaryKey(self.parentid)
        return None

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
    
    transfer = property(get_transfer, set_transfer)
