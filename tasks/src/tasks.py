from datetime import timedelta
from celery import Celery
from stocktwits import StockTwitFeed, insert_messages, StockTwitIntraday, insert_intraday_trades


celery = Celery('stocktwits')
celery.conf.update(
    BROKER_URL='redis://redis:6379',
    CELERY_TASK_SERIALIZER='json',
    CELERY_ACCEPT_CONTENT=['json'],
    CELERYBEAT_SCHEDULE={
        'save_page': {
            'task': 'stocktwits.get_intra_day_trades',
            'schedule': timedelta(minutes=60)
        }
    }
)


@celery.task(name='stocktwits.get_intra_day_trades')
def get_intraday_trades():
    symbols = ['nugt', 'jnug', 'dust', 'jdst', 'oil', 'uso']
    for stock_symbol in symbols:
        st = StockTwitFeed(symbol=stock_symbol)
        msgs = st.retrieve_messages()

        insert_messages(stock_symbol, msgs, st.item_id, st.stream_id)

        st_prices = StockTwitIntraday(symbol=stock_symbol)
        trades = st_prices.get_intraday_trades()
        insert_intraday_trades(stock_symbol, trades)
