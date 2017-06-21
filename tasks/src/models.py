import peewee

db = peewee.SqliteDatabase('StockTwit_Feeds.db', threadlocals=True)


class Symbol(peewee.Model):
    name = peewee.CharField(unique=True)
    stream_id = peewee.CharField()
    item_id = peewee.CharField()

    class Meta:
        database = db


class SymbolPrice(peewee.Model):
    symbol = peewee.ForeignKeyField(Symbol)
    start_timestamp = peewee.DateTimeField(null=False)
    end_timestamp = peewee.DateTimeField(null=False)
    trades = peewee.IntegerField()
    volume = peewee.IntegerField()
    utc_offset = peewee.CharField()
    low = peewee.FloatField()
    open = peewee.FloatField()
    close = peewee.FloatField()
    high = peewee.FloatField()
    twap = peewee.FloatField()
    vwap = peewee.FloatField()

    class Meta:
        database = db
        primary_key = peewee.CompositeKey('start_timestamp', 'end_timestamp', 'symbol')

    def __str__(self):
        return str(self.symbol)


class User(peewee.Model):
    id = peewee.IntegerField(unique=True)
    username = peewee.CharField()
    name = peewee.CharField()

    class Meta:
        database = db


class Message(peewee.Model):
    symbol = peewee.ForeignKeyField(Symbol)
    user = peewee.ForeignKeyField(User)
    st_id = peewee.IntegerField(unique=True)
    sentiment = peewee.CharField(null=True)
    reshares = peewee.IntegerField(null=True)
    likes = peewee.IntegerField(null=True)
    timestamp = peewee.DateTimeField()
    body = peewee.TextField()

    class Meta:
        database = db


def check_database():
    db.connect()
    try:
        db.create_tables([User, Message, Symbol, SymbolPrice])
    except peewee.OperationalError:
        pass
    db.close()


check_database()
