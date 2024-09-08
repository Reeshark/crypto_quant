from get_factors import *
import pandas as pd
import numpy as np
import utils,os
from strategies.RSI_ADX_Lorentzian import calculate_profit
from visual.plot import plot_three_trade,plot_one_trade
def get_trade_factors(df):
    df = calculate_ADX(df)
    df = calculate_rsi(df)
    df = calculate_macd(df)
    df = calculate_wt(df)
    df = calculate_lorentzian(df)
    return df

def continuous_trend(df,index,back_length=3):
    if index<back_length+1:
        return 0
    Ks=df.iloc[index-back_length:index + 1]
    status=0
    for i in range(1,back_length+1):
        if status==0: #初始状态
            if Ks['MACD_Histogram'].values[i]>=Ks['MACD_Histogram'].values[i-1]:
                status=1
            else:
                status=-1
        elif status==1: #前一状态为增
            if Ks['MACD_Histogram'].values[i]>=Ks['MACD_Histogram'].values[i-1]:
                status=1
            else:
                return 0 #没有连续形成相同趋势
        elif status==-1:
            if Ks['MACD_Histogram'].values[i]<Ks['MACD_Histogram'].values[i-1]:
                status=-1
            else:
                return 0 #没有连续形成相同趋势
    return status

def get_internal_factors(df,index,cur_time):
    success=False
    for cur_index in range(index,len(df)-1): #在大周期向下寻找对应当前时间的K线
        if df['close_time'].values[cur_index]>cur_time: #当前大周期时间超过了交易时间
            success=False
            return cur_index,success
        elif df['close_time'].values[cur_index]<=cur_time and df['close_time'].values[cur_index+1]>cur_time: #找到对应K线
            success=True
            return cur_index,success
        elif cur_index==len(df)-1: #遍历到了最后一个K线
            return cur_index,success
    return cur_index,success
def three_trend_align(df,mode='A'):
    for i in range(3):
        df[i]=get_trade_factors(df[i])
        df[i]['MACD_CT']=[0]*len(df[i])
    index_first,index_second=0,0
    signal=[]
    for index_third in range(len(df[2])): #遍历所有第三级区间数据
        cur_time=df[2]['open_time'].values[index_third]
        index_first,suc_first=get_internal_factors(df[0],index_first,cur_time)
        index_second, suc_second = get_internal_factors(df[1], index_second, cur_time)
        if not (suc_first and suc_second): #某个大周期找不到对应K线
            signal.append(0)
            continue
        else: #找到对应K线
            K_first=df[0].iloc[index_first:index_first+1]
            macd1,lor1=K_first['MACD_Histogram'].values[0],K_first['signal'].values[0]
            macd1_ct=continuous_trend(df[0],index_first)
            df[0].iloc[index_first,43]=macd1_ct
            K_second=df[1].iloc[index_second:index_second+1]
            macd2, lor2 = K_second['MACD_Histogram'].values[0], K_second['signal'].values[0]
            macd2_ct = continuous_trend(df[1], index_second)
            df[1].iloc[index_second,43]=macd2_ct
            K_third=df[2].iloc[index_third:index_third+1]
            macd3, lor3 = K_third['MACD_Histogram'].values[0], K_third['signal'].values[0]
            macd3_ct = continuous_trend(df[2], index_third)
            df[2].iloc[index_third,43]=macd3_ct
            if mode=='A': #三种周期，两种指标全部相同
                if lor1 == 1 and lor2 == 1 and lor3 == 1 and macd1 > 0 and macd2 > 0 and macd3 > 0:  # 三个周期，两种指标均是看多
                    signal.append(1)
                elif lor1 == -1 and lor2 == -1 and lor3 == -1 and macd1 < 0 and macd2 < 0 and macd3 < 0:  # 三个周期，两种指标均是看空
                    signal.append(-1)
                else:  # 啥也不是
                    signal.append(0)
            if mode=='B': #除了A的情况之外，如果MACD在连续n跟K线均趋势相同(递增/递减)同样出信号
                if lor1==1 and lor2==1 and lor3==1 and macd1>0 and macd2>0 and macd3>0: #三个周期，两种指标均是看多
                    signal.append(1)
                elif lor1==-1 and lor2==-1 and lor3==-1 and macd1<0 and macd2<0 and macd3<0: #三个周期，两种指标均是看空
                    signal.append(-1)
                elif lor1==1 and lor2==1 and lor3==1 and macd1_ct==1 and macd2_ct==1 and macd3_ct==1: #三个周期洛伦兹看多，macd持续增长
                    signal.append(1)
                elif lor1==-1 and lor2==-1 and lor3==-1 and macd1_ct==-1 and macd2_ct==-1 and macd3_ct==1: #三个周期洛伦兹看空，macd持续下降
                    signal.append(-1)
                else: #啥也不是
                    signal.append(0)
            if mode=='C': #大周期MACD或lor，中周期Lor或MACD，小周期MACD或Lor:
                if (macd1 or lor1==1) > 0 and (lor2 == 1 or macd2>0) and (lor3 == 1 or macd3>0):  # 三个周期，两种指标均是看多
                    signal.append(1)
                elif (macd1<0 or lor1==-1)  and (lor2 == -1 or macd2<0) and (lor3 == -1 or macd3<0):  # 三个周期，两种指标均是看空
                    signal.append(-1)
                else:  # 啥也不是
                    signal.append(0)
            if mode=='D': #大周期MACD或n根K线趋势或lor，中周期Lor或MACD金死叉，小周期MACD金死叉或Lor:
                if (macd1>0 or macd1_ct==1 or lor1==1) and (lor2 == 1 or macd2>0) and (lor3 == 1 or macd3>0):  # 三个周期，两种指标均是看多
                    signal.append(1)
                elif (macd1<0 or macd1_ct==-1 or lor1==-1) and (lor2 == -1 or macd2<0) and (lor3 == -1 or macd3<0):  # 三个周期，两种指标均是看空
                    signal.append(-1)
                else:  # 啥也不是
                    signal.append(0)
            if mode=='E': #大周期MACD或n根K线趋势或lor，中周期Lor或n根K线趋势，小周期MACD金死叉或Lor:
                if (macd1>0 or macd1_ct==1 or lor1==1) and (lor2 == 1 or macd2_ct==1) and (lor3 == 1 or macd3>0):  # 三个周期，两种指标均是看多
                    signal.append(1)
                elif (macd1<0 or macd1_ct==-1 or lor1==-1) and (lor2 == -1 or macd2_ct==-1) and (lor3 == -1 or macd3<0):  # 三个周期，两种指标均是看空
                    signal.append(-1)
                else:  # 啥也不是
                    signal.append(0)
            if mode=='F': #大周期n根K线趋势，中周期MACD，小周期Lor:
                if (macd1>0) and (macd2>0) and (lor3 == 1 ):  # 三个周期，两种指标均是看多
                    signal.append(1)
                elif (macd1<0 ) and ( macd2<0) and (lor3 == -1):  # 三个周期，两种指标均是看空
                    signal.append(-1)
                else:  # 啥也不是
                    signal.append(0)
    df[2]['strategy_signal'] = signal
    return df

def get_prices(symbol='BTCUSDT',internals=['1d','4h','1h'],num_candles=1000):
    df=[]
    df.append(pd.read_csv(f"C:\\Trade\\data\\{symbol}_{internals[0]}_spot.csv"))
    # df1['open_time'] = pd.to_datetime(df1['open_time'], unit='ms')
    # df1['close_time'] = pd.to_datetime(df1['close_time'], unit='ms')
    df[0] = df[0][-num_candles:]  # extract the latest n candles
    df.append(pd.read_csv(f"C:\\Trade\\data\\{symbol}_{internals[1]}_spot.csv"))
    # df2['open_time'] = pd.to_datetime(df2['open_time'], unit='ms')
    # df2['close_time'] = pd.to_datetime(df2['close_time'], unit='ms')
    df[1] = df[1][-num_candles:]  # extract the latest n candles
    df.append(pd.read_csv(f"C:\\Trade\\data\\{symbol}_{internals[2]}_spot.csv"))
    # df3['open_time'] = pd.to_datetime(df3['open_time'], unit='ms')
    # df3['close_time'] = pd.to_datetime(df3['close_time'], unit='ms')
    df[2] = df[2][-num_candles:]  # extract the latest n candles
    time_start=max(df[0]['open_time'].values[0],df[1]['open_time'].values[0],df[2]['open_time'].values[0])
    time_end=min(df[0]['close_time'].values[-1],df[1]['close_time'].values[-1],df[2]['close_time'].values[-1])
    for i in range(3):
        # df[i] = df[i].loc[df[i]['open_time'] > time_start]
        # df[i] = df[i].loc[df[i]['close_time'] < time_end]
        df[i]['open_time'] = pd.to_datetime(df[i]['open_time'], unit='ms')
        df[i]['close_time'] = pd.to_datetime(df[i]['close_time'], unit='ms')
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
    internals=['1d','4h','1h','15m']
    #internals=['1d','4h','1h']
    #internals = ['4h', '1h', '15m']
    internals_dict={'1h':['1d','4h','1h'],'15m':['4h', '1h', '15m']}
    internals_dict = {'1h': ['1d', '4h', '1h']}
    modes=['A','B','C','D','E']
    modes=['F']
    num_candles=5000
    for symbol in symbols:
        for key,internals in internals_dict.items():
            for mode in modes:
                print('Backtesting:%s_%s_%s_%s'%(symbol,internals[-1],num_candles,mode))
                df=get_prices(symbol,internals,num_candles)
                df=three_trend_align(df,mode=mode)
                df1,df2,df3=df
                df3 = calculate_profit(df3)
                file_name='%s_%s_%s.pdf'%(symbol, internals[-1],mode)
                #plot_three_trade(df,symbol,internals,mode='F',ADX_thr=80,RSI_thr=[0,100],dump_file='D:\\Trade\\three_trend\\24.8.15\\%s'%file_name)
                dump_file='C:\\Trade\\three_trend\\24.8.15\\'
                os.makedirs(dump_file,exist_ok=True)
                plot_one_trade(df, symbol, internals, mode='F', ADX_thr=15, RSI_thr=[0, 100],dump_file=dump_file+'\\%s'%file_name)
                holding_balance = 10000 / df3['open_price'].values[0] * df3['close_price'].values[-1]
                print('Backtesting:%s_%s_%s, %s--%s last_balance:%d holding_balance:%d '% (
                      symbol, internals[-1], num_candles, str(df3['open_time'].tolist()[0]), str(df3['close_time'].tolist()[-1]),df3['balance'].values[-1], holding_balance))