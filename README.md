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

When running a simulation Palantir will automatically download the desired price data and store it in a local SQLite database on the first run.
The tokens used and the number of samples are specified at the beginning of `palantir.main:run_sumulation()`.

### Run a simulation

You need to configure your simularion parameters in `palantir/main.py` and prepare your data by cleaning your old db if you have it and downloading new data for the currencies you want to use.

Once you have downloaded the price data and configured your simulation just do

```bash
poetry run simulation
```

### Run unit tests

We use Pytest to run tests. Just run the following commands to execute unit tests in a virtual environment.

Activate Poetry's virtual environment

```bash
poetry shell
```

Run Pytest's unit tests

```bash
pytest
```

Deactivate the virtual environment

```bash
exit
```
