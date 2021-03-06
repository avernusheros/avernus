from avernus import objects
from avernus.config import avernusConfig
from avernus.objects import account
from avernus.objects.account import CategoryFilter
import logging


logger = logging.getLogger(__name__)


def get_all_rules():
    return objects.session.query(CategoryFilter).all()


def get_all_active_by_priority():
    return objects.Session().query(CategoryFilter).filter_by(active=True)\
                        .order_by(CategoryFilter.priority).all()


def match_transaction(rule, transaction):
    # print rule.rule, transaction.description
    return rule.rule in transaction.description


def get_category(transaction):
    for rule in rules:
        # print "Probing rule ", rule, transaction.description
        if match_transaction(rule, transaction):
            return rule.category
    return None


def apply_categorization_rules(*args):
    if config.get_option('assignments categorized transactions', 'Account') == 'True':
        b_include_categorized = True
    else:
        b_include_categorized = False
    global rules
    rules = get_all_active_by_priority()
    transactions = account.get_all_transactions()
    # print "Size: ", len(transactions)
    for transaction in transactions:
        if b_include_categorized or transaction.category is None:
            cat = get_category(transaction)
            if cat != transaction.category:
                transaction.category = get_category(transaction)
                logger.debug("Category assignment %s -> %s"
                              % (transaction, cat))
            yield transaction


config = avernusConfig()
rules = get_all_active_by_priority()
