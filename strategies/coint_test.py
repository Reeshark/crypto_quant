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

def calculate_cointegrated(df1,df2):
    crypto1=(df1['close_price']).to_numpy()
    crypto2 = (df2['close_price']).to_numpy()
    crypto1_mean=np.mean(crypto1)
    crypto2_mean=np.mean(crypto2)
    weight=crypto1_mean/crypto2_mean
    returns_crypto1 = (crypto1[1:] - crypto1[:-1]) / crypto1[:-1]
    returns_crypto2 = (crypto2[1:] - crypto2[:-1]) / crypto2[:-1]
    # returns_crypto1 = np.log(crypto1 / np.roll(crypto1, 1))
    # returns_crypto2 = np.log(crypto2 / np.roll(crypto2, 1))
    coint_t, pvalue, crit_value = coint(crypto1, crypto2)
    coint_t2, pvalue2, crit_value2 = coint(returns_crypto1, returns_crypto2)
    spread = crypto1 - crypto2*weight
    pvalue_adf = adfuller(spread)[1]
    spread = crypto1/crypto2
    pvalue_adf2 = adfuller(spread)[1]
    return pvalue,pvalue2,pvalue_adf,pvalue_adf2

if __name__ == '__main__':
    #symbols = ['RVNUSDT', 'SHIBUSDT']
    stat_df=pd.DataFrame(columns=["coin_pair1","coin_pair2", "num_candles", "coint_value", "coint_value2", "adfvalue", "adfvalue2"])
    symbols = coin_whole_list
    for symbol1 in symbols:
        for symbol2 in symbols:
            if symbol1==symbol2:
                continue
            try: #有些csv没有，防止程序中断
                internal = '15m'
                balance_ratio = [0.5, 0.5]
                init_balance = 10000
                num_candles = 10000
                offset=5000
                transaction_fee = 0.0002
                df1 = pd.read_csv(f"D:\\Trade\\data\\{symbol1}_{internal}_contract.csv")
                df2 = pd.read_csv(f"D:\\Trade\\data\\{symbol2}_{internal}_contract.csv")
                if len(df1)<num_candles+offset:
                    print("%s is less than %d"%(symbol1,num_candles+offset))
                if len(df2)<num_candles+offset:
                    print("%s is less than %d"%(symbol2,num_candles+offset))
                df1, df2 = get_overlapping(df1, df2)
                df1 = df1[-(num_candles+offset):-offset]  # extract the latest n candles
                df2 = df2[-(num_candles+offset):-offset]  # extract the latest n candles
                coint_value,coint_value2,adfvalue,adfvalue2=calculate_cointegrated(df1,df2)
                if len(df1)>num_candles*0.9: #至少有90%的K线参与评测
                    data={"coin_pair1":symbol1,"coin_pair2":symbol2 , "num_candles": len(df1), "coint_value": coint_value, "coint_value2": coint_value2,
                         "adfvalue": adfvalue, "adfvalue2": adfvalue2}
                    stat_df = pd.concat([stat_df, pd.DataFrame([data])], ignore_index=True)
                    print('%s<->%s num_candles:%d coint value:%.3f coint value2:%.3f adfvalue:%.3f adfvalue2:%.3f' % (
                    symbol1, symbol2, len(df1), coint_value, coint_value2, adfvalue, adfvalue2))
            except:
                a=1
    stat_df=stat_df.sort_values(by='coint_value', ascending=True)
    rest_df = pd.DataFrame(
        columns=["coin_pair1", "coin_pair2", "num_candles", "coint_value", "coint_value2", "adfvalue", "adfvalue2"])
    coins_list=[] # 用于存储已经配对的币，如果已经在list里存在了这个币，则直接跳过 (贪心法的思路)
    for index, row_info in enumerate(stat_df.iterrows()):
        row = row_info[1]
        if row["coint_value"]<0.2 and not row['coin_pair1'] in coins_list and not row['coin_pair2'] in coins_list:
            rest_df = pd.concat([rest_df, pd.DataFrame([row_info[1]])], ignore_index=True)
            coins_list.append(row['coin_pair1'])
            coins_list.append(row['coin_pair2'])
    dump_root="D:\\Trade\\results\\pair_trading\\24.10.29\\"
    os.makedirs(dump_root, exist_ok=True)
    num_files=len(os.listdir(dump_root))
    file_path=dump_root+'test%d.csv'%num_files
    rest_df.to_csv(file_path, index=False)
    print("testing")