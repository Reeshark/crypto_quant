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
from wave_strategy import *
from wave_trend import *
import json

# status：
# 1：正在开多->做多
# 0.5：开多临时避险->不做
# 0：观望->不做
# -0.5：开空临时避险->不做
# -1：正在开空->做空

# 整体过程：大周期多：观望-开多-临时避险-返场-结束
#         大周期空：观望-开空-临时避险-返场-结束

# 1.观望时：可以开多或开空

# 1.1开多条件：大周期(1d)多 && ((lor信号多) || (prediction>=4) && 波浪趋势蓝色)
# 1.2开空条件：大周期(1d)空 && ((lor信号空) || (prediction<=-4) && 波浪趋势粉色)

# 2.开多时：可以临时退场避险或返场
#
# 2.1 临时退场：lor信号空 || ((prediction<0) && 波浪趋势粉色 && 波浪趋势>0)
# 2.2 退场后返场：((prediction>2) && 波浪趋势预判下一时刻或已经蓝色)


# 3.开空时：可以临时退场避险或返场
#
# 3.1 临时退场：lor信号多 || ((prediction>0) && 波浪趋势蓝色 && 波浪趋势<0)
# 3.2 退场后返场：((prediction<-2) && 波浪趋势预判下一时刻或已经粉色)

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

def get_symbol(print_str):
    position=print_str.find("USDT")
    return print_str[7:position+4] #返回对应symbol

def find_newest_file(directory):
    # 确保提供的路径存在且是一个目录
    if not os.path.isdir(directory):
        print("提供的路径不是一个有效的目录")
        return None

    # 初始化最新时间和最新文件路径
    newest_time = 0
    newest_file = None

    # 遍历目录中的所有文件和文件夹
    for item in os.listdir(directory):
        full_path = os.path.join(directory, item)
        # 确保是一个文件而不是文件夹
        if os.path.isfile(full_path):
            # 获取文件的修改时间
            file_time = os.path.getmtime(full_path)
            # 检查这个文件的时间是否是最新的
            if file_time > newest_time:
                newest_time = file_time
                newest_file = full_path

    return newest_file

def get_signals(symbol,interval,max_candles):
    global print_list
    print(symbol)
    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    df = get_cur_price(symbol, '4h', now, max_candles)
    #df_1d=get_cur_price(symbol, '1d', now, max_candles)
    #df = wave_strategy_lor(df)
    df = wave_trend(df)
    # 寻找最后一个信号的索引
    last_short_index = list(np.where(df['oper_signal'].to_numpy() == -1))[0][-1]
    last_long_index = list(np.where(df['oper_signal'].to_numpy() == 1))[0][-1]
    if not len(list(np.where(df['oper_signal'].to_numpy() == 10))[0])==0:
        last_stop_index = list(np.where(df['oper_signal'].to_numpy() == 10))[0][-1]
    else:
        last_stop_index = 0
    cur_ts = pd.to_datetime(now, origin="1970-01-01 08:00:00", unit='ms')
    last_signal_idx=max(last_long_index, last_short_index,last_stop_index)
    last_signal_ts=df['close_time'].values[last_signal_idx]
    if (cur_ts - last_signal_ts) < timedelta(
            hours=8):  # 判断最后一次信号是否距离现在在12h之内
        if last_short_index==last_signal_idx:
            if not symbol in trading_list:
                print_str = ("Symbol:%s, now:%s last_short:%s" %
                             (symbol, str(cur_ts)[:19], str(df['close_time'].to_list()[last_short_index])[:19]))
                print(f"{bcolors.FAIL}%s{bcolors.ENDC}" % print_str) # print with red
                print_list.append(print_str)
        elif last_long_index==last_signal_idx:
            if not symbol in trading_list:
                print_str = ("Symbol:%s, now:%s last_long:%s" %
                             (symbol, str(cur_ts)[:19],  str(df['close_time'].to_list()[last_long_index])[:19]))
                print(f"{bcolors.OKGREEN}%s{bcolors.ENDC}" % print_str) # print with green
                print_list.append(print_str)
        else:
            if symbol in trading_list:
                print_str = ("Symbol:%s, now:%s last_stop:%s" %
                             (symbol, str(cur_ts)[:19],  str(df['close_time'].to_list()[last_stop_index])[:19]))
                print(f"{bcolors.OKBLUE}%s{bcolors.ENDC}" % print_str) # print with blue
                print_list.append(print_str)

if __name__ == '__main__':
    global print_list
    print_list=[]
    symbols=coin_whole_list
    # trading_list 主要用于过滤显示的信号，没有在list里的做多做空信号会显示出来，在list里的平仓信号会显示出来，其余不显示
    record_path='C:\\trade\\results\\trading_record\\'
    #record_file=record_path+"2024-09-16 13_38_08.json"
    record_file=find_newest_file(record_path)
    with open(record_file, 'r') as file:
        trading_list = json.load(file)
    interval="4h"
    max_candles=1000
    failed_list=[]
    #symbols=['HBARUSDT','ICPUSDT']
    for symbol in symbols:
        #get_signals(symbol, interval, max_candles)
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
            try:  # 如果网络失败就计入failed_list里 后面再重新跑
                get_signals(symbol,interval,max_candles)
            except:
                print("Running %s Failed!" % symbol)
                failed_list2.append(symbol)
        failed_list=failed_list2
        tries+=1
        if tries>20: #超过20次尝试如果还没跑出来就不要了
            break
    # 打印结果
    trading_dict={'buy':{},'sell':{}}
    for idx,print_str in enumerate(print_list):
        if "long" in print_str:
            print(f"%d. {bcolors.OKGREEN}%s{bcolors.ENDC}" % (idx+1, print_str)) # print with green
            trading_dict['buy'][idx+1]=get_symbol(print_str)
        elif "short" in print_str:
            print(f"%d. {bcolors.FAIL}%s{bcolors.ENDC}" % (idx + 1, print_str)) # print with red
            trading_dict['buy'][idx+1] = get_symbol(print_str)
        else:
            print(f"%d. {bcolors.OKBLUE}%s{bcolors.ENDC}" % (idx + 1, print_str))  # print with blue
            trading_dict['sell'][idx+1] = get_symbol(print_str)
    buy_list_str = input("Input Buy List:")
    if buy_list_str == '':
        buy_list=[]
    else:
        buy_list = [int(num) for num in buy_list_str.split(',')]
    sell_list_str = input("Input Sell List:")
    if sell_list_str=='':
        sell_list=[]
    else:
        sell_list = [int(num) for num in sell_list_str.split(',')]
    # 添加买入的单，删除卖出的单
    for trading_id in buy_list:
        symbol = trading_dict['buy'][trading_id]
        trading_list.append(symbol)
    for trading_id in sell_list:
        symbol = trading_dict['sell'][trading_id]
        trading_list.remove(symbol)
    print('Trading List:')
    print(trading_list)

    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    cur_ts = pd.to_datetime(now, origin="1970-01-01 08:00:00", unit='ms')
    record_name='%s.json'%str(cur_ts)[:19].replace(":", "_")
    # 保存当前交易状态，方便下次调用
    with open(record_path+record_name, 'w') as f:
        json.dump(trading_list, f, indent=4)