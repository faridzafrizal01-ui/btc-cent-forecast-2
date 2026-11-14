# BTC Cent Forecast

Entry for make.fun competition `btc-cent-forecast-01`.

Forecasts Bitcoin's US-dollar price 240 minutes (4 hours) after each
checkpoint, one point guess per case. The score is the mean absolute error
over the cases, in cents; a prize needs a score strictly below the house
baseline's (persistence) on the final, with every case valid.

## Method

`main.py` (Python 3.13, standard library only) reads each `<id>.in` case
file (4,320 one-minute closes, the last one the checkpoint close) and
writes `<id>.out` as `{"forecasts": [{"case": "<id>", "price": <guess>}]}`.

The guess starts from the checkpoint's own close and fades a small part of
the last 240 minutes' move, because the practice data show that after a
large 4-hour move the price tends to snap back over the next 4 hours:

```
guess = x - 0.3 * 400 * tanh((x - p240) / 400)
```

where `x` is the checkpoint close and `p240` the close 240 minutes
earlier. The tanh keeps the fade bounded (at most $120) and roughly
proportional for small moves. No drift term: the practice window's
downward drift is a regime, not a law.

## Backtest (practice, 6 official cases)

| entry | MAE (cents) | vs baseline |
|---|---|---|
| persistence (house baseline) | 44,521.58 | — |
| this entry | 44,399.81 | **-0.27%** |

Rolling backtest over every 10th minute of the six cases' 72-hour
histories (target +240 min): persistence 35,303.90 cents, this entry
35,213.20 cents (-0.26%).

The edge is small and regime-dependent — honest assessment in `main.py`'s
docstring. Persistence ties the baseline and can never win; this entry
takes the small, bounded edge the data support.

## Run

```sh
mkdir -p out && MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```
