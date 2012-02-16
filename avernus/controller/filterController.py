from avernus.objects.filter import CategoryFilter
from avernus.controller import controller
from avernus.config import avernusConfig


def create(rule, category, priority=10, active=False):
    result = CategoryFilter(rule=rule, category=category, active=active, priority=priority)
    result.insert()
    #update rule list
    rules = get_all_active_by_priority()
    return result


def get_all():
    return CategoryFilter.getAll()


def get_all_active_by_priority():
    return sorted([f for f in get_all() if f.active], key=lambda f: f.priority)

def match_transaction(rule, transaction):
    return rule.rule in transaction.description

def get_category(transaction):
    for rule in rules:
        if match_transaction(rule, transaction):
            return rule.category
    return None

def run_auto_assignments():
    if config.get_option('assignments categorized transactions', 'Account') == 'True':
        b_include_categorized = True
    else:
        b_include_categorized = False
    for transaction in controller.getAllAccountTransactions():
        if b_include_categorized or transaction.category is None:
            cat = get_category(transaction)
            if cat != transaction.category:
                transaction.category = get_category(transaction)
    print "finished"

config = avernusConfig()
try:
    rules = get_all_active_by_priority()
except:
    rules = []

