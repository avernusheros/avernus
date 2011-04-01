from avernus.gui import gui_utils
from avernus import date_utils
from dateutil.relativedelta import relativedelta

def get_step_for_range(start,end):
    if start + relativedelta(months=+1) > end:
        #print "delta day"
        return relativedelta(days=1)
    if start + relativedelta(months=+10) > end:
        #print "delta week"
        return relativedelta(weeks=1)
    #print "delta month"
    return relativedelta(months=1)


class TransactionChartController:
    
    def __init__(self, transactions):
        self.transactions = sorted(transactions, key=lambda t: t.date)
        self.start_date = self.transactions[0].date
        self.end_date = self.transactions[-1].date
        #print "start, end ", self.start_date, self.end_date
        self.step = get_step_for_range(self.start_date, self.end_date)
        self.x_values = []
        current = self.start_date
        while current < self.end_date:
            self.x_values.append(current)
            current += self.step
        self.x_values.append(self.end_date)
        self.legend = [gui_utils.get_date_string(x) for x in self.x_values]

        
class TransactionValueOverTimeChartController(TransactionChartController):
    
    def __init__(self, transactions):
        TransactionChartController.__init__(self, transactions)
        self.y_values = []
        temp = {}
        i = 0
        x = self.x_values[i]
        temp[x] = 0
        for t in self.transactions:
            if t.date > x:
                i +=1
                x = self.x_values[i]
                temp[x] = temp[self.x_values[i-1]]
            temp[x] += t.amount
        for x in self.x_values:
            self.y_values.append(temp[x])


class DividendsPerYearChartController():
    
    def __init__(self, portfolio):
        data = {}
        for year in date_utils.get_years(portfolio.birthday):
            data[str(year)] = 0.0
        for pos in portfolio:
            for div in pos.dividends:
                data[str(div.date.year)]+=div.total
        self.x_values = sorted(data.keys())
        self.y_values = []
        for x_value in self.x_values:
            self.y_values.append([data[x_value]])


class DividendsPerPositionChartController():
    
    def __init__(self, portfolio):
        data = {}
        for pos in portfolio:
            for div in pos.dividends:
                try:
                    data[pos.name]+=div.total
                except:
                    data[pos.name]=div.total
        self.x_values = sorted(data.keys())
        self.y_values = []
        for x_value in self.x_values:
            self.y_values.append([data[x_value]])
