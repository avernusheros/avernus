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
    
    def get_monthly_earnings(self, date):
        return self.get_transactions(date - datetime.timedelta(days=30), date)
    
    def get_monthly_spendings(self, date):
        return self.get_transactions(date - datetime.timedelta(days=30), 
                                 date, 
                                 earnings=False)


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
