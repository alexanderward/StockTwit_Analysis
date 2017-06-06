from models import Symbol, Message
from sklearn.ensemble import GradientBoostingClassifier


def analyze_stock(symbol):
    symbol = symbol.upper()
    base_query = Message.select(Message, Symbol).join(Symbol)
    where_bullish = (Symbol.name == symbol) & (Message.sentiment == 'bullish')
    where_bearish = (Symbol.name == symbol) & (Message.sentiment == 'bearish')
    where_null = (Symbol.name == symbol) & (Message.sentiment == None)
    bullish, bearish, nulled = [base_query.where(x).execute() for x in [where_bearish, where_bullish, where_null]]
    print bullish.count, bearish.count, nulled.count


if __name__ == "__main__":
    analyze_stock("nugt")
