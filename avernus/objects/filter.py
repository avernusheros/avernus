from avernus.objects.account import AccountCategory
from avernus.objects.model import SQLiteEntity

class CategoryFilter(SQLiteEntity):
    
    __primaryKey__ = 'id'
    __tableName__ = "transactionFilter"
    __columns__ = {
                   'id': 'INTEGER',
                   'rule': 'VARCHAR',
                   'active': 'BOOLEAN',
                   'priority': 'INTEGER',
                   'category': AccountCategory
                  }    
    __comparisonPositives__ = ['rule']
