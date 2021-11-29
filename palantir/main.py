from argparse import ArgumentParser
from sqlalchemy.orm import sessionmaker

from palantir.crawlers.coingecko import (
    coin_ids,
    Interval,
    market_chart,
)
from palantir.db import init_db, Quote


VS_CURRENCY = "usd"


def crawl():
    """
    Download price data for coin `token` for the last `days` days from Coingeko API
    """
    parser = ArgumentParser()
    parser.add_argument("token", metavar="token", type=str, help="The token we need prices for")
    parser.add_argument("days", metavar="days", type=int, help="Number of days of historical data")
    args = parser.parse_args()

    valid_coin_ids = list(coin_ids())
    valid_coin_ids_msg = f"Coin should be one of {valid_coin_ids}"

    token = args.token
    assert token in valid_coin_ids, valid_coin_ids_msg

    days = args.days

    prices = market_chart(token, VS_CURRENCY, days, Interval.DAILY)

    quotes = [
        Quote(coin=token, vs_currency=VS_CURRENCY, timestamp=timestamp, price=price)
        for timestamp, price in prices
    ]

    db = init_db()

    Session = sessionmaker(bind=db)
    session = Session()

    for quote in quotes:
        session.add(quote)

    session.commit()


def backtest():
    # TODO backtest entry point
    pass
