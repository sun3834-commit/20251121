"""Simple web interface for Monte Carlo option pricing."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict

from flask import Flask, flash, redirect, render_template_string, request, url_for

from monte_carlo_pricing import MonteCarloSpec, build_payoff, monte_carlo_price

app = Flask(__name__)
app.secret_key = "dev-secret-key"


TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Monte Carlo Option Pricer</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 2rem auto; max-width: 900px; line-height: 1.5; }
      h1 { color: #1f2937; }
      form { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
      label { font-weight: bold; }
      input, textarea { width: 100%; padding: 0.5rem; font-size: 1rem; }
      .full-row { grid-column: span 2; }
      .result { background: #f3f4f6; padding: 1rem; border-radius: 6px; margin-top: 1rem; }
      .error { color: #b91c1c; margin-top: 0.5rem; }
      button { padding: 0.75rem 1rem; font-size: 1rem; background: #2563eb; color: white; border: none; border-radius: 4px; cursor: pointer; }
      button:hover { background: #1d4ed8; }
    </style>
  </head>
  <body>
    <h1>Monte Carlo Option Pricer</h1>
    <p>Provide market parameters and a payoff expression that uses <code>s</code> for the terminal price and <code>path</code> for the list of prices along the simulated path.</p>

    {% with messages = get_flashed_messages() %}
      {% if messages %}
        {% for message in messages %}
          <div class="error">{{ message }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}

    <form method="post" action="{{ url_for('price') }}">
      <div>
        <label for="spot">Spot price</label>
        <input type="number" step="any" id="spot" name="spot" value="{{ params.spot }}" required>
      </div>
      <div>
        <label for="rate">Risk-free rate</label>
        <input type="number" step="any" id="rate" name="rate" value="{{ params.rate }}" required>
      </div>
      <div>
        <label for="volatility">Volatility</label>
        <input type="number" step="any" id="volatility" name="volatility" value="{{ params.volatility }}" required>
      </div>
      <div>
        <label for="maturity">Maturity (years)</label>
        <input type="number" step="any" id="maturity" name="maturity" value="{{ params.maturity }}" required>
      </div>
      <div>
        <label for="dividend_yield">Dividend yield</label>
        <input type="number" step="any" id="dividend_yield" name="dividend_yield" value="{{ params.dividend_yield }}" required>
      </div>
      <div>
        <label for="paths">Paths</label>
        <input type="number" id="paths" name="paths" value="{{ defaults.paths }}" min="1" required>
      </div>
      <div>
        <label for="steps">Steps per path</label>
        <input type="number" id="steps" name="steps" value="{{ defaults.steps }}" min="1" required>
      </div>
      <div>
        <label for="seed">Random seed (optional)</label>
        <input type="number" id="seed" name="seed" value="">
      </div>
      <div class="full-row">
        <label for="payoff">Payoff expression</label>
        <textarea id="payoff" name="payoff" rows="2" placeholder="max(s - 100, 0)">{{ defaults.payoff }}</textarea>
      </div>
      <div class="full-row">
        <button type="submit">Price option</button>
      </div>
    </form>

    {% if result %}
      <div class="result">
        <h2>Result</h2>
        <p><strong>Price:</strong> {{ "%.6f" | format(result.price) }}</p>
        <p><strong>Standard error:</strong> {{ "%.6f" | format(result.standard_error) }} (paths={{ result.paths }})</p>
      </div>
    {% endif %}
  </body>
</html>
"""


def _parse_float(field: str, value: str) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"Invalid numeric value for {field}") from exc


def _parse_int(field: str, value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"Invalid integer value for {field}") from exc
    if parsed <= 0:
        raise ValueError(f"{field} must be positive")
    return parsed


@app.get("/")
def index() -> str:
    spec = MonteCarloSpec(spot=100.0, rate=0.05, volatility=0.2, maturity=1.0)
    defaults: Dict[str, Any] = {"paths": 20000, "steps": 1, "payoff": "max(s - 100, 0)"}
    return render_template_string(TEMPLATE, params=asdict(spec), defaults=defaults, result=None)


@app.post("/")
def price() -> str:
    try:
        spec = MonteCarloSpec(
            spot=_parse_float("spot", request.form["spot"]),
            rate=_parse_float("rate", request.form["rate"]),
            volatility=_parse_float("volatility", request.form["volatility"]),
            maturity=_parse_float("maturity", request.form["maturity"]),
            dividend_yield=_parse_float("dividend yield", request.form["dividend_yield"]),
        )
        payoff_expr = request.form.get("payoff", "")
        paths = _parse_int("paths", request.form["paths"])
        steps = _parse_int("steps", request.form["steps"])
        seed_raw = request.form.get("seed")
        seed = int(seed_raw) if seed_raw else None

        payoff = build_payoff(payoff_expr)
        result = monte_carlo_price(spec, payoff, paths=paths, steps=steps, seed=seed)
    except Exception as exc:  # noqa: BLE001
        flash(str(exc))
        return redirect(url_for("index"))

    return render_template_string(
        TEMPLATE,
        params=asdict(spec),
        defaults={"paths": paths, "steps": steps, "payoff": payoff_expr},
        result=result,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
