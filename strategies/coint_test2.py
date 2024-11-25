from get_factors import *
from visual.plot import plot_trend
import os
import numpy as np
import pandas as pd
from strategies.pair_trading import get_overlapping
from coin_list import coin_whole_list,coin_test_list
import statsmodels
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint, adfuller

def generate_data(params):
    mu = params[0]
    sigma = params[1]
    return np.random.normal(mu, sigma)

def calculate_cointegrated(df1,df2,length,num_candles):
    coint_list=[]
    adf_list=[]
    open_list=[]
    close_list=[]
    corr_list=[]
    for start in range(0,num_candles,length):
        start_time=str(df1['open_time'].tolist()[start])
        end_time=str(df1['close_time'].tolist()[start+length-1])
        crypto1=(df1['close_price']).to_numpy()[start:start+length]
        crypto2 = (df2['close_price']).to_numpy()[start:start+length]
        weight=crypto1[0]/crypto2[0]
        coint_t, pvalue, crit_value = coint(crypto1, crypto2)
        spread = crypto1 - crypto2*weight
        pvalue_adf = adfuller(spread)[1]
        corr=pd.Series(crypto1).corr(pd.Series(crypto2))
        coint_list.append(pvalue)
        adf_list.append(pvalue_adf)
        open_list.append(start_time)
        close_list.append(end_time)
        corr_list.append(corr)
    return coint_list,adf_list,open_list,close_list,corr_list

if __name__ == '__main__':
    #symbols = ['RVNUSDT', 'SHIBUSDT']
    internal = '1h'
    balance_ratio = [0.5, 0.5]
    init_balance = 10000
    num_candles = 4000
    offset = 1
    length=1000
    columns=["coin_pair1","coin_pair2", "num_candles"]
    for num in range(int(num_candles/length)):
        for key in ['start','end','coint','adf','corr']:
            columns+=[key+'_%d'%num]
    stat_df=pd.DataFrame(columns=columns)
    symbols = coin_whole_list
    for symbol1 in symbols:
        for symbol2 in symbols:
            if symbol1==symbol2:
                continue
            try: #有些csv没有，防止程序中断
                df1 = pd.read_csv(f"D:\\Trade\\data\\{symbol1}_{internal}_contract.csv")
                df2 = pd.read_csv(f"D:\\Trade\\data\\{symbol2}_{internal}_contract.csv")
                if len(df1)<num_candles+offset:
                    print("%s is less than %d"%(symbol1,num_candles+offset))
                if len(df2)<num_candles+offset:
                    print("%s is less than %d"%(symbol2,num_candles+offset))
                df1, df2 = get_overlapping(df1, df2)
                df1 = df1[-(num_candles+offset):-offset]  # extract the latest n candles
                df2 = df2[-(num_candles+offset):-offset]  # extract the latest n candles
                coint_list,adf_list,open_list,close_list,corr_list=calculate_cointegrated(df1,df2,length=length,num_candles=num_candles)
                if len(df1)>num_candles*0.9: #至少有90%的K线参与评测
                    data={"coin_pair1":symbol1,"coin_pair2":symbol2 , "num_candles": len(df1)}
                    for num in range(int(num_candles / length)):
                        data['start_%d'%num]=open_list[num]
                        data['end_%d' % num] = close_list[num]
                        data['coint_%d' % num] = coint_list[num]
                        data['adf_%d' % num] = adf_list[num]
                        data['corr_%d' % num] = corr_list[num]
                    stat_df = pd.concat([stat_df, pd.DataFrame([data])], ignore_index=True)
            except:
                a=1
    stat_df=stat_df.sort_values(by='corr_0', ascending=True)
    rest_df = pd.DataFrame(columns=columns)
    coins_list=[] # 用于存储已经配对的币，如果已经在list里存在了这个币，则直接跳过 (贪心法的思路)
    for index, row_info in enumerate(stat_df.iterrows()):
        row = row_info[1]
        if row["coint_0"]<0.3 and row['adf_0']<0.3 and row['corr_0']>0.8 and not row['coin_pair1'] in coins_list and not row['coin_pair2'] in coins_list:
            rest_df = pd.concat([rest_df, pd.DataFrame([row_info[1]])], ignore_index=True)
            coins_list.append(row['coin_pair1'])
            coins_list.append(row['coin_pair2'])
    dump_root="D:\\Trade\\results\\pair_trading\\24.11.20\\"
    os.makedirs(dump_root, exist_ok=True)
    num_files=len(os.listdir(dump_root))
    file_path=dump_root+'coint_1h_5000_1000_%d.csv'%num_files
    rest_df.to_csv(file_path, index=False, float_format='%.4f')
    print("testing")