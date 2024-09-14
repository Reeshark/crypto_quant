import sys
sys.path.append('./')
sys.path.append('./strategies/')
import os
import numpy as np
from coin_list import coin_whole_list
import pandas as pd
import datetime
from datetime import datetime, timezone, timedelta
import requests
from get_factors import *
import multiprocessing
from termcolor import colored


def get_cur_price(symbol,interval,end_time,max_candles):
    columns = ["open_time", "open_price", "high_price", "low_price", "close_price",
           "volume", "close_time", "turnover", "tickcount", "active_buying_volume",
           "active_buying_turnover", "Unknown"]
    klines = []
    limit = max_candles
    contractType = "PERPETUAL"
    while len(klines)<max_candles:
        # url = f"https://api.binance.com/api/v3/klines?symbol={symbol}"+\
        # f"&interval={interval}&endTime={end_time}&limit={limit}" # for spot
        url = f"https://fapi.binance.com/fapi/v1/continuousKlines?pair={symbol}"+\
            f"&contractType={contractType}&interval={interval}&endTime={end_time}&limit={limit}" # contract
        print(url)
        # Send the request
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            klines = data + klines
            try:
                end_time = data[0][0] - 1
            except:
                break
        else:
            # If the API returns an error, print the response
            print(response.json())
            break
    df = pd.DataFrame(klines, columns=columns)
    df = df.astype(float)
    df['open_time'] = pd.to_datetime(df['open_time'], origin="1970-01-01 08:00:00",unit='ms')
    df['close_time'] = pd.to_datetime(df['close_time'], origin="1970-01-01 08:00:00", unit='ms')
    return df

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def get_signals(symbol,interval,max_candles):
    global print_list
    print(symbol)
    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    df = get_cur_price(symbol, interval, now, max_candles)
    df = calculate_lorentzian(df)
    # 寻找最后一个信号的索引
    last_short_index = list(np.where(df['lor_signal'].to_numpy() == -1))[0][-1]
    last_long_index = list(np.where(df['lor_signal'].to_numpy() == 1))[0][-1]
    cur_ts = pd.to_datetime(now, origin="1970-01-01 08:00:00", unit='ms')
    if (cur_ts - df['close_time'].values[max(last_long_index, last_short_index)]) < timedelta(
            hours=12):  # 判断最后一次信号是否距离现在在两天之内
        if last_short_index>last_long_index:
            print_str = ("Symbol:%s, now:%s last_short:%s" %
                         (symbol, str(cur_ts)[:19], str(df['close_time'].to_list()[last_short_index])[:19]))
            #print(colored(print_str, 'red'))
            print(f"{bcolors.FAIL}%s{bcolors.ENDC}" % print_str) # print with red
        else:
            print_str = ("Symbol:%s, now:%s last_long:%s" %
                         (symbol, str(cur_ts)[:19],  str(df['close_time'].to_list()[last_long_index])[:19]))

            #print(colored(print_str,'green'))
            print(f"{bcolors.OKGREEN}%s{bcolors.ENDC}" % print_str) # print with green
        print_list.append(print_str)

if __name__ == '__main__':
    global print_list
    print_list=[]
    symbols=coin_whole_list
    interval="4h"
    max_candles=1000
    failed_list=[]
    for symbol in symbols:
        try: #如果网络失败就计入failed_list里 后面再重新跑一次
            get_signals(symbol,interval,max_candles)
        except:
            print("Running %s Failed!"%symbol)
            failed_list.append(symbol)

    failed_list2 = failed_list
    tries=0
    while(len(failed_list2)!=0): #循环跑 直到没有了为止
        print("rest of list:")
        print(failed_list)
        failed_list2 = []
        for symbol in failed_list:
            try:  # 如果网络失败就计入failed_list里 后面再重新跑一次
                get_signals(symbol,interval,max_candles)
            except:
                print("Running %s Failed!" % symbol)
                failed_list2.append(symbol)
        failed_list=failed_list2
        tries+=1
        if tries>20: #超过20次尝试如果还没跑出来就不要了
            break
    for idx,print_str in enumerate(print_list):
        if "long" in print_str:
            #print(colored("%d. %s"%(idx+1,print_str),'green'))
            print(f"%d. {bcolors.OKGREEN}%s{bcolors.ENDC}" % (idx+1, print_str)) # print with green
        else:
            #print(colored("%d. %s"%(idx+1,print_str),'red'))
            print(f"%d. {bcolors.FAIL}%s{bcolors.ENDC}" % (idx + 1, print_str)) # print with red