from stocktracker.objects.model import SQLiteEntity
from stocktracker import pubsub
import controller
import datetime
from dateutil.relativedelta import relativedelta

class Account(SQLiteEntity):

    __primaryKey__ = 'id'
    __tableName__ = "account"
    __columns__ = {
                   'id': 'INTEGER',
                   'name': 'VARCHAR',
                   'type': 'INTEGER',
                   'amount': 'FLOAT'
                  }
                  
    def on_delete(self, **kwargs):
        controller.deleteAllAccountTransaction(self)
                  
    __callbacks__ = {
                     'onDelete':on_delete,
                    }
                  
    def __iter__(self):
        return controller.getTransactionsForAccount(self).__iter__()

    @property
    def transaction_count(self):
        count = 0
        for ta in self:
            count+=1
        return count

    def get_transactions_in_period(self, start_date, end_date):
        res = []
        for trans in self:
            if trans.date >= start_date and trans.date <= end_date:
                res.append(trans)
        return res

    def yield_earnings_in_period(self, start_date, end_date):
        for trans in self:
            if trans.date >= start_date and trans.date <= end_date and trans.amount >= 0.0:
                yield trans
    
    def yield_spendings_in_period(self, start_date, end_date):
        for trans in self:
            if trans.date >= start_date and trans.date <= end_date and trans.amount < 0.0:
                yield trans

    def get_balance_over_time(self, start_date):
        today = datetime.date.today()
        one_day = datetime.timedelta(days=1)
        amount = self.amount
        res = [(today, amount)]
        for change, date in controller.getAccountChangeInPeriodPerDay(self, start_date, today):
            #print date, change
            res.append((date, amount)) 
            amount -= change
        res.reverse()
        return res

    def get_sum_in_period_by_category(self, start_date, end_date, parent_category=None, b_earnings=False):
        #sum for all categories including subcategories
        if parent_category:
            parent_category_id = parent_category.id
        else:
            parent_category_id = None
        hierarchy = controller.getAllAccountCategoriesHierarchical()
        cat_ids = {}
        sums = {}
        
        def get_child_categories(parent):
            if parent.id in hierarchy:
                res = []
                for cat in hierarchy[parent.id]:
                    res.append(cat)
                    res += get_child_categories(cat)
                return res
            return []
        
        if parent_category_id in hierarchy:
            for cat in hierarchy[parent_category_id]:
                cat_ids[cat] = [cat] + get_child_categories(cat)
                sums[cat] = 0.0
        
        cat_ids['None'] = [parent_category]
        sums['None'] = 0.0

        for trans in self:
            if trans.isEarning() == b_earnings:
                for cat, subcats in cat_ids.items():
                    if trans.category in subcats:
                        sums[cat] += trans.amount
        return sums

    def get_earnings_summed(self, end_date, start_date, period='month'):
        return self._get_earnings_or_spendings_summed(start_date, end_date, period, earnings=True)
    
    def get_spendings_summed(self, end_date, start_date, period='month'):
        return self._get_earnings_or_spendings_summed(start_date, end_date, period, earnings=False)

    def _get_earnings_or_spendings_summed(self, start_date, end_date, period='month', earnings=True):
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
            ret.append(controller.getEarningsOrSpendingsSummedInPeriod(self, start_date, temp, earnings=earnings))
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
                   'parent': 'INTEGER'
                  }


class AccountTransaction(SQLiteEntity):
    __primaryKey__ = 'id'
    __tableName__ = "accounttransaction"
    __columns__ = {
                   'id': 'INTEGER',
                   'description': 'VARCHAR',
                   'amount': 'FLOAT',
                   'date' :'DATE',
                   'account': Account,
                   'category': AccountCategory
                  }
    __comparisonPositives__ = ['amount', 'date', 'description']

    def isEarning(self):
        return self.amount >= 0
