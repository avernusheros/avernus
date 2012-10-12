def xirr(transactions):
    """
    calculate the internal rate of return for a sequence of cash flows with
    dates
    the XIRR function chooses an initial guess of the interest rate,
    calculates the net present value, and iterates until the result is
    close enough
    """
    years = [(ta[0] - transactions[0][0]).days / 365.0 for ta in transactions]
    residual = 1
    step = 0.05
    guess = 0.05
    epsilon = 0.0001
    limit = 10000
    while abs(residual) > epsilon and limit > 0:
        limit -= 1
        residual = 0.0
        for i, ta in enumerate(transactions):
            try:
                residual += ta[1] / pow(guess, years[i])
            except:
                # catch div by zero
                return 0.0
        if abs(residual) > epsilon:
            if residual > 0:
                guess += step
            else:
                guess -= step
                step /= 2.0
    return guess - 1


if __name__ == "__main__":
    from datetime import date
    tas = [(date(2010, 12, 29), -10000), (date(2012, 1, 25), 20),
            (date(2012, 3, 8), 10100)]
    #0.0100612640381
    print xirr(tas)

    tas = [(date(2010, 12, 29), -879.6), (date(2012, 1, 25), 32.31),
            (date(2012, 3, 8), 240.0)]
    print xirr(tas)

    tas = [(date(2011, 6, 27), 2554.57), (date(2012, 1, 25), 47.44),
           (date(2012, 7, 11), 42.82), (date(2012, 10, 2), 2719.85)]
    print xirr(tas)
