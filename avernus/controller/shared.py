def check_duplicate(tp, **kwargs):
    sqlArgs = {}
    for req in tp.__comparisonPositives__:
        sqlArgs[req] = kwargs[req]
    present = tp.getByColumns(sqlArgs, operator=" AND ", create=True)
    if present:
        return present[0]
    return None



def detect_duplicate(tp, **kwargs):
    #print tp, kwargs
    sqlArgs = {}
    for req in tp.__comparisonPositives__:
        sqlArgs[req] = kwargs[req]
    present = tp.getByColumns(sqlArgs, operator=" AND ", create=True)
    if present:
        return present[0]
    #print "not Present!"
    new = tp(**kwargs)
    new.insert()
    return new