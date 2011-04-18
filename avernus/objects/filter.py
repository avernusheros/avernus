'''
Created on 18.04.2011

@author: bastian
'''
from avernus.objects.account import AccountCategory
from avernus.objects.model import SQLiteEntity

class CategoryFilter(SQLiteEntity):
    
    __primaryKey__ = 'rule'
    __tableName__ = "categoryFilter"
    __columns__ = {
                   'rule': 'VARCHAR',
                   'active': 'BOOLEAN',
                   'priority': 'INTEGER',
                   'category': AccountCategory
                  }    