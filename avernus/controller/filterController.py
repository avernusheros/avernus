from avernus.objects.filter import CategoryFilter
from avernus.controller import controller

def create(rule, category, priority = 10, active = False):
    result = CategoryFilter(rule=rule, category=category, active=active, priority=priority)
    result.insert()
    return result

def get_all():
    return CategoryFilter.getAll()

def match_transaction(filter, transaction):
    return filter.rule in transaction.description

def get_category(transaction):
    #FIXME process filter by priority
    for filter in get_all():
        if match_transaction(filter, transaction):
            return filter.category
    return None

def run_auto_assignments():
    for transaction in controller.getAllAccountTransactions():
        if transaction.category is None:
            transaction.category = get_category(transaction)
