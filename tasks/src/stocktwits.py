import urllib
import re
from functools import wraps

import requests
from models import Symbol, SymbolPrice, User, Message, db
import peewee

requests.packages.urllib3.disable_warnings()


class Source(object):
    def __init__(self):
        self.__url = None
        self.__parameters = {}

    @property
    def url(self):
        return self.__url

    @url.setter
    def url(self, url_):
        self.__url = url_
        self.__parameters = {}

    @property
    def parameters(self):
        return urllib.urlencode(self.__parameters)

    def update_parameters(self, params):
        assert isinstance(params, dict)
        self.__parameters.update(params)

    def get_data(self, headers=None):
        assert self.__url
        url = self.url
        if self.parameters:
            url = url + '?' + self.parameters
        if headers:
            assert isinstance(headers, dict)
            req = requests.get(url, headers=headers, verify=False)
        else:
            req = requests.get(url, verify=False)
        assert req.status_code == 200
        content_type = req.headers.get('Content-Type', "")
        if 'application/json' in content_type:
            return req.json()
        return req.content


class StockTwitFeed(Source):
    def __init__(self, symbol):
        super(StockTwitFeed, self).__init__()
        self.symbol = symbol
        self.item_id = None
        self.stream_id = None

    def get_feed_parameters(self):
        self.url = "https://stocktwits.com/symbol/%s" % self.symbol.upper()
        data = self.get_data()
        token_match = re.findall("csrf-token\"\scontent=\"(.*?)\"", data)
        csrf_token = token_match[0]
        id_match = re.findall("StreamHistory.init\(\'symbol\', \'(.*?)\'", data)
        if not id_match:
            raise ValueError("Stock symbol does not exist: %s" % self.symbol.upper())
        stock_id = id_match[0]
        self.item_id = self.stream_id = stock_id
        return csrf_token, stock_id

    def retrieve_messages(self):
        csrf_token, stock_id = self.get_feed_parameters()
        self.url = 'https://stocktwits.com/streams/poll'
        self.update_parameters(
            {'stream': 'symbol', 'blocking': '0', 'signed_in': '0', 'substream': 'top',
             'stream_id': stock_id, 'item_id': stock_id})
        results = self.get_data(headers={'X-CSRF-Token': csrf_token,
                                         'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ("
                                                       "KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
                                         'X-Requested-With': 'XMLHttpRequest'})
        assert isinstance(results, dict)
        return results.get('messages')


class StockTwitIntraday(Source):
    def __init__(self, symbol):
        super(StockTwitIntraday, self).__init__()
        self.symbol = symbol

    def get_intraday_trades(self):
        self.url = "https://ql.stocktwits.com/intraday"
        self.update_parameters({'symbol': self.symbol})
        results = self.get_data(headers={
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ("
                          "KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
        })
        return results


def db_transaction(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        db.connect()
        with db.transaction():
            results = f(*args, **kwargs)
        db.close()
        return results
    return wrapped


@db_transaction
def insert_messages(symbol, messages, item_id, stream_id):
    symbol = symbol.upper()
    symbol_dict = dict(name=symbol, stream_id=stream_id, item_id=item_id)
    try:
        symbol_obj = Symbol.create(**symbol_dict)
    except peewee.IntegrityError:
        symbol_obj = Symbol.get(name=symbol)

    for message in messages:
        with db.atomic():
            user_dict = dict(id=message['user'].get('id'), username=message['user'].get('username'),
                             name=message['user'].get('name'))
            try:
                user_obj = User.create(**user_dict)
            except peewee.IntegrityError:
                user_obj = User.get(id=user_dict.get('id'))

            sentiment = message.get('sentiment')
            if sentiment:
                sentiment = sentiment.get('class')
            message_dict = dict(body=message.get('body'), timestamp=message.get('created_at'), sentiment=sentiment,
                                symbol=symbol_obj, user=user_obj, st_id=message.get('id'))
            try:
                message_obj = Message.get(st_id=message.get('id'))
            except Message.DoesNotExist:
                message_obj = Message.create(**message_dict)
            message_obj.reshares = message.get('total_reshares')
            message_obj.likes = message.get('total_likes')
            message_obj.save()


@db_transaction
def insert_intraday_trades(symbol, intraday_trades):
    symbol = symbol.upper()
    symbol_obj = Symbol.get(name=symbol)
    for intraday_trade in intraday_trades:
        it_dict = dict(symbol=symbol_obj, start_date=intraday_trade.get('StartDate'),
                       end_date=intraday_trade.get('EndDate'),
                       start_time=intraday_trade.get('StartTime'), end_time=intraday_trade.get('EndTime'),
                       trades=intraday_trade.get('Trades'),
                       volume=intraday_trade.get('Volume'), utc_offset=intraday_trade.get('UTCOffset'),
                       low=intraday_trade.get('Low'),
                       open=intraday_trade.get('Open'), close=intraday_trade.get('Close'),
                       high=intraday_trade.get('High'),
                       twap=intraday_trade.get('TWAP'), vwap=intraday_trade.get('VWAP'))
        try:
            symbol_price_obj = SymbolPrice.create(**it_dict)
        except peewee.IntegrityError:
            pass
            # symbol_price_obj = SymbolPrice.get(symbol=symbol_obj, start_date=intraday_trade.get('StartDate'),
            #                                    end_date=intraday_trade.get('EndDate'),
            #                                    start_time=intraday_trade.get('StartTime'),
            #                                    end_time=intraday_trade.get('EndTime'))


if __name__ == '__main__':
    symbols = ['nugt', 'jnug', 'dust', 'jdst', 'oil', 'uso']
    for stock_symbol in symbols:
        st = StockTwitFeed(symbol=stock_symbol)
        msgs = st.retrieve_messages()
        insert_messages(stock_symbol, msgs, st.item_id, st.stream_id)

        st_prices = StockTwitIntraday(symbol=stock_symbol)
        trades = st_prices.get_intraday_trades()
        insert_intraday_trades(stock_symbol, trades)
