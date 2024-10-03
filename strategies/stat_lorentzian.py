from get_factors import *
import pandas as pd
import numpy as np
import utils
from visual.plot import plot_lorentzian_stat
import pandas as pd
import os

def stat_lorentzian(df):
    future_internal=10
    df = calculate_ADX(df)
    df = calculate_rsi(df)
    df = calculate_macd(df)
    df = calculate_wt(df)
    df = calculate_lorentzian(df)
    df = calculate_wave(df, src_type='hlc3', clen=10, alen=21, slen=4)
    df = calculate_wave_1d(df, src_type='hl2', clen=60, alen=30, slen=25)
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
    stat_signals={}
    stat_signals = pd.DataFrame(columns=['is_correct', 'lor_signal', 'lor_score','macd','wt','adx','rsi'])
    for index, row_info in enumerate(df.iterrows()): #遍历统计正确信号
        if index>len(df)-future_internal:
            continue
        row=row_info[1]
        signal=row['lor_signal']
        if row['prediction']>4:
            signal=1
        elif row['prediction']<-4:
            signal=-1
        if signal==1 or signal==-1: #出现洛伦兹买或卖信号时
            cur_price=row['close_price']
            future_price=df['close_price'].iloc[index+1:index+future_internal+1]
            #if (future_price.tolist()[-1] - cur_price)*signal> cur_price*0.05: #做多信号在未来n时刻涨 或者 做空信号在未来n时刻跌
            if max((future_price- cur_price)*signal)>cur_price*0.2:
                info = {'is_correct': True, 'lor_signal': signal, 'lor_score': row['prediction'], 'macd': row['MACD_Histogram'],
                        'wt': row['WT'],
                        'adx': row['ADX'], 'rsi': row['RSI'],'wave_o':row['wave_o'],'wave_s':row['wave_s'],'wave_h':row['wave_h'],
                        'wave_1d_h':row['wave_1d_h']}
            else: #预测失败
                info = {'is_correct': False, 'lor_signal': signal, 'lor_score': row['prediction'], 'macd': row['MACD_Histogram'],
                        'wt': row['WT'],
                        'adx': row['ADX'], 'rsi': row['RSI'],'wave_o':row['wave_o'],'wave_s':row['wave_s'],'wave_h':row['wave_h'],
                        'wave_1d_h':row['wave_1d_h']}
            info=pd.DataFrame([info])
            stat_signals = pd.concat([stat_signals, info], ignore_index=True)
    return stat_signals


def calculate_profit(df,balance=10000):
    cur_balance=[]
    for index, row_info in enumerate(df.iterrows()):
        if index==0:
            cur_balance.append(balance)
            continue
        last_price=df['close_price'].values[index-1]
        cur_price=df['close_price'].values[index]
        profit=df['strategy_signal'].values[index-1]*((cur_price-last_price)/last_price)*balance
        balance+=profit
        cur_balance.append(balance)
    df['balance']=cur_balance
    return df

if __name__ == '__main__':

    symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'DOGEUSDT', 'ETCUSDT',
               "YFIUSDT",
               "BCHUSDT",
               "AVAXUSDT",
               "LTCUSDT",
               "ORDIUSDT",
               "APTUSDT",
               "AAVEUSDT",
               "INJUSDT",
               "LINKUSDT",
               "TRBUSDT",
               "WLDUSDT",
               "NEARUSDT",
               "FILUSDT",
               "RNDRUSDT",
               "DOTUSDT",
               "ARUSDT",
               "ILVUSDT",
               "TIAUSDT",
               "XMRUSDT",
               "COMPUSDT",
               "QNTUSDT",
               "EGLDUSDT",
               "ATOMUSDT",
               "ENSUSDT",
               "RUNEUSDT",
               "CFXUSDT",
               "CRVUSDT",
               "AIUSDT",
               "IDUSDT",
               "PORTALUSDT",
               "ICPUSDT"]
    symbols = ['PEOPLEUSDT']
    internals=['1d','4h','1h','15m']
    internals=['4h']
    num_candles=20000
    ADX_thrs=[30,35,40]
    RSI_offsets=[10,15,20]
    #ADX_thrs=[40]
    #RSI_offsets=[10]
    mode='B'
    for symbol in symbols:
        for internal in internals:
                dump_root='C:\\trade\\results\wave_trading\\24.9.22\\'
                os.makedirs(dump_root, exist_ok=True)
                num_files = len(os.listdir(dump_root))
                print('Backtesting:%s_%s_%s'%(symbol,internal,num_candles))
                df = pd.read_csv(f"C:\\trade\\Data\\{symbol}_{internal}_spot.csv")
                df = df[-num_candles:] # extract the latest n candles
                stat_signal =stat_lorentzian(df)
                plot_lorentzian_stat(stat_signal,dump_root + 'test%d.pdf' % num_files)
                print('testing')