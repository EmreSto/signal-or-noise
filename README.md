# indicators-signal-or-illusion

**Do trading indicators show real market patterns, or do they just make noise look like patterns?**

## What This Is

This project tests three indicators commonly used together in retail trading systems (SSL Channels, AlphaTrend, EMA 200) to determine whether the patterns they produce reflect real market structure or are artifacts of the indicator math.

## What I Test

**H1: Do SSL channels act as real support and resistance?**
Compare forward returns after fresh channel tests on real data vs 1000 GARCH-generated synthetic price series (200 for EUR). If synthetic data shows the same returns, the pattern is not real.

**H2: Does price move toward EMA 200 after a crossover?**
Compare EMA reach rate and time-to-reach after crossovers against two baselines: random entry points (Control A) and similar sized moves without a crossover (Control B). Two-proportion z-test and Mann-Whitney U.

**H3: Does AlphaTrend help filter bad crossovers?**
Split crossovers into confirmed and unconfirmed by AlphaTrend, then run a permutation test with 1,000 shuffles to check if the difference is real.

All p-values go through Benjamini-Hochberg correction across 114 tests.

## Data

| Asset | Instrument | Source | Period |
|-------|-----------|---------|--------|
| BTC/USD | CME Globex BTC Futures | Databento | Jan 2023 – Jan 2026 |
| EUR/USD | CME 6E Futures | Databento | Jan 2023 – Jan 2025 |

All futures. All real exchange volume. Single data provider. Timeframes: 15m, 30m, 1h, 2h, 4h.

## Results

| Hypothesis | Significant | Total | Result |
|-----------|-------------|-------|--------|
| H1: SSL Channel Tests | 0 | 54 | No signal. Indistinguishable from GARCH noise. |
| H2: EMA Attraction | 30 | 30 | Real signal. Survives BH correction across both assets. |
| H3: AlphaTrend Filter | 0 | 30 | No value added. Confirmed = unconfirmed. |

**30 discoveries out of 114 tests after Benjamini-Hochberg correction (FDR = 0.05). All 30 are H2.**

### Key Findings

- **SSL channel lines are noise.** Fresh channel test returns are indistinguishable from GARCH synthetic data. P-values cluster around 0.5 across all timeframes and both assets.
- **Dual HMA regime crossover predicts EMA 200 movement.** 65-79% reach rate vs 25-49% from random and momentum-matched controls. Average time to reach: 1.5-4.5 bars. Both z-test and Mann-Whitney U significant.
- **AlphaTrend adds nothing.** Confirmed and unconfirmed crossovers perform the same. The crossover already captures the directional signal.
- **Practical implication:** The useful system reduces to HMA regime alignment + EMA 200 target. Channel lines and AlphaTrend can be removed.

## Methodology

Based on Lopez de Prado, *Advances in Financial Machine Learning* (2018). Synthetic nulls (Ch 13), multiple testing correction (Ch 14). No train/test split - each test builds its own null internally. Full details in [methodology.md](docs/methodology.md).

## Project Structure
```
├── src/
│   ├── aggregation_data.py   # Data loading and OHLCV resampling
│   ├── indicators.py         # HMA, SSL Channels, AlphaTrend, EMA 200
│   ├── signals.py            # SSL crossover detection
│   ├── synthetic.py          # GARCH(1,1) synthetic price generation
│   ├── tests.py              # H1, H2, H3 test functions
│   └── corrections.py        # Benjamini-Hochberg correction
├── notebooks/
│   ├── 00_validation.ipynb   # Function pipeline check
│   ├── 01_h1_synthetic_null.ipynb
│   ├── 02_h2_ema_attraction.ipynb
│   ├── 03_h3_permutation.ipynb
│   └── 04_summary.ipynb      # BH correction and final results
├── docs/
│   └── methodology.md
└── pinescript/
    └── mtf_regime_combined.pine
```

## References

- Lopez de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley.
- Benjamini, Y. & Hochberg, Y. (1995). Controlling the false discovery rate.
- KivancOzbilgic. AlphaTrend. TradingView.