from stocktracker.objects.model import SQLiteEntity
import controller
import datetime

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

    def get_earnings(self, date, month=1):
        return self.get_transactions(date - datetime.timedelta(days=30*month),
                                date)

    def get_spendings(self, date, month=1):
        return self.get_transactions(date - datetime.timedelta(days=30*month),
                                 date,
                                 earnings=False)

    def get_all_earnings(self):
        return [t for t in self if t.isEarning()]

    def get_all_spendings(self):
        return [t for t in self if t.isSpending()]

    def birthday(self):
        if not 'birthday_cache' in dir(self):
            self.birthday_cache = None
        if self.birthday_cache:
            return self.birthday_cache
        else:
            birthday = datetime.today()
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
