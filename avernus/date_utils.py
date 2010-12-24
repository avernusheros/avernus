import datetime

def get_ytd_first():
    year = datetime.date.today().year
    return datetime.date(day=1, month=1, year=year)

def get_act_first():
    td = datetime.date.today()
    return datetime.date(day=1, month=td.month, year=td.year)

def get_years(start_date, end_date=None):
    start = start_date.year
    end_date = end_date or datetime.date.today()
    end = end_date.year
    while start <= end:
        yield start
        start+=1
