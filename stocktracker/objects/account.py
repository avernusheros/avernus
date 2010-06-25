from stocktracker.objects.model import SQLiteEntity

class Account(SQLiteEntity):

    __primaryKey__ = 'id'
    __tableName__ = "account"
    __columns__ = {
                   'id': 'INTEGER',
                   'name': 'VARCHAR',
                   'type': 'INTEGER',
                   'amount': 'FLOAT'                   
                  }


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
                   'date' :'TIMESTAMP',
                   'account': Account,
                   'category': AccountCategory                   
                  }
