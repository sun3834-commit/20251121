import math

import pytest

from binomial_pricing import BinomialResult, ModelParams, OptionSpec, price_option


def test_price_matches_black_scholes_call():
    model = ModelParams(spot=100, rate=0.05, volatility=0.2)
    option = OptionSpec(kind="call", strike=100, maturity=1.0, american=False)

    result: BinomialResult = price_option(model, option, steps=500)

    # Black-Scholes price for comparison
    d1 = (math.log(model.spot / option.strike) + (model.rate + 0.5 * model.volatility**2) * option.maturity) / (
        model.volatility * math.sqrt(option.maturity)
    )
    d2 = d1 - model.volatility * math.sqrt(option.maturity)

    from math import erf, sqrt

    def norm_cdf(x: float) -> float:
        return 0.5 * (1 + erf(x / sqrt(2)))

    bs_price = model.spot * norm_cdf(d1) - option.strike * math.exp(-model.rate * option.maturity) * norm_cdf(d2)
    assert result.price == pytest.approx(bs_price, rel=5e-3)


def test_american_put_exercise_premium_positive():
    model = ModelParams(spot=50, rate=0.03, volatility=0.4)
    european = OptionSpec(kind="put", strike=55, maturity=1.0, american=False)
    american = OptionSpec(kind="put", strike=55, maturity=1.0, american=True)

    euro_price = price_option(model, european, steps=200).price
    amer_price = price_option(model, american, steps=200).price

    assert amer_price >= euro_price


def test_invalid_probability_raises():
    model = ModelParams(spot=100, rate=-0.5, volatility=0.01)
    option = OptionSpec(kind="call", strike=100, maturity=1.0)

    with pytest.raises(ValueError):
        price_option(model, option, steps=10)


if __name__ == "__main__":
    pytest.main([__file__])
