from avernus.objects.filter import CategoryFilter


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
    for filter in CategoryFilter.getAll():
        if match_transaction(filter, transaction):
            return filter.category
    return None
