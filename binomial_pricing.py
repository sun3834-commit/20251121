"""Binomial option pricing implementation.

This module implements the Cox-Ross-Rubinstein binomial tree model with
support for European and American call/put options.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Iterable, List


@dataclass(frozen=True)
class OptionSpec:
    """Specification for a single option contract."""

    kind: str
    strike: float
    maturity: float
    american: bool = False
    dividend_yield: float = 0.0

    def payoff(self, spot: float) -> float:
        """Return the intrinsic value of the option at a given spot price."""
        if self.kind.lower() not in {"call", "put"}:
            raise ValueError("kind must be 'call' or 'put'")

        if self.kind.lower() == "call":
            return max(spot - self.strike, 0.0)
        return max(self.strike - spot, 0.0)


@dataclass(frozen=True)
class ModelParams:
    """Market parameters for the binomial model."""

    spot: float
    rate: float
    volatility: float


@dataclass(frozen=True)
class BinomialResult:
    """Result returned by the binomial pricer."""

    price: float
    tree: List[List[float]]


def _up_down(volatility: float, dt: float) -> tuple[float, float]:
    u = math.exp(volatility * math.sqrt(dt))
    d = 1 / u
    return u, d


def _risk_neutral_prob(rate: float, dividend_yield: float, dt: float, u: float, d: float) -> float:
    discounted_growth = math.exp((rate - dividend_yield) * dt)
    p = (discounted_growth - d) / (u - d)
    if not 0.0 <= p <= 1.0:
        raise ValueError("Risk-neutral probability outside [0, 1]; adjust inputs")
    return p


def price_option(model: ModelParams, option: OptionSpec, steps: int) -> BinomialResult:
    """Price a single option using a binomial tree.

    Args:
        model: Market parameters for the option.
        option: Details of the option contract.
        steps: Number of steps in the binomial tree (must be positive).

    Returns:
        BinomialResult containing the option price and the lattice of option values.
    """
    if steps <= 0:
        raise ValueError("steps must be positive")

    dt = option.maturity / steps
    u, d = _up_down(model.volatility, dt)
    p = _risk_neutral_prob(model.rate, option.dividend_yield, dt, u, d)

    # Terminal underlying prices
    terminal_spots = [model.spot * (u ** j) * (d ** (steps - j)) for j in range(steps + 1)]
    option_values = [option.payoff(s) for s in terminal_spots]

    tree: List[List[float]] = [option_values.copy()]
    discount = math.exp(-model.rate * dt)

    for step in range(steps - 1, -1, -1):
        next_values: List[float] = []
        for j in range(step + 1):
            continuation = discount * (p * option_values[j + 1] + (1 - p) * option_values[j])
            if option.american:
                spot = model.spot * (u ** j) * (d ** (step - j))
                exercise = option.payoff(spot)
                next_values.append(max(continuation, exercise))
            else:
                next_values.append(continuation)
        option_values = next_values
        tree.append(option_values.copy())

    tree.reverse()  # Root at index 0
    return BinomialResult(price=option_values[0], tree=tree)


def price_options(model: ModelParams, options: Iterable[OptionSpec], steps: int) -> List[BinomialResult]:
    """Price multiple options using the same market parameters and step count."""
    return [price_option(model, opt, steps) for opt in options]


def _example() -> None:
    model = ModelParams(spot=100, rate=0.05, volatility=0.2)
    option = OptionSpec(kind="call", strike=100, maturity=1.0, american=False)
    result = price_option(model, option, steps=200)
    print(f"European call price (N=200): {result.price:.4f}")


if __name__ == "__main__":
    _example()
