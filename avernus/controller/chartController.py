'''
Created on 17.03.2011

@author: bastian
'''

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
        
class TransactionValueOverTimeChartController(TransactionChartController):
    
    def __init__(self, transactions):
        TransactionChartController.__init__(self, transactions)
        self.y_values = {}
        i = 0
        x = self.x_values[i]
        self.y_values[x] = 0
        for t in self.transactions:
            if t.date > x:
                i +=1
                x = self.x_values[i]
                self.y_values[x] = self.y_values[self.x_values[i-1]]
            self.y_values[x] += t.amount