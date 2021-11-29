# Palantir

A simulator to backtest a replica of the Ithil protocol under historical and simulated market conditions.

### Requirements

- Poetry: Python package and version management. Install from [here](https://python-poetry.org/docs/#installation).
- Python 3.8: install from [here](https://www.python.org/downloads/).

### Setup

Install Python dependencies

```bash
poetry install
```

### Download historical data

Download daily historical data for different coins using the Coingeko api.
USD is implicitly used as vs currency (i.e. data for bitcoin is price in BTC/USD).

```bash
# E.g. download historical data from the past 20 days for bitcoin.
poetry run crawl bitcoin 20
```

### Run a simulation

__WORK IN PROGRESS__
