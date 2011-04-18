'''
Created on 18.04.2011

@author: bastian
'''
from avernus.objects.filter import CategoryFilter


def create(rule, category, active = False):
    result = CategoryFilter(rule=rule, category=category, active=active)
    result.insert()
    return result