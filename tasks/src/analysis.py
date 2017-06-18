import datetime

from models import Symbol, Message


# from sklearn.ensemble import GradientBoostingClassifier

def get_percentage(count, total):
    return (float(count) / float(total)) * 100


def analyze_stock(symbol):
    symbol = symbol.upper()
    base_query = Message.select(Message, Symbol).join(Symbol)
    where_bullish = (Symbol.name == symbol) & (Message.sentiment == 'bullish')
    where_bearish = (Symbol.name == symbol) & (Message.sentiment == 'bearish')
    where_null = (Symbol.name == symbol) & (Message.sentiment == None)
    bullish, bearish, nulled = [base_query.where(x).execute() for x in [where_bearish, where_bullish, where_null]]
    print bullish.count, bearish.count, nulled.count


def get_daily_percentage_on_stock(symbol):
    symbol = symbol.upper()
    base_query = Message.select(Message, Symbol).join(Symbol)
    today_query = Message.timestamp >= datetime.date.today()
    where_bullish = (Symbol.name == symbol) & (Message.sentiment == 'bullish')
    where_bearish = (Symbol.name == symbol) & (Message.sentiment == 'bearish')
    where_null = (Symbol.name == symbol) & (Message.sentiment == None)
    bullish, bearish, nulled = [base_query.where(x).where(today_query).execute() for x in
                                [where_bearish, where_bullish, where_null]]
    total = bullish.count + bearish.count + nulled.count
    print "%s:\n%.2f%% (%s) Bull\n%.2f%% (%s) Bear\n%.2f%% (%s) Neutral\n" % (
        symbol, get_percentage(bullish.count, total),
        bullish.count,
        get_percentage(bearish.count, total),
        bearish.count,
        get_percentage(nulled.count, total),
        nulled.count)


if __name__ == "__main__":
    # analyze_stock("nugt")
    # analyze_stock("jnug")
    # analyze_stock("dust")
    # analyze_stock("jdst")

    get_daily_percentage_on_stock("uso")
    get_daily_percentage_on_stock("nugt")
    get_daily_percentage_on_stock("jnug")
    get_daily_percentage_on_stock("dust")
    get_daily_percentage_on_stock("jdst")
