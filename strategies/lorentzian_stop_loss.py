from get_factors import *
import pandas as pd
import numpy as np
import utils
from visual.plot import plot_price_with_adx,plot_strategy_RAL,plot_RAL
import pandas as pd

def lorentzian_stop_loss(df):
    df = calculate_lorentzian(df)
    df['open_time'] = pd.to_datetime(df['open_time'], origin="1970-01-01 08:00:00", unit='ms')
    df['close_time'] = pd.to_datetime(df['close_time'], origin="1970-01-01 08:00:00", unit='ms')
    strategy_signal=[]
    status=0
    for index, row_info in enumerate(df.iterrows()):
        row=row_info[1]
    return df

def strategy_RSI_ADX_Lorentzian(df,mode='A',ADX_thr=40,RSI_thr=[35,65]): #strategy_RAL
    df = calculate_ADX(df)
    df = calculate_rsi(df)
    df = calculate_lorentzian(df)
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
    strategy_signal=[]
    last_dir=0
    for index, row_info in enumerate(df.iterrows()):
        row=row_info[1]
        if row['ADX']< ADX_thr and row['RSI_EMA']>RSI_thr[0] and row['RSI_EMA']<RSI_thr[1]:
            is_fluctuations=True
        else:
            is_fluctuations=False
        if mode=='A': # 震荡趋势不做交易，非震荡方向取决于洛伦兹
            if not is_fluctuations:
                if row['signal']==1 and row['RSI']>50: # long (buy) signal
                    strategy_signal.append(1)
                elif row['signal']==-1 and row['RSI']<50: # short (sell) signal
                    strategy_signal.append(-1)
                else:
                    strategy_signal.append(0)
            else: # fluctuations
                strategy_signal.append(0)
        elif mode=='B': #震荡趋势沿用非震荡方向，忽略震荡中洛伦兹信号
            if not is_fluctuations: #非震荡期
                if row['lor_signal'] == 1 and row['RSI'] > 50: # long (buy) signal
                    cur_dir=1
                elif row['lor_signal']==-1 and row['RSI']<50: # short (sell) signal
                    cur_dir=-1
                else: #当前无洛伦兹信号
                    if row['prediction']>0 and row['RSI_EMA'] > 50: #如果洛伦兹看多并且RSI_EMA上穿
                        cur_dir=1
                    elif row['prediction']<0 and row['RSI_EMA'] < 50: #如果洛伦兹看空并且RSI_EMA下穿
                        cur_dir=-1
                    else:
                        cur_dir=last_dir #否则沿用上一时刻信号

            else: #震荡期沿用上一时刻信号
                cur_dir=last_dir
            strategy_signal.append(cur_dir)
            last_dir=cur_dir
        elif mode=='C': # 纯洛伦兹分类
            if row['signal']==1: # long (buy) signal
                strategy_signal.append(1)
            elif row['signal']==-1: # short (sell) signal
                strategy_signal.append(-1)
            else:
                strategy_signal.append(0)

    df['strategy_signal']=strategy_signal
    return df

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
    symbols = ['BTCUSDT']
    internals=['4h']
    #internals=['15m']
    num_candles=15000
    ADX_thrs=[30,35,40]
    high_balance_record={}
    for symbol in symbols:
        for internal in internals:
            high_balance=0
            threshold="Nan"
            df = pd.read_csv(f"D:\\Trade\\informer-Amazon\\utils\\Binacne_Data\\{symbol}\\{symbol}_{internal}_spot.csv")
            df = df[-num_candles:] # extract the latest n candles
            df =lorentzian_stop_loss(df)
            df = calculate_profit(df)
            if df['balance'].values[-1]>0:
                holding_balance=10000/df['open_price'].values[0]*df['close_price'].values[-1]
                max_recall=min(df['balance'].values)
                if df['balance'].values[-1]>high_balance:
                    high_balance=df['balance'].values[-1]
                    threshold='%s_%s, holding_balance:%d max_recall:%d'% (symbol, internal, holding_balance,max_recall)
                print('Backtesting:%s_%s_%s, %s--%s  last_balance:%d holding_balance:%d min_balance:%d'
                      % (symbol, internal, num_candles,str(df['open_time'].values[0]),str(df['open_time'].values[-1]),df['balance'].values[-1],holding_balance,max_recall))
            high_balance_record[threshold]=high_balance
    for key,value in high_balance_record.items():
        print("%s-->%d"%(key,value))