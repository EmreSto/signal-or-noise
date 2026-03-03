import pandas as pd 
def load_and_resample(filepath, timeframe):
    df = pd.read_csv(filepath)
    df = df[~df['symbol'].str.contains('-')]
    df['date'] = pd.to_datetime(df['ts_event']).dt.date
    daily_volume = df.groupby(['date','symbol'])['volume'].sum()
    best = daily_volume.reset_index()
    best = best.loc[best.groupby('date')['volume'].idxmax()]
    df = pd.merge(df, best[['date', 'symbol']], on=['date', 'symbol'])
    df['ts_event'] = pd.to_datetime(df['ts_event'])
    df = df.set_index('ts_event')
    df = df.resample(timeframe).agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'})
    df = df.dropna()
    return df


