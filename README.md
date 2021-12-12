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
USD is implicitly used as vs currency (i.e. data for Ether is price in ETH/USD).

```bash
# E.g. download historical hourly price data from the past 20 days for ETH.
poetry run crawler ethereum 20
```

### Run a simulation

You need to configure your simularion parameters in `palantir/main.py` and prepare your data by cleaning your old db if you have it and downloading new data for the currencies you want to use.

Once you have downloaded the price data and configured your simulation just do

```bash
poetry run simulation
```
