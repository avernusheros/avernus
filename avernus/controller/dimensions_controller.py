from avernus.objects import session
from avernus.objects.dimension import Dimension


def new_dimension(name):
    d = Dimension(name=name)
    session.add(d)
    return d
    
def new_dimension_value(*args, **kwargs):
    print "TODO"

        
def get_all_dimensions():
    res = session.query(Dimension).all()
    return res

