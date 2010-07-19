from stocktracker.objects.model import SQLiteEntity
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

    def __iter__(self):
        return controller.getTransactionsForAccount(self).__iter__()

    def get_transactions(self, fromDate, toDate, earnings=True):
        return controller.getPeriodTransactionsForAccount(self, fromDate, toDate, earnings)

    def get_earnings(self, end_date, start_date, period='month'):
        return self._get_earnings_or_spendings(end_date, start_date, period, earnings=True)
    
    def get_spendings(self, end_date, start_date, period='month'):
        return self._get_earnings_or_spendings(end_date, start_date, period, earnings=False)

    def _get_earnings_or_spendings(self, end_date, start_date, period='month', earnings=True):
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
            ret.append(controller.getEarningsOrSpendingsSummedInPeriod(self, temp, start_date, earnings=earnings))
            start_date += delta
        print ret
        return ret
                
    def get_all_earnings(self, period):
        return controller.getEarningsOrSpendingsSummed(self, period, earnings = True)

    def get_all_spendings(self, period):
        return controller.getEarningsOrSpendingsSummed(self, period, earnings = False)

    def get_ytd_earnings(self):
        return self.get_transactions(controller.get_ytd_first(), datetime.date.today())

    def get_ytd_spendings(self):
        return self.get_transactions(controller.get_ytd_first(), datetime.date.today(), earnings=False)

    def get_act_earnings(self):
        return self.get_transactions(controller.get_act_first(), datetime.date.today())

    def get_act_spendings(self):
        return self.get_transactions(controller.get_act_first(), datetime.date.today(), earnings=False)

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
                   'name': 'VARCHAR'
                  }


class AccountTransaction(SQLiteEntity):
    __primaryKey__ = 'id'
    __tableName__ = "accounttransaction"
    __columns__ = {
                   'id': 'INTEGER',
                   'description': 'VARCHAR',
                   'type': 'INTEGER',
                   'amount': 'FLOAT',
                   'date' :'DATE',
                   'account': Account,
                   'category': AccountCategory
                  }

    def isEarning(self):
        return self.amount >= 0
