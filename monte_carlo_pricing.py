"""Monte Carlo option pricing with user-defined payoff expressions.

This module simulates asset paths under geometric Brownian motion and prices
options by discounting expected payoffs. Users can supply a Python expression
for the payoff, using ``s`` for the terminal price and ``path`` for the full
price path.
"""
from __future__ import annotations

import argparse
import math
import random
import statistics
from dataclasses import dataclass
from typing import Callable, List


PayoffFunc = Callable[[float, List[float]], float]


@dataclass(frozen=True)
class MonteCarloSpec:
    """Market and contract parameters for simulation."""

    spot: float
    rate: float
    volatility: float
    maturity: float
    dividend_yield: float = 0.0


@dataclass(frozen=True)
class MonteCarloResult:
    """Result of a Monte Carlo price estimation."""

    price: float
    standard_error: float
    paths: int


def build_payoff(expression: str) -> PayoffFunc:
    """Compile a payoff expression into a callable.

    The expression can reference:
    - ``s``: the terminal asset price.
    - ``path``: the list of asset prices over the simulated path (including the initial price).
    Basic math helpers (``math``, ``max``, ``min``, ``abs``) are available.
    """

    expression = expression.strip()
    if not expression:
        raise ValueError("payoff expression cannot be empty")

    code = compile(expression, "<payoff>", "eval")
    allowed_globals = {
        "__builtins__": {},
        "math": math,
        "max": max,
        "min": min,
        "abs": abs,
        "sum": sum,
        "len": len,
    }

    def payoff(s: float, path: List[float]) -> float:
        value = eval(code, allowed_globals, {"s": s, "path": path})
        return float(value)

    return payoff


def monte_carlo_price(
    spec: MonteCarloSpec,
    payoff: PayoffFunc,
    *,
    paths: int = 10000,
    steps: int = 1,
    seed: int | None = None,
) -> MonteCarloResult:
    """Estimate an option price via Monte Carlo simulation.

    Args:
        spec: Market parameters and maturity.
        payoff: Callable accepting ``(terminal_price, path)``.
        paths: Number of simulated paths.
        steps: Time steps per path (>=1). ``steps=1`` samples the terminal price directly.
        seed: Optional seed for reproducible draws.
    """

    if paths <= 0:
        raise ValueError("paths must be positive")
    if steps <= 0:
        raise ValueError("steps must be positive")

    rng = random.Random(seed)
    dt = spec.maturity / steps
    drift = (spec.rate - spec.dividend_yield - 0.5 * spec.volatility**2) * dt
    vol_step = spec.volatility * math.sqrt(dt)

    discounted_payoffs: List[float] = []
    discount_factor = math.exp(-spec.rate * spec.maturity)

    for _ in range(paths):
        price = spec.spot
        path_values = [price]
        for _ in range(steps):
            z = rng.gauss(0.0, 1.0)
            price *= math.exp(drift + vol_step * z)
            path_values.append(price)

        discounted_payoff = discount_factor * payoff(price, path_values)
        discounted_payoffs.append(discounted_payoff)

    mean_payoff = statistics.fmean(discounted_payoffs)
    if paths > 1:
        std_dev = statistics.pstdev(discounted_payoffs)
        standard_error = std_dev / math.sqrt(paths)
    else:
        standard_error = 0.0

    return MonteCarloResult(price=mean_payoff, standard_error=standard_error, paths=paths)


def _cli() -> None:
    parser = argparse.ArgumentParser(description="Monte Carlo option pricer with custom payoff expression")
    parser.add_argument("payoff", help="Python expression using 's' (terminal price) and 'path' (list of prices)")
    parser.add_argument("--spot", type=float, default=100.0, help="Current asset price")
    parser.add_argument("--rate", type=float, default=0.05, help="Risk-free annual rate")
    parser.add_argument("--vol", type=float, default=0.2, help="Annual volatility")
    parser.add_argument("--maturity", type=float, default=1.0, help="Time to maturity in years")
    parser.add_argument("--dividend", type=float, default=0.0, help="Continuous dividend yield")
    parser.add_argument("--paths", type=int, default=20000, help="Number of Monte Carlo paths")
    parser.add_argument("--steps", type=int, default=1, help="Time steps per path")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")

    args = parser.parse_args()

    spec = MonteCarloSpec(
        spot=args.spot,
        rate=args.rate,
        volatility=args.vol,
        maturity=args.maturity,
        dividend_yield=args.dividend,
    )
    payoff_fn = build_payoff(args.payoff)
    result = monte_carlo_price(spec, payoff_fn, paths=args.paths, steps=args.steps, seed=args.seed)

    print(f"Price: {result.price:.6f}")
    print(f"Standard error: {result.standard_error:.6f} (paths={result.paths})")


if __name__ == "__main__":
    _cli()
