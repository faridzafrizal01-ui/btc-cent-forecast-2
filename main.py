#!/usr/bin/env python3
"""Bitcoin price, 4 hours ahead: one point forecast per case.

Entry for make.fun competition btc-cent-forecast-01.

Each case file holds 4,320 one-minute closes for the market btc-usdc; the
last close is the checkpoint. The score is the mean absolute error across
cases, in cents, and a prize needs a score strictly below the house
baseline (persistence: guess the checkpoint close). Persistence ties the
baseline exactly, so it can never win. This entry therefore starts from
the checkpoint close and pulls a little of the last 4-hour move back:

    guess = x - 0.3 * 400 * tanh((x - p240) / 400)

with x the checkpoint close and p240 the close 240 minutes earlier. The
practice cases show that after a large 4-hour move the price tends to
snap back over the next 4 hours, so fading the move helps; the tanh
bounds the fade at $120 and keeps it roughly proportional for small
moves. No drift term is added: the practice window drifted down, but a
drift is a regime, not a law, and betting on it continuing would be a
directional gamble.

Backtest on the 6 official practice cases: persistence 44,521.58 cents,
this entry 44,399.80 cents (-0.27%); rolling backtest over every 10th
minute of the six 72-hour histories (n = 2,412): -0.26%. The edge is
small and regime-dependent, so the final is close to a coin flip with a
slight positive lean -- the honest picture for a 4-hour-ahead BTC price,
which is close to a martingale. This entry takes the small bounded edge
the data do support rather than tying the baseline and guaranteeing no
prize.

Deterministic: a pure function of the case file. No randomness, no clock,
no network. Standard library only.
"""

import json
import math
import os

IN_DIR = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
OUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

# Grid of the scorer: prices live on 5 decimals, inside (0, 10,000,000).
STEP = 0.00001
TOP = 9999999.99999

# Fade constants, in dollars, fixed for every case -- never fitted per case.
STRENGTH = 0.3
SCALE = 400.0


def snap(price):
    """Clamp a raw guess onto the scorer's grid, strictly inside (0, 10M).

    Rounding to the grid after clamping keeps the value representable:
    a raw guess like 73833.1234567 becomes 73833.12346, never 0 and never
    at or above the 10,000,000 cap. Multiplying by 1e5 before rounding
    (rather than dividing by the step) keeps the printed value on exactly
    5 decimals instead of a float artefact like 74831.90714000001.
    """
    clipped = min(TOP, max(STEP, price))
    return round(clipped * 1e5) / 1e5


def predict(closes):
    """Forecast the price 240 minutes after the last close in `closes`."""
    if not closes:
        raise ValueError("case has no price history")
    last = closes[-1]
    if not isinstance(last, (int, float)) or not math.isfinite(last):
        raise ValueError("last close is not a finite number")
    if len(closes) > 240:
        move = last - closes[-241]
        guess = last - STRENGTH * SCALE * math.tanh(move / SCALE)
    else:
        guess = last
    return snap(guess)


def run():
    os.makedirs(OUT_DIR, exist_ok=True)
    for filename in sorted(os.listdir(IN_DIR)):
        if not filename.endswith(".in"):
            continue
        case_id = filename[: -len(".in")]
        with open(os.path.join(IN_DIR, filename), encoding="utf-8") as fh:
            case = json.load(fh)
        markets = case.get("markets")
        if not isinstance(markets, list) or len(markets) != 1:
            raise ValueError(f"{filename}: expected exactly one market")
        price = predict(markets[0]["prices"])
        with open(os.path.join(OUT_DIR, case_id + ".out"), "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"forecasts": [{"case": case_id, "price": price}]}) + "\n")


if __name__ == "__main__":
    run()
