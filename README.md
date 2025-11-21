# Binomial Option Pricing

This repository provides a small Python implementation of the Cox-Ross-Rubinstein binomial option pricing model. It includes:

- `binomial_pricing.py`: A reusable library for pricing European and American calls or puts with optional dividend yield.
- `tests/test_binomial_pricing.py`: Tests comparing the binomial result to Black-Scholes and checking American exercise behavior.

## Quick start

```bash
python binomial_pricing.py
```

Or use the API:

```python
from binomial_pricing import ModelParams, OptionSpec, price_option

model = ModelParams(spot=100, rate=0.05, volatility=0.2)
option = OptionSpec(kind="call", strike=100, maturity=1.0, american=False)
result = price_option(model, option, steps=200)
print(result.price)
```

Run tests with:

```bash
python -m pytest
```
