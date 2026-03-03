# Methodology

## Research Question

Do the patterns observed when using SSL Channels, AlphaTrend, and EMA 200 reflect real market behavior, or are they side effects of the indicator math?

## Why This Matters

Indicators are built from price. When price "bounces" off an indicator line, part of that is price interacting with its own smoothed version. This would happen on random data too. Lopez de Prado (2018) argues that skipping this check leads to false discoveries. This project does not try to find alpha. It tests whether the patterns are real in the first place.

## The Indicators

### SSL Channel

Two hull moving averages form a band around price. A regime variable tracks which side of the band price is on.

**Weighted Moving Average:**

$$WMA(t) = \frac{\sum_{i=1}^{N} i \cdot X_{t-N+i}}{\sum_{i=1}^{N} i}$$

**Hull Moving Average:**

$$HMA(t) = WMA\left(2 \cdot WMA(X, \lfloor N/2 \rfloor) - WMA(X, N), \; \lfloor\sqrt{N}\rfloor\right)$$

HMA nearly eliminates lag while staying smooth. The $2 \cdot WMA(\text{half}) - WMA(\text{full})$ overshoots intentionally to compensate for lag. The final $WMA(\sqrt{N})$ smooths the result.

**Regime variable:**

$$hlv(t) = \begin{cases} +1 & \text{if } C_t > HMA_H(t) \\ -1 & \text{if } C_t < HMA_L(t) \\ hlv(t-1) & \text{otherwise} \end{cases}$$

The regime is sticky. It only flips when price closes beyond a boundary. Inside the channel, the previous state holds.

**Line swap:**

$$\text{If } hlv(t) = +1: \quad \text{upper} = HMA_H(t), \quad \text{lower} = HMA_L(t)$$

$$\text{If } hlv(t) = -1: \quad \text{upper} = HMA_L(t), \quad \text{lower} = HMA_H(t)$$

When the regime flips, the lines swap. This creates the visible crossover on the chart.

**Two channels:** We run $N = 60$ (fast) and $N = 120$ (slow) at the same time.

**Crossover (both channels agree):**

A crossover fires when both regimes first agree on a new direction.

Bullish crossover at bar $t$:

$$hlv_{60}(t) = +1 \quad \text{and} \quad hlv_{120}(t) = +1 \quad \text{and not both } +1 \text{ at } t-1$$

Bearish crossover at bar $t$:

$$hlv_{60}(t) = -1 \quad \text{and} \quad hlv_{120}(t) = -1 \quad \text{and not both } -1 \text{ at } t-1$$

The bands may visually cross without triggering this if the hlv values did not actually change.

### AlphaTrend

An adaptive trailing stop combining volatility (ATR), momentum (MFI), and a ratchet mechanism.

**Volatility:**

$$TR_t = \max(H_t - L_t, \; |H_t - C_{t-1}|, \; |L_t - C_{t-1}|)$$

$$ATR(t) = \frac{1}{N}\sum_{i=0}^{N-1} TR_{t-i}$$

ATR uses SMA, not Wilder's smoothing. $N = 14$.

**Support and resistance levels:**

$$upT_t = L_t - \alpha \cdot ATR(t) \qquad downT_t = H_t + \alpha \cdot ATR(t)$$

$\alpha = 1.0$. $upT$ sits one ATR below the low. $downT$ sits one ATR above the high.

**Momentum gate:**

$$\text{bullish}(t) = \begin{cases} \text{true} & \text{if } MFI(t) \geq 50 \\ \text{false} & \text{otherwise} \end{cases}$$

MFI is computed over 14 bars using $HLC3$ and volume. All assets in this project have real exchange volume, so MFI is used uniformly.

**Ratchet:**

$$AT(t) = \begin{cases} \max(upT_t, \; AT(t-1)) & \text{if bullish}(t) \\ \min(downT_t, \; AT(t-1)) & \text{if not bullish}(t) \end{cases}$$

The ratchet only allows movement in the trend direction. This creates the staircase shape. Flat sections mean the new level was not enough to move the line.

For H3, we check whether the staircase is stepping up, down, or flat at the time of a crossover. We do not use AlphaTrend's own buy/sell signals.

### EMA 200

$$EMA(t) = \lambda \cdot C_t + (1 - \lambda) \cdot EMA(t-1) \qquad \lambda = \frac{2}{N+1}$$

With $N = 200$, $\lambda \approx 0.01$. Moves slowly. Acts as a long-term trend reference.

**Cloud:**

$$\text{cloud upper} = EMA_H(t) \qquad \text{cloud lower} = EMA_C(t)$$

$EMA_H$ is EMA of highs, $EMA_C$ is EMA of close. The cloud width adapts naturally to volatility rather than using a fixed percentage.

## How The System Works Together

1. SSL(60) and SSL(120) run simultaneously.
2. A crossover fires when both regimes first agree on a new direction.
3. AlphaTrend confirms or denies the crossover: if the staircase steps in the same direction, confirmed. If it stays flat or goes the other way, unconfirmed.
4. EMA 200 acts as a target price tends to move toward after a crossover.

## Hypotheses

### H1: SSL Channel Returns

- **Claim:** SSL channels capture real support and resistance - tests produce meaningful directional returns
- **Null:** Post-touch returns on real data are no different from synthetic GARCH data
- **Method:** Empirical p-value from 1000 synthetic series (BTC) / 200 (EUR). Forward returns at 5, 10, 20 bars. Tested on each channel (60 and 120) separately.

**Touch definition:** A "fresh channel test" - price enters the channel zone from outside. Bullish: low penetrates HMA_H while hlv = +1 and previous bar's low was above HMA_H. Bearish: high penetrates HMA_L while hlv = -1 and previous bar's high was below HMA_L. This filters out bars where price simply lingers inside the channel.

### H2: EMA 200 Attraction Post-Crossover

- **Claim:** Price moves toward EMA 200 after a crossover (both SSLs agree)
- **Null A:** EMA reach rate from crossovers = from random timestamps
- **Null B:** EMA reach rate from crossovers = from similar sized moves without a crossover
- **Method:** Two-proportion z-test (reach rate) and Mann-Whitney U (time to reach)

### H3: AlphaTrend Confirmation Filter

- **Claim:** Confirmed crossovers perform better than unconfirmed ones
- **Null:** No difference. The gap could come from random label assignment
- **Method:** Permutation test (10,000 shuffles)

Confirmed = both SSLs agree + AlphaTrend steps in the same direction. Unconfirmed = both SSLs agree but AlphaTrend flat or opposite.

## Data

| Asset    | Instrument             | Source    | Period              |
|----------|------------------------|-----------|---------------------|
| BTC/USD  | CME Globex BTC Futures | Databento | Jan 2023 – Jan 2026 |
| EUR/USD  | CME 6E Futures         | Databento | Jan 2023 – Jan 2025 |

All futures. All real exchange volume. Single data provider.

Timeframes: 15m, 30m, 1h, 2h, 4h. Total tests: 114 (54 H1 + 30 H2 + 30 H3).

## Test Procedures

### H1: Synthetic Data Comparison

1. Fit GARCH(1,1) to real returns for each asset and timeframe.
2. Generate 1000 synthetic price series from the fitted model. Same statistics, no market structure.
3. Construct synthetic OHLC: close from GARCH, high/low from randomly sampled real intrabar spreads.
4. Compute fresh channel test returns on each synthetic series and on real data. Forward returns measured at 5, 10, 20 bars. Bullish: (close[t+N] - close[t]) / close[t]. Bearish: flipped so positive = regime correct.
5. p-value = proportion of synthetic mean returns >= real mean return.

Runs separately for SSL(60) and SSL(120).

### H2: Two-Control Comparison

1. Find all crossovers (both SSLs agree on new direction).
2. Track whether price reaches EMA 200 cloud within N bars (10, 20, 30). Record bars to reach.
3. Control A: same metric from random timestamps (10x sample size).
4. Control B: same metric from points with similar sized price moves but no crossover.
5. Two-proportion z-test against each control (reach rate comparison).
6. Mann-Whitney U test against Control A (time-to-reach comparison, one-sided: crossovers expected to reach faster).

Reading results:
- Beats random but not directional moves: crossover just flags big moves.
- Beats both: indicator captures something beyond price movement.
- Beats neither: no EMA attraction effect.

### H3: Permutation Test

1. Find all crossovers (both SSLs agree). Label as confirmed or unconfirmed by AlphaTrend.
2. Measure directional return at 5, 10, 20 bars forward. Positive = crossover was right.
3. Compute delta = mean(confirmed) - mean(unconfirmed).
4. Shuffle labels 1,000 times. Compute delta each time.
5. p-value = proportion of shuffles where |delta| >= observed.

## Overfitting Defense

No train/test split. Hypotheses came from trading the whole period, so splitting would be dishonest. Instead:

1. **Synthetic nulls (H1):** Must beat structureless data.
2. **Control groups (H2):** Must beat random and directional-move baselines.
3. **Permutation tests (H3):** Must survive random label shuffling.
4. **Multiple comparison correction:** Must survive correction across all tests.

## Multiple Comparison Correction

Benjamini-Hochberg at FDR = 0.05.

1. Sort all p-values: $p_{(1)} \leq p_{(2)} \leq \cdots \leq p_{(m)}$
2. For rank $i$, threshold = $\frac{i}{m} \times 0.05$
3. Find largest $i$ where $p_{(i)} \leq$ threshold.
4. All ranks $\leq i$ are discoveries.

Both raw and corrected p-values reported. Only BH-corrected results claimed.

## Results

### H1: 0/54 significant
SSL channel touches produce returns indistinguishable from GARCH synthetic data across all timeframes and both assets. P-values cluster around 0.5 — dead center of the null distribution.

### H2: 30/30 significant (all p < 0.0001)
Dual regime crossovers reach EMA 200 at 65-79% vs 25-49% from both random bars (Control A) and momentum-matched bars (Control B). Average time to reach: 1.5-4.5 bars. Both z-test and Mann-Whitney U significant across all tests. Effect is consistent across all timeframes and both BTC and EUR/USD.

### H3: 0/30 significant
AlphaTrend confirmation does not separate good crossovers from bad. Confirmed and unconfirmed crossovers produce similar returns. On some timeframes, unconfirmed crossovers performed slightly better.

### After Benjamini-Hochberg correction (FDR = 0.05)
30 discoveries out of 114 tests. All 30 are H2. No H1 or H3 test survives correction.

### Practical implication
The SSL channel lines themselves are noise - any smoothed average produces the same "resistance/support." But dual HMA regime alignment captures real directional structure that predicts movement toward EMA 200. AlphaTrend adds complexity for zero benefit. The useful system reduces to: dual HMA regime crossover + EMA 200 target.


## References

- Lopez de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley. Ch 11, 13, 14.
- Benjamini, Y. & Hochberg, Y. (1995). Controlling the false discovery rate.
- Fisher, R.A. (1935). The Design of Experiments.
- KivancOzbilgic. AlphaTrend. MPL 2.0. https://www.tradingview.com/script/o50NYLAZ-AlphaTrend/
