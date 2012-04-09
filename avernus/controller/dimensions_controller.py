from avernus.objects import session
from avernus.objects.dimension import Dimension


def get_all_dimensions():
    res = session.query(Dimension).all()
    return res