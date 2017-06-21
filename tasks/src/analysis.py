from functools import wraps

import datetime

from filters import Filters
# from sklearn.ensemble import GradientBoostingClassifier
from models import SymbolPrice, Message, db
from utils import MarketType


def get_percentage(count, total):
    try:
        return (float(count) / float(total)) * 100
    except ZeroDivisionError:
        return 0


def normalize_symbol(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        args = list(args)
        args[0] = args[0].upper()
        return f(*args, **kwargs)

    return wrapped


@normalize_symbol
def analyze_stock(symbol):
    base_query = Filters.Message.join_on_symbol()
    bearish_filter, bullish_filter, null_filter = Filters.Symbol.movement(symbol)
    bullish, bearish, nulled = [base_query.where(x).execute() for x in [bearish_filter, bullish_filter, null_filter]]
    print bullish.count, bearish.count, nulled.count


@normalize_symbol
def get_daily_percentage_on_stock(symbol):
    base_query = Filters.Message.join_on_symbol()
    bearish_filter, bullish_filter, null_filter = Filters.Symbol.movement(symbol)
    bullish, bearish, nulled = [base_query.where(x).where(Filters.Message.today()).execute() for x in
                                [bearish_filter, bullish_filter, null_filter]]
    total = bullish.count + bearish.count + nulled.count
    print "%s:\n%.2f%% (%s) Bull\n%.2f%% (%s) Bear\n%.2f%% (%s) Neutral\n" % (
        symbol, get_percentage(bullish.count, total),
        bullish.count,
        get_percentage(bearish.count, total),
        bearish.count,
        get_percentage(nulled.count, total),
        nulled.count)


@normalize_symbol
def get_symbol_direction(symbol, date=None):
    def get_sentiment(sp, ep):
        if sp > ep:
            sentiment = MarketType.bear
        elif sp < ep:
            sentiment = MarketType.bull
        else:
            sentiment = MarketType.neutral
        return sentiment

    base_query = Filters.SymbolPrice.join_on_symbol()
    symbol_query = base_query.where(Filters.Generic.symbol_is(symbol))
    if not date:
        today = Filters.SymbolPrice.today()
        prices = list(symbol_query.where(today).order_by(SymbolPrice.start_timestamp).execute())
    else:
        assert isinstance(date, datetime.date)
        prices = list(symbol_query.where(Filters.SymbolPrice.date_is(date)).order_by(SymbolPrice.start_timestamp).
                      execute())
    return get_sentiment(prices[0].close, prices[-1].close)


if __name__ == "__main__":
    symbols = ['nugt', 'jnug', 'dust', 'jdst']
    for symbol in symbols:
        print symbol
        # analyze_stock(symbol)
        # get_daily_percentage_on_stock(symbol)
        print get_symbol_direction(symbol)  # date=datetime.datetime.now().date())
