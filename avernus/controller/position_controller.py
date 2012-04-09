from avernus.objects.container import PortfolioPosition
from avernus.objects import session



def new_portfolio_position(price, date, shares, portfolio, stock):
    position = PortfolioPosition()
    position.price = price
    position.date = date
    position.quantity = shares
    position.portfolio = portfolio
    position.stock = stock
    session.add(position)
    return position

def get_buy_value(position):
    return position.quantity * position.price

def get_current_value(position):
    return position.quantity * position.stock.price

def get_current_change(position):
    return position.stock.change, position.stock.percent
