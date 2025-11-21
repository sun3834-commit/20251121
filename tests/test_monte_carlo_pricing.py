import math
import pytest

from monte_carlo_pricing import MonteCarloSpec, build_payoff, monte_carlo_price


def _black_scholes_call(spot: float, strike: float, rate: float, vol: float, maturity: float) -> float:
    d1 = (math.log(spot / strike) + (rate + 0.5 * vol**2) * maturity) / (vol * math.sqrt(maturity))
    d2 = d1 - vol * math.sqrt(maturity)

    def norm_cdf(x: float) -> float:
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    return spot * norm_cdf(d1) - strike * math.exp(-rate * maturity) * norm_cdf(d2)


def test_monte_carlo_call_close_to_black_scholes():
    spec = MonteCarloSpec(spot=100, rate=0.05, volatility=0.2, maturity=1.0)
    payoff = build_payoff("max(s - 100, 0)")

    result = monte_carlo_price(spec, payoff, paths=200000, steps=1, seed=7)
    bs_price = _black_scholes_call(spot=100, strike=100, rate=0.05, vol=0.2, maturity=1.0)

    assert result.price == pytest.approx(bs_price, rel=2e-2, abs=0.25)


def test_build_payoff_uses_path_average():
    spec = MonteCarloSpec(spot=100, rate=0.0, volatility=0.01, maturity=1.0)
    payoff = build_payoff("max(sum(path) / len(path) - 100, 0)")

    result = monte_carlo_price(spec, payoff, paths=5000, steps=4, seed=123)

    assert result.price >= 0
    assert result.standard_error > 0
