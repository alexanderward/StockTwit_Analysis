from functools import wraps

import datetime

from export.CSV import CSV
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
def get_daily_percentage_on_stock(symbol):
    base_query = Filters.Message.join_on_symbol()
    bearish_filter, bullish_filter, neutral_filter = Filters.Symbol.movement(symbol)
    bullish, bearish, neutral = [base_query.where(x).where(Filters.Message.today()).execute() for x in
                                 [bearish_filter, bullish_filter, neutral_filter]]
    total = bullish.count + bearish.count + neutral.count

    return (get_percentage(bullish.count, total), bullish.count), \
           (get_percentage(bearish.count, total), bearish.count), \
           (get_percentage(neutral.count, total), neutral.count)


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
        date = Filters.SymbolPrice.today()
        yesterday = Filters.SymbolPrice.date_is(datetime.date.today() - datetime.timedelta(1))
    else:
        assert isinstance(date, datetime.date)
        yesterday = Filters.SymbolPrice.date_is(date - datetime.timedelta(1))

    yesterday_close = list(symbol_query.where(yesterday).order_by(SymbolPrice.start_timestamp).execute())
    prices = list(symbol_query.where(date).order_by(SymbolPrice.start_timestamp).execute())
    if prices:
        day_open = prices[0].close
        if yesterday_close:
            day_open = yesterday_close[-1].close

        return get_sentiment(day_open, prices[-1].close)
    return MarketType.neutral


@normalize_symbol
def get_user_accuracy_per_symbol(symbol, sentiment, date=None):
    bearish_filter, bullish_filter, neutral_filter = Filters.Symbol.movement(symbol)
    base_query = Filters.Message.join_on_symbol()
    if sentiment == MarketType.bear:
        market_type_filter = bearish_filter
    elif sentiment == MarketType.bull:
        market_type_filter = bullish_filter
    else:
        market_type_filter = neutral_filter
    # print base_query.where(market_type_filter).execute()
    print 'Incomplete - todo'


@normalize_symbol
def find_bull_run_times_of_day_for_symbol(symbol):
    pass


class Export(object):
    @staticmethod
    def high_and_lows(symbols, filename):
        csv = CSV()
        csv.headers = ['Date', 'Symbol', 'Direction', 'High Start', 'High End', 'Low Start', 'Low End', 'High - Price',
                       'Low - Price']
        start_date = SymbolPrice.select().order_by(SymbolPrice.start_timestamp.asc()).get().start_timestamp.date()
        for symbol_ in symbols:
            day_counter = 0
            while True:
                date = start_date + datetime.timedelta(day_counter)  # datetime.date.today()
                day_counter += 1
                if date.weekday() not in [5, 6]:
                    high, low = find_high_and_low_of_day_for_symbol(symbol_, date)

                    if not high or not low:
                        break
                    high_time_start = high[1].strftime('%H:%M:%S')
                    high_time_end = high[2].strftime('%H:%M:%S')
                    low_time_start = low[1].strftime('%H:%M:%S')
                    low_time_end = low[2].strftime('%H:%M:%S')
                    csv.add_row(
                        [date.strftime('%m/%d/%Y'), symbol_.upper(), get_symbol_direction(symbol_, date=date).value,
                         high_time_start, high_time_end, low_time_start, low_time_end, high[0], low[0]])
        csv.save(filename)


@normalize_symbol
def find_high_and_low_of_day_for_symbol(symbol, date=None):
    if not date:
        date = datetime.date.today()
    assert isinstance(date, datetime.date)
    base_query = Filters.SymbolPrice.join_on_symbol()
    symbol_prices = base_query.where(Filters.SymbolPrice.date_is(date)).where(Filters.Generic.symbol_is(symbol))

    high = [None, None, None]
    low = [None, None, None]
    for price in symbol_prices:
        if low[0] is None or price.low <= low[0]:
            low[0] = price.low
            low[1] = price.start_timestamp
            low[2] = price.end_timestamp
        if high[0] is None or price.high >= high[0]:
            high[0] = price.high
            high[1] = price.start_timestamp
            high[2] = price.end_timestamp
    if not high[0]:
        return None, None
    print 'Date: ', date.strftime('%m/%d/%Y')
    print 'Symbol: ', symbol
    print 'Direction: ', get_symbol_direction(symbol, date=date)
    print 'Low: ', low[0], '@: %s - %s' % (low[1].strftime('%H:%M:%S'), low[2].strftime('%H:%M:%S'))
    print 'High: ', high[0], '@: %s - %s' % (high[1].strftime('%H:%M:%S'), high[2].strftime('%H:%M:%S'))
    print
    return high, low


if __name__ == "__main__":
    def export_high_low_of_day(filename='daily_high_low_of_day.csv'):
        csv = CSV()
        csv.headers = ['Date', 'Symbol', 'Direction', 'High Start', 'High End', 'Low Start', 'Low End', 'High - Price',
                       'Low - Price']
        for symbol_ in ['nugt', 'jnug', 'dust', 'jdst', 'oil', 'uso']:
            day_counter = 0
            while True:
                date = datetime.date.today() - datetime.timedelta(day_counter)
                high, low = find_high_and_low_of_day_for_symbol(symbol_, date)
                day_counter += 1
                if not high or not low:
                    break
                high_time_start = high[1].strftime('%H:%M:%S')
                high_time_end = high[2].strftime('%H:%M:%S')
                low_time_start = low[1].strftime('%H:%M:%S')
                low_time_end = low[2].strftime('%H:%M:%S')
                csv.add_row([date.strftime('%m/%d/%Y'), symbol_.upper(), get_symbol_direction(symbol_, date=date).value,
                             high_time_start, high_time_end, low_time_start, low_time_end, high[0], low[0]])
        csv.save(filename)


    symbols = ['nugt', 'jnug', 'dust', 'jdst', 'oil', 'uso']
    if False:
        print 'Daily Statistics:'
        print '=' * 50
        for symbol_ in symbols:
            print "\t%s:" % symbol_.upper()
            bull, bear, neutral = get_daily_percentage_on_stock(symbol_)
            print '\t\t- Messages:'
            print "\t\t\t%.2f%% (%s) Bull\n\t\t\t%.2f%% (%s) Bear\n\t\t\t%.2f%% (%s) Neutral" % (
                bull[0], bull[1], bear[0], bear[1],
                neutral[0], neutral[1])
            market_type = get_symbol_direction(symbol_)  # date=datetime.datetime.now().date())
            print '\t\t- Market Type:\n\t\t\t%s' % market_type
            print '\t\t- User Accuracy:\n\t\t\t%s' % get_user_accuracy_per_symbol(symbol_, market_type)
            print
        print '=' * 50

        for symbol_ in ['nugt', 'jnug', 'dust', 'jdst', 'oil', 'uso']:
            find_high_and_low_of_day_for_symbol(symbol_, datetime.date.today() - datetime.timedelta(3))
            find_high_and_low_of_day_for_symbol(symbol_, datetime.date.today() - datetime.timedelta(2))
            find_high_and_low_of_day_for_symbol(symbol_, datetime.date.today() - datetime.timedelta(1))
            find_high_and_low_of_day_for_symbol(symbol_)

    Export.high_and_lows(symbols=symbols, filename='exported_data/high_and_lows.csv')
