from random import gauss


DESIRED_MAX_SLIPPAGE_PERCENT = 10

# We model slippage as a normally distributed random variable with mean equal to the current price
# and variance proportional to a percentage of the price as described by max desired slippage.
GAUSS_RANDOM_SLIPPAGE = lambda price: gauss(price, price * DESIRED_MAX_SLIPPAGE_PERCENT / 100)

# We model fees as a 0% flat rate
NULL_FEES = lambda amount: amount - amount * 0.0 / 100

SECONDS_IN_A_DAY = 24 * 60 * 60
