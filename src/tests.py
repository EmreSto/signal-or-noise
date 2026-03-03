import pandas as pd
import numpy as np
from synthetic import generate_garch_series
from indicators import ssl_channels ,EMA200 ,alpha_trend
from signals import crossoverdetection
from scipy import stats
def compute_touch_returns(df, length, forward_bars):
    hlv, hma_high, hma_low = ssl_channels(df, length)
    returns = []
    for i in range(1, len(df)):
        if i + forward_bars >= len(df):
            continue
        if df['low'].iloc[i] <= hma_high.iloc[i] and hlv[i] == 1:
            if df['low'].iloc[i-1] > hma_high.iloc[i-1]:
                ret = (df['close'].iloc[i + forward_bars] - df['close'].iloc[i]) / df['close'].iloc[i]
                returns.append(ret)
        elif df['high'].iloc[i] >= hma_low.iloc[i] and hlv[i] == -1:
            if df['high'].iloc[i-1] < hma_low.iloc[i-1]:
                ret = (df['close'].iloc[i] - df['close'].iloc[i + forward_bars]) / df['close'].iloc[i]
                returns.append(ret)
    return returns
def h1_test(df, length, forward_bars, n_simulations=1000):
    returns = compute_touch_returns(df, length, forward_bars)
    if len(returns) == 0:
        return None, [] ,None
    real_mean = sum(returns) / len(returns)
    synthetic_series = generate_garch_series(df['close'], n_simulations)
    simulated_means = []
    high_spread = (df['high'] - df['close']) / df['close']
    low_spread =  (df['close'] - df['low']) / df['close']
    for sim_prices in synthetic_series:
        sampled_high = np.random.choice(high_spread, size = len(sim_prices))
        sampled_low = np.random.choice(low_spread, size = len(sim_prices))
        sim_df= pd.DataFrame({
            'open': sim_prices,
            'high': sim_prices *(1+sampled_high),
            'low': sim_prices *(1-sampled_low),
            'close': sim_prices
        })
        sim_returns = compute_touch_returns(sim_df, length, forward_bars)
        if len(sim_returns) > 0:
            simulated_means.append(sum(sim_returns)/len(sim_returns))
    p_value = sum(1 for mean in simulated_means if mean >= real_mean) / n_simulations
    return real_mean, simulated_means, p_value

def h2_test(df, max_bars=30):
    crossovers = crossoverdetection(df)
    ema_close, cloud_upper, cloud_lower = EMA200(df)
    
    reached = 0
    total = 0
    crossover_bars = []
    
    for i in range(len(df)):
        if crossovers[i] == 1:
            total += 1
            for j in range(1, max_bars + 1):
                if i + j >= len(df):
                    break
                if df['high'].iloc[i+j] > cloud_lower.iloc[i+j]:
                    reached += 1
                    crossover_bars.append(j)
                    break
        elif crossovers[i] == -1:
            total += 1
            for j in range(1, max_bars + 1):
                if i + j >= len(df):
                    break
                if df['low'].iloc[i+j] < cloud_upper.iloc[i+j]:
                    reached += 1
                    crossover_bars.append(j)
                    break
    if total == 0:
        return None, None, None, None, None, None
    real_rate = reached / total
    random_reached = 0
    n_random = total * 10
    random_bars = []
    random_indices = np.random.choice(range(max_bars, len(df) - max_bars), size=n_random)
    for i in random_indices:
        if df['close'].iloc[i] < ema_close.iloc[i]:
            for j in range(1, max_bars + 1):
                if i + j >= len(df):
                    break
                if df['high'].iloc[i+j] > cloud_lower.iloc[i+j]:
                    random_reached += 1
                    random_bars.append(j)
                    break
        else:
            for j in range(1, max_bars + 1):
                if i + j >= len(df):
                    break
                if df['low'].iloc[i+j] < cloud_upper.iloc[i+j]:
                    random_reached += 1
                    random_bars.append(j)
                    break
    random_rate = random_reached / n_random
    
    # Z-test
    p1 = real_rate
    p2 = random_rate
    n1 = total
    n2 = n_random
    pooled_p = (reached + random_reached) / (n1 + n2)
    standard_error = np.sqrt(pooled_p * (1 - pooled_p) * ((1/n1) + (1/n2)))
    z_score = (p1 - p2) / standard_error if standard_error > 0 else 0
    z_p_value = stats.norm.sf(abs(z_score)) * 2
    
    # Mann-Whitney U
    if len(crossover_bars) > 0 and len(random_bars) > 0:
        u_stat, mw_p_value = stats.mannwhitneyu(crossover_bars, random_bars, alternative='less')
    else:
        u_stat, mw_p_value = None, None
    
    return real_rate, random_rate, z_score, z_p_value, mw_p_value, np.mean(crossover_bars) if crossover_bars else None
def h3_test(df, forward_bars ,n_permutations = 1000):
    at = alpha_trend(df)
    crossovers = crossoverdetection(df)
    confirmed_returns =[]
    unconfirmed_returns = []
    for i in range(1, len(df)):
        if i + forward_bars >= len(df):
            continue
        if crossovers[i] == 1:
            ret = (df['close'].iloc[i +forward_bars] - df['close'].iloc[i]) / df['close'].iloc[i]
            if at[i] > at[i-1]:
                confirmed_returns.append(ret)
            else:
                unconfirmed_returns.append(ret)
        elif crossovers[i] == -1:
            ret = (df['close'].iloc[i] - df['close'].iloc[i + forward_bars]) / df['close'].iloc[i]
            if at[i-1] > at[i]:
                confirmed_returns.append(ret)
            else:
                unconfirmed_returns.append(ret)
    if len(confirmed_returns) == 0 or len(unconfirmed_returns) == 0:
        return None, [], None
    all_returns = confirmed_returns + unconfirmed_returns
    real_delta = np.mean(confirmed_returns) - np.mean(unconfirmed_returns)
    permuted_deltas = []
    for i in range(n_permutations):
        np.random.shuffle(all_returns)
        shuffled_confirmed = all_returns[:len(confirmed_returns)]
        shuffled_unconfirmed = all_returns[len(confirmed_returns):]
        permuted_deltas.append(np.mean(shuffled_confirmed) - np.mean(shuffled_unconfirmed))
    p_value = sum(1 for delta in permuted_deltas if abs(delta) >= abs(real_delta)) / n_permutations
    return real_delta, permuted_deltas ,p_value

def h2_control_b(df, max_bars):
    crossovers = crossoverdetection(df)
    ema_close, cloud_upper, cloud_lower = EMA200(df)
    crossover_moves = []
    crossover_reached = 0
    
    for i in range(5, len(df) - max_bars):
        if crossovers[i] != 0:
            move = abs(df['close'].iloc[i] - df['close'].iloc[i-5]) / df['close'].iloc[i-5]
            crossover_moves.append(move)
            if crossovers[i] == 1:
                for j in range(1, max_bars +1):
                    if i + j >= len(df):
                        break
                    if df['high'].iloc[i+j] > cloud_lower.iloc[i+j]:
                        crossover_reached +=1
                        break
            elif crossovers[i] == -1:
                for j in range(1, max_bars +1):
                    if i +j >= len(df):
                        break
                    if df['low'].iloc[i+j] < cloud_upper.iloc[i+j]:
                        crossover_reached +=1
                        break
    if len(crossover_moves) == 0:
        return None, None, None
    avg_move = sum(crossover_moves) / len(crossover_moves)
    tolerance = 0.2  # ±20%
    control_reached = 0
    control_total = 0
    
    for i in range(5, len(df) - max_bars):
        if crossovers[i] == 0:
            move = abs(df['close'].iloc[i] - df['close'].iloc[i-5]) / df['close'].iloc[i-5]

            if move >= avg_move * (1 - tolerance) and move <= avg_move * (1 + tolerance):
                control_total += 1
                if df['close'].iloc[i] < ema_close.iloc[i]:  
                    for j in range(1, max_bars + 1):
                        if df['high'].iloc[i+j] >= cloud_lower.iloc[i+j]:
                            control_reached += 1
                            break
                else: 
                    for j in range(1, max_bars + 1):
                        if df['low'].iloc[i+j] <= cloud_upper.iloc[i+j]:
                            control_reached += 1
                            break
    
    control_rate = control_reached / control_total if control_total > 0 else None
    crossover_rate = crossover_reached / len(crossover_moves)
    return crossover_rate, control_rate, control_total