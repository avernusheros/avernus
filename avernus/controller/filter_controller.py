from avernus.objects.account import CategoryFilter
from avernus.objects import session
from avernus.config import avernusConfig
from avernus.controller import account_controller
import logging

from avernus.objects import session

logger = logging.getLogger(__name__)


def create(rule, category, priority=10, active=False):
    result = CategoryFilter(rule=rule, category=category, active=active, priority=priority)
    session.add(result)
    #update rule list
    #rules = get_all_active_by_priority()
    return result

def get_all_rules():
    return session.query(CategoryFilter).all()

def get_all_active_by_priority():
    return session.query(CategoryFilter).filter_by(active=True).order_by(CategoryFilter.priority).all()

def match_transaction(rule, transaction):
    #print rule.rule, transaction.description
    return rule.rule in transaction.description

def get_category(transaction):
    for rule in rules:
        #print "Probing rule ", rule, transaction.description
        if match_transaction(rule, transaction):
            return rule.category
    return None

def run_auto_assignments(*args):
    if config.get_option('assignments categorized transactions', 'Account') == 'True':
        b_include_categorized = True
    else:
        b_include_categorized = False
    transactions = account_controller.get_all_transactions()
    #print "Size: ", len(transactions)
    for transaction in transactions:
        if b_include_categorized or transaction.category is None:
            cat = get_category(transaction)
            msg = "Category Auto Assignment" + str(transaction) + ": "
            if cat != transaction.category:
                transaction.category = get_category(transaction)
                msg += "Change to " + str(transaction.category)
            else:
                msg += "No Change."
            logger.debug(msg)
            yield transaction

config = avernusConfig()
try:
    rules = get_all_active_by_priority()
except:
    logger.error("Category Auto Assignments: Error while retrieving rules")
    rules = []
