"""BTC 4h-ahead point forecaster for make.fun btc-cent-forecast-01.

One guess per case. The working assumption is that Bitcoin's price
four hours ahead is usually close to the checkpoint close, but after a
sharp move over the previous 240 minutes it tends to give part of that
move back. So the guess starts at the checkpoint close and fades a
bounded slice of the last-240-minute move: the fade is a tanh of the
move, which caps it at 0.3 * 400 = 120 price units no matter how far
the market ran. The result is then clamped onto the scorer's
5-decimal grid strictly inside (0, 10_000_000).

Standard library only. Deterministic: no randomness, no clock, no
network. Input and output directories come from the environment.
"""

import json
import math
import os
from pathlib import Path

LOOKBACK = 240            # minutes back to the reference close
FADE_SHARE = 0.3          # fraction of the scaled move to fade back
TANH_SCALE = 400.0        # tanh scale, in the same units as prices
GRID_LOW = 0.00001        # smallest price the scorer accepts
GRID_HIGH = 9999999.99999  # largest price the scorer accepts
GRID_PLACES = 5           # scorer's price grid, in decimals


def read_closes(path):
    """Load one <id>.in case file and return its list of closes."""
    with path.open() as handle:
        case = json.load(handle)

    markets = case.get("markets")
    if not isinstance(markets, list) or len(markets) != 1:
        raise ValueError(f"{path.name}: expected exactly one market")

    prices = markets[0].get("prices")
    if not isinstance(prices, list) or not prices:
        raise ValueError(f"{path.name}: missing or empty price list")

    last = prices[-1]
    if isinstance(last, bool) or not isinstance(last, (int, float)):
        raise ValueError(f"{path.name}: last close is not numeric")
    if not math.isfinite(last):
        raise ValueError(f"{path.name}: last close is not finite")

    return prices


def guess_price(prices):
    """One forecast for a list of closes; the last close is the checkpoint."""
    x = prices[-1]
    if len(prices) > LOOKBACK:
        p240 = prices[-LOOKBACK - 1]
        # tanh keeps the fade bounded: at most FADE_SHARE * TANH_SCALE
        # (= 120) even after an extreme 4-hour run, and near-linear
        # for small moves, so ordinary drift is faded proportionally.
        guess = x - FADE_SHARE * TANH_SCALE * math.tanh((x - p240) / TANH_SCALE)
    else:
        guess = x
    clipped = min(GRID_HIGH, max(GRID_LOW, guess))
    return round(clipped * 10 ** GRID_PLACES) / 10 ** GRID_PLACES


def main():
    input_dir = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
    output_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    output_dir.mkdir(parents=True, exist_ok=True)

    for in_path in sorted(input_dir.glob("*.in")):
        case_id = in_path.stem
        price = guess_price(read_closes(in_path))
        payload = {"forecasts": [{"case": case_id, "price": price}]}
        with (output_dir / f"{case_id}.out").open("w") as handle:
            handle.write(json.dumps(payload) + "\n")


if __name__ == "__main__":
    main()
