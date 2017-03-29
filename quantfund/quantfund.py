import datetime
import logging
import math


class Source(object):
    def get_price(self, security, date):
        pass


class RunParams(object):
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date


class Position(object):
    def __init__(self, security,
                 total_amount):
        self.security = security
        self.total_amount = total_amount


class Portfolio(object):
    def __init__(self, inout_cash,
                 available_cash,
                 total_value,
                 returns,
                 position_value):
        self.inout_cash = inout_cash
        self.available_cash = available_cash
        self.positions = []
        self.total_value = total_value
        self.returns = returns
        self.position_value = position_value

    def update_position(self, security, amount):
        '''
        :param security:
        :param amount:
        :return: real amount changed
        '''

        # find position of security
        for p in self.positions:
            if p.security == security:
                # if not enough amount
                if amount + p.total_amount < 0:
                    logging.error('failed operation: not enough amount in position %s' % security)
                    return p.total_amount
                else:
                    p.total_amount += amount
                    return amount

        # if no this security yet
        # add it
        if amount < 0:
            logging.error('failed operation: not enough amount in position %s' % security)
            return 0
        else:
            p = Position(security, amount)
            self.positions.append(p)
            return amount

    def get_position(self, security):
        '''
        :param security:
        :return: return Position if found, otherwise None is return
        '''
        for p in self.positions:
            if p.security == security:
                return p
        return None


class Context(object):
    def __init__(self, starting_cash, start_date, end_date, source):
        self._commision_rate = 0.001
        self._source = source
        self.portfolio = Portfolio(starting_cash, starting_cash, starting_cash, 0, 0)
        if not isinstance(start_date, datetime.date):
            start_date = datetime.datetime.strptime(str(start_date), '%Y-%m-%d')
        if not isinstance(end_date, datetime.date):
            end_date = datetime.datetime.strptime(str(end_date), '%Y-%m-%d')

        self.current_dt = start_date
        self.run_params = RunParams(start_date, end_date)

    def order(self, security, amount):
        price = self._source.get_price(security, self.current_dt)

        value = amount * price
        commision = value * self._commision_rate
        cost = value + commision

        if cost > self.portfolio.available_cash:
            real_amount = math.floor(self.portfolio.available_cash / (price * (1 + self._commision_rate)))
            logging.warn('Not enough money to buy. Required amount: %f, actual amount: %f' % (amount, real_amount))
            amount = real_amount

        amount = self.portfolio.update_position(security, amount)
        value = amount * price
        commision = value * self._commision_rate
        cost = value + commision
        self.portfolio.available_cash -= cost
        self.portfolio.position_value += value
        self.portfolio.total_value -= commision

    def order_value(self, security, value):
        price = self._source.get_price(security, self.current_dt)
        self.order(security, value / price)

    def order_target(self, security, amount):
        p = self.portfolio.get_position(security)
        if p:
            self.order(security, amount - p.total_amount)
        else:
            self.order(security, amount)

    def order_target_value(self, security, value):
        price = self._source.get_price(security, self.current_dt)
        self.order_target(security, value / price)


strategies = []


def strategy(cls):
    if not hasattr(cls, 'handle_data') or not hasattr(cls, 'initialize'):
        raise Exception("not a strategy")
    strategies.append(cls)
    return cls


def run(starting_cash, start_date, end_date, datasource):
    # convert date to datetime.datetime
    if not isinstance(start_date, datetime.date):
        start_date = datetime.datetime.strptime(str(start_date), '%Y-%m-%d')
        start_date = datetime.date(start_date.year, start_date.month, start_date.day)
    if not isinstance(end_date, datetime.date):
        end_date = datetime.datetime.strptime(str(end_date), '%Y-%m-%d')
        end_date = datetime.date(end_date.year, end_date.month, end_date.day)

    one_day = datetime.timedelta(days=1)

    # run each strategy
    for S in strategies:
        # create context
        ctx = Context(starting_cash, start_date, end_date, datasource)
        s = S()

        current_dt = start_date
        while current_dt <= end_date:
            ctx.current_dt = current_dt
            s.handle_data(ctx)
            current_dt += one_day
