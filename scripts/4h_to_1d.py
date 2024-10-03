import pandas as pd
import numpy as np

symbol = 'BTCUSDT'
interval = '4h'
num_candles = 5000
df = pd.read_csv(f"C:\\Trade\\data\\{symbol}_{interval}_spot.csv")
df = df[-num_candles:]
df['open_time'] = pd.to_datetime(df['open_time'], origin="1970-01-01 08:00:00", unit='ms')
df['close_time'] = pd.to_datetime(df['close_time'], origin="1970-01-01 08:00:00", unit='ms')