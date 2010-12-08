import datetime

def get_ytd_first():
    year = datetime.date.today().year
    return datetime.date(day=1, month=1, year=year)

def get_act_first():
    td = datetime.date.today()
    return datetime.date(day=1, month=td.month, year=td.year)
