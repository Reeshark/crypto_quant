import pandas as pd
from get_factors import *
symbol='BTCUSDT'
interval = '1d'
num_candles=1000
df_1d = pd.read_csv(f"C:\\Trade\\data\\{symbol}_{interval}_spot.csv")
df_1d = df_1d[-num_candles:]
df_1d['open_time'] = pd.to_datetime(df_1d['open_time'], origin="1970-01-01 08:00:00", unit='ms')
df_1d['close_time'] = pd.to_datetime(df_1d['close_time'], origin="1970-01-01 08:00:00", unit='ms')
df_1d = calculate_wave(df_1d, src_type='hlc3', clen=10, alen=21, slen=4)
wave_h=df_1d['wave_h']
wave_h_s1=wave_h.shift(1)
wave_h_s2=wave_h.shift(2)
wave_h_s3=wave_h.shift(3)
wave_h_pred=7/4.0*wave_h_s1-0.5*wave_h_s2-0.25*wave_h_s3
wave_h_pred2=13/8.0*wave_h_s1-0.25*wave_h_s2-3/8.0*wave_h_s3
print('testing')