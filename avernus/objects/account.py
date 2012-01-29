from avernus import pubsub
from avernus.objects.model import SQLiteEntity
import datetime


class AccountBase():

    def __len__(self):
        return self.transaction_count

    def __iter__(self):
        return self.transactions.__iter__()

    def has_transaction(self, transaction):
        return self.controller.check_duplicate(AccountTransaction, account=self.id, **transaction)

    @property
    def transaction_count(self):
        return len(self.transactions)

    def yield_matching_transfer_transactions(self, transaction):
        for trans in self:
            if transaction.amount == -trans.amount:
                if trans.transfer is None or trans.transfer == transaction:
                    fivedays = datetime.timedelta(5)
                    if transaction.date-fivedays < trans.date and transaction.date+fivedays > trans.date:
                        yield trans

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




class Account(SQLiteEntity, AccountBase):

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

    @property
    def transactions(self):
        return self.controller.getTransactionsForAccount(self)



class AllAccount(AccountBase):
    name = ''
    id = -1
    __name__ = 'Account'

    @property
    def transactions(self):
        return self.controller.getAllAccountTransactions()

    @property
    def amount(self):
        return sum([acc.amount for acc in self.controller.getAllAccount()])


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

    def __str__(self):
        return self.name

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

    def on_update(self, **kwargs):
        pubsub.publish('accountTransaction.updated', self)

    __callbacks__ = {
                   'onUpdate':on_update,
                    }
    transfer = property(get_transfer, set_transfer)
