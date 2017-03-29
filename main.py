from quantfund.quantfund import *
import tushare
import requests
import json


class QQDataSource(Source):
    def __init__(self):
        self.cached = {}

    def get_price(self, security, date):
        if isinstance(date, datetime.date):
            date = datetime.datetime.strptime(str(date), '%Y-%m-%d')
            date=date.strftime('%Y%m%d')
        else:
            date=date.replace('-','')

        if not security in self.cached:
            req = requests.get('http://stockjs.finance.qq.com/fundUnitNavAll/data/year_all/%s.js' % security)
            tmp = json.loads(req.text[19:])
            data = {}
            for d in tmp['data']:
                data[d[0]]=float(d[1])

            self.cached[security]=tmp
            self.cached[security]['data']=data

        if date in self.cached[security]['data']:
            return self.cached[security]['data'][date]
        else:
            return None


d = QQDataSource()

@strategy
class s1:
    def initialize(self):
        print 'init'

    def handle_data(self, ctx):
        ctx.order_value('510880', 10000)
        print ctx.portfolio.position_value, ctx.portfolio.available_cash
        print ctx.current_dt


run(200000, '2017-03-21', '2017-03-23', d)
