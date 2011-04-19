'''
Created on 18.04.2011

@author: bastian
'''
from avernus.objects.filter import CategoryFilter


def create(rule, category, priority = 10, active = False):
    result = CategoryFilter(rule=rule, category=category, active=active, priority=priority)
    result.insert()
    return result
    
def get_all():
    return CategoryFilter.getAll()
