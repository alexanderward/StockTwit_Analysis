import datetime
from utils import MarketType
from models import Symbol, Message, SymbolPrice, db


class Filters(object):
    class Generic(object):
        @staticmethod
        def symbol_is(symbol):
            return Symbol.name == symbol

    class Message(object):
        @staticmethod
        def movement():
            return (Message.sentiment == MarketType.bear.value), (Message.sentiment == MarketType.bull.value), \
                   (Message.sentiment == MarketType.neutral.value)

        @staticmethod
        def join_on_symbol():
            return Message.select(Message, Symbol).join(Symbol)

        @staticmethod
        def today():
            return db.truncate_date('day', Message.timestamp) == datetime.date.today()

    class Symbol(object):
        @staticmethod
        def movement(symbol):
            assert isinstance(symbol, basestring)
            symbol_filter = (Symbol.name == symbol)
            bearish, bullish, null = Filters.Message.movement()
            return bearish & symbol_filter, bullish & symbol_filter, null & symbol_filter

    class SymbolPrice(object):
        @staticmethod
        def base():
            return SymbolPrice.select(SymbolPrice)

        @staticmethod
        def join_on_symbol():
            return SymbolPrice.select(SymbolPrice, Symbol).join(Symbol)

        @staticmethod
        def today():
            return db.truncate_date('day', SymbolPrice.start_timestamp) == datetime.date.today()

        @staticmethod
        def date_is(date):
            return db.truncate_date('day', SymbolPrice.start_timestamp) == date

