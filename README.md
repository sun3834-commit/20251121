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

## Monte Carlo web calculator

Launch a simple Flask server that wraps the Monte Carlo pricer with an HTML form:

```bash
pip install -r requirements.txt
python web_app.py
```

Then open http://localhost:8000 in your browser. Enter market parameters, the number of simulated paths/steps, and a payoff expression using `s` (terminal price) and `path` (full path). Example payoffs:

- European call: `max(s - 100, 0)`
- Digital call: `1 if s > 100 else 0`
- Asian call (average price): `max(sum(path)/len(path) - 100, 0)`
