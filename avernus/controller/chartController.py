from avernus.gui import gui_utils
from avernus import date_utils
from dateutil.relativedelta import relativedelta
import datetime

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

    def calculate_x_values(self):
        self.end_date = datetime.date.today()
        self.step = get_step_for_range(self.start_date, self.end_date)
        self.x_values_all = []
        current = self.start_date
        while current < self.end_date:
            self.x_values_all.append(current)
            current += self.step
        self.x_values_all.append(self.end_date)
        self.x_values = [gui_utils.get_date_string(x) for x in self.x_values_all]


class TransactionValueOverTimeChartController(TransactionChartController):

    def __init__(self, transactions, start_date):
        self.transactions = sorted(transactions, key=lambda t: t.date)
        self.start_date = start_date
        self.calculate_values()
        
    def calculate_values(self):
        self.calculate_x_values()
        
        self.y_values = []
        #FIXME do we need this temp dict?
        temp = {}
        i = 0
        x = self.x_values_all[i]
        temp[x] = 0
        for t in self.transactions:
            if t.date > x:
                i +=1
                x = self.x_values_all[i]
                temp[x] = temp[self.x_values_all[i-1]]
            temp[x] += t.amount
        if len(self.x_values_all) > len(temp):
            print "more x than y, defaulting to the value of the last"
            for x in self.x_values_all:
                if not x in temp:
                    print "X: ", x, " index ", self.x_values_all.index(x)
                    temp[x] = temp[self.x_values_all[self.x_values_all.index(x)-1]]
        for x in self.x_values_all:
            value = x
            self.y_values.append(temp[value])


class AccountBalanceOverTimeChartController(TransactionChartController):

    def __init__(self, transactions, start_date):
        self.transactions = sorted(transactions, key=lambda t: t.date, reverse=True)
        self.start_date = start_date
        self.account = transactions[0].account
        self.calculate_values()

    def calculate_values(self):
        self.calculate_x_values()
        
        count = 1
        trans_count = len(self.transactions)
        iterator = self.transactions.__iter__()
        current_trans = iterator.next()
        amount = self.account.amount
        self.y_values = []
        for current_date in reversed(self.x_values_all):
            while current_trans.date > current_date and count != trans_count:
                amount -= current_trans.amount
                current_trans = iterator.next()
                count += 1
            self.y_values.append(amount)
        self.y_values.reverse()     
        

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


class StockChartPlotController():
    
    def __init__(self, quotations):
        self.y_values = [d.close for d in quotations]
        quotation_count = len(quotations)
        self.x_values = [gui_utils.get_date_string(quotations[int(quotation_count/18 *i)].date) for i in range(18)]
        self.x_values.insert(0,str(quotations[0].date))
        self.x_values.insert(len(self.x_values),str(quotations[-1].date))
