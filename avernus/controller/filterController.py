'''
Created on 18.04.2011

@author: bastian
'''
from avernus.objects.filter import CategoryFilter
import re


def create(rule, category, priority = 10, active = False):
    result = CategoryFilter(rule=rule, category=category, active=active, priority=priority)
    result.insert()
    return result
    
def get_all():
    return CategoryFilter.getAll()

class FilterController:
    
    def __init__(self, filter):
        self.filter = filter
        self.regex = re.compile(filter.rule)
        
    def match_transaction(self, transaction):
        #print self.filter, " ?matches? ", transaction
        desc = transaction.description
        match = self.regex.search(desc)
        if match:
            return True
        return False
