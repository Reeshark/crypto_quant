import numpy as np
import pandas as pd
from get_factors import *
from visual.plot import plot_wave
import os
from coin_list import coin_whole_list

# status：
# 1：正在开多->做多
# 0.5：开多临时避险->不做
# 0：观望->不做
# -0.5：开空临时避险->不做
# -1：正在开空->做空

# 整体过程：大周期多：观望-开多-临时避险-返场-结束
#         大周期空：观望-开空-临时避险-返场-结束

# 1.观望时：可以开多或开空

# 1.1开多条件：大周期(1d)多 && ((lor信号多) || (prediction>=6) && 波浪趋势蓝色)
# 1.2开空条件：大周期(1d)空 && ((lor信号空) || (prediction<=-6) && 波浪趋势粉色)

# 2.开多时：可以临时退场避险或返场
#
# 2.1 临时退场：lor信号空 || ((prediction<-4) && 波浪趋势粉色 && 波浪趋势>0)
# 2.2 退场后返场：((prediction>=2) && 波浪趋势预判下一时刻或已经蓝色)


# 3.开空时：可以临时退场避险或返场
#
# 3.1 临时退场：lor信号多 || ((prediction>4) && 波浪趋势蓝色 && 波浪趋势<0)
# 3.2 退场后返场：((prediction<=-2) && 波浪趋势预判下一时刻或已经粉色)

def align_signals(df,df_1d):
    # 获取两周期overlap部分
    time_start=max(df['open_time'].values[0],df_1d['open_time'].values[0])
    time_end=min(df['close_time'].values[-1],df_1d['close_time'].values[-1])
    df = df.loc[df['open_time'] >= time_start]
    df = df.loc[df['close_time'] <= time_end]
    # 1d要尽量包裹住4h
    df_1d = df_1d.loc[df_1d['close_time'] >= time_start]
    df_1d = df_1d.loc[df_1d['open_time'] <= time_end]
    wave_1d=[]
    index_1d=0
    # 将对应时段的1d wave指标填入4h中
    for index_4h in range(len(df)):  # 遍历所有第三级区间数据
        start_1d=df_1d['open_time'].values[index_1d]
        end_1d=df_1d['close_time'].values[index_1d]
        start_4h=df['open_time'].values[index_4h]
        end_4h=df['close_time'].values[index_4h]
        if not (start_4h>=start_1d and end_4h<=end_1d):
            index_1d+=1
        wave_1d.append(df_1d['wave_h'].values[index_1d])
    df['wave_1d_h']=wave_1d
    #df['wave_1d_h']=df['wave_1d_h'].shift(6)
    return df


def wave_strategy3(df,cfg):
    type,clen,alen,slen,buy_thresh,sell_thresh,return_thresh=(
        cfg['type'],cfg['clen'],cfg['alen'],cfg['slen'],cfg['buy_thresh'],cfg['sell_thresh'],cfg['return_thresh'])
    df= calculate_wave(df, src_type='hlc3', clen=10, alen=21, slen=4)
    df=calculate_macd(df)
    df=calculate_lorentzian(df)
    df = calculate_wave_1d(df, src_type=type, clen=clen, alen=alen, slen=slen)
    #df=align_signals(df,df_1d)

    status=0
    status_list=[]
    strategy_signal=[] # 观望：0 做多：1 做空：-1
    oper_signal=[] # 新出做多信号：1 新出做空信号：-1 新出平仓信号(包含多空):10 其余：0
    for index, row_info in enumerate(df.iterrows()):
        row=row_info[1]
        if status==0: #观望，等待多或空信号
            #开多条件：大周期(1d)多 && ((lor信号多) || (prediction>=6) && 波浪趋势蓝色)
            if (row['wave_1d_h']>0 and
                    (row['lor_signal']==1 or (row['prediction']>=buy_thresh and row['wave_h']>0))):
                strategy_signal.append(1)
                oper_signal.append(1)
                status=1
                status_list.append(status)
                continue
            #开空条件：大周期(1d)空 && ((lor信号空) || (prediction<=-6) && 波浪趋势粉色)
            elif (row['wave_1d_h']<0 and
                    (row['lor_signal']==-1 or (row['prediction']<=-buy_thresh and row['wave_h']<0))):
                strategy_signal.append(-1)
                oper_signal.append(-1)
                status=-1
                status_list.append(status)
                continue
        elif status==1: #持有多，等待临时避险，或永久平仓(大周期反转)
            # 大周期没有反转
            if (row['wave_1d_h'])>0:
                #临时退场：lor信号空 | | ((prediction < -4) & & 波浪趋势粉色 & & 波浪趋势 > 0)
                if row['lor_signal']==-1 or \
                    (row['prediction'] < -sell_thresh and row['wave_h'] < 0 and row['wave_o'] > 0):
                    strategy_signal.append(0)
                    oper_signal.append(10)
                    status = 0.5
                    status_list.append(status)
                    continue
            # 大周期反转
            elif (row['wave_1d_h'])<0:
                #结束交易：出现开空条件时,由多转空
                if row['lor_signal']==-1 or (row['prediction']<=-buy_thresh and row['wave_h']<0):
                    strategy_signal.append(-1)
                    oper_signal.append(-1)
                    status=-1
                    status_list.append(status)
                    continue
                #退场观望，没出现信号时，退场观望等待后续信号
                else:
                    strategy_signal.append(0)
                    oper_signal.append(10)
                    status=0
                    status_list.append(status)
                    continue
        elif status == -1:  # 持有空，等待临时避险，或永久平仓(大周期反转)
            # 大周期没有反转
            if (row['wave_1d_h']) < 0:
                # 临时退场：lor信号多 | | ((prediction > 4) & & 波浪趋势蓝色 & & 波浪趋势 < 0)
                if row['lor_signal'] == 1 or \
                        (row['prediction'] > sell_thresh and row['wave_h'] > 0 and row['wave_o'] < 0):
                    strategy_signal.append(0)
                    oper_signal.append(10)
                    status = -0.5
                    status_list.append(status)
                    continue
            # 大周期反转
            elif (row['wave_1d_h']) > 0:
                # 结束交易：出现开多条件时,由空转多
                if row['lor_signal'] == 1 or (row['prediction'] >= buy_thresh and row['wave_h'] > 0):
                    strategy_signal.append(1)
                    oper_signal.append(1)
                    status = 1
                    status_list.append(status)
                    continue
                # 退场观望，没出现信号时，退场观望等待后续信号
                else:
                    strategy_signal.append(0)
                    oper_signal.append(10)
                    status = 0
                    status_list.append(status)
                    continue
        elif status==0.5: #开多临时退场，等待返场
            # 大周期没有反转
            if (row['wave_1d_h']) > 0:
                #返场条件：((prediction>=2) && 波浪趋势预判下一时刻或已经蓝色)
                if row['lor_signal']==1 or \
                    (row['prediction']>=return_thresh and row['wave_h']>0):
                    strategy_signal.append(1)
                    oper_signal.append(1)
                    status=1
                    status_list.append(status)
                    continue
                # 继续观望，没出现信号时，退场观望等待后续信号
                else:
                    strategy_signal.append(0)
                    oper_signal.append(0)
                    status = 0.5
                    status_list.append(status)
                    continue
            # 大周期反转
            elif (row['wave_1d_h'])<0:
                # 结束交易：出现开空条件时,由多转空
                if row['lor_signal'] == -1 or (row['prediction'] <= -buy_thresh and row['wave_h'] < 0):
                    strategy_signal.append(-1)
                    oper_signal.append(-1)
                    status = -1
                    status_list.append(status)
                    continue
                # 继续观望，没出现信号时，退场观望等待后续信号
                else:
                    strategy_signal.append(0)
                    oper_signal.append(0)
                    status = 0
                    status_list.append(status)
                    continue
        elif status == -0.5:  # 开多临时退场，等待返场
            # 大周期没有反转
            if (row['wave_1d_h']) < 0:
                # 返场条件：((prediction<=-2) && 波浪趋势预判下一时刻或已经粉色)
                if row['lor_signal'] == -1 or \
                        (row['prediction'] <= -return_thresh and row['wave_h'] < 0):
                    strategy_signal.append(-1)
                    oper_signal.append(-1)
                    status = -1
                    status_list.append(status)
                    continue
                # 继续观望，没出现信号时，退场观望等待后续信号
                else:
                    strategy_signal.append(0)
                    oper_signal.append(0)
                    status = -0.5
                    status_list.append(status)
                    continue
            # 大周期反转
            elif (row['wave_1d_h']) > 0:
                # 结束交易：出现开多条件时,由空转多
                if row['lor_signal'] == 1 or (row['prediction'] >= buy_thresh and row['wave_h'] > 0):
                    strategy_signal.append(1)
                    oper_signal.append(1)
                    status = 1
                    status_list.append(status)
                    continue
                # 继续观望，没出现信号时，退场观望等待后续信号
                else:
                    strategy_signal.append(0)
                    oper_signal.append(0)
                    status = 0
                    status_list.append(status)
                    continue
        #没有任何信号出现，维持上一时刻
        if not len(strategy_signal)==0:
            strategy_signal.append(strategy_signal[-1])
        else:
            strategy_signal.append(0)
        oper_signal.append(0)
        status_list.append(status)
    df['strategy_signal'] = strategy_signal
    df['oper_signal'] = oper_signal
    df['status']=status_list
    return df

def calculate_profit(df,balance=10000.0,transaction_fee=0.00045):
    cur_balance=[]
    transaction_fee_list=[]
    last_signal=0
    for index, row_info in enumerate(df.iterrows()):
        if index==0:
            cur_balance.append(balance)
            transaction_fee_list.append(0)
            continue
        last_price=df['close_price'].values[index-1]
        cur_price=df['close_price'].values[index]
        # 0 holding 1 long -1 short
        cur_signal=df['strategy_signal'].values[index-1]
        if cur_signal!=0 and last_signal==0: # new transaction -> transaction_fee
            profit=cur_signal*((cur_price-last_price)/last_price)*balance
            profit-=balance*transaction_fee
            transaction_fee_list.append(balance*(transaction_fee))
        elif cur_signal==0 and last_signal!=0: #
            profit=-(balance*(transaction_fee))
            transaction_fee_list.append(balance*(transaction_fee))
        else:
            profit = cur_signal * ((cur_price - last_price) / last_price) * balance
            transaction_fee_list.append(0)
        balance+=profit
        cur_balance.append(balance)
        last_signal=cur_signal
    df['balance']=cur_balance
    df['transaction_fee']=transaction_fee_list
    return df

if __name__ == '__main__':
    cfg={}
    #cfg['type'], cfg['clen'], cfg['alen'], cfg['slen'], cfg['buy_thresh'], cfg['sell_thresh'], cfg['return_thresh'])
    output_txt = 'C:\\trade\\results\wave_trading\\24.9.17\\'
    type_list=['hl2']
    clen_list=[60,80,100]
    alen_list=[30,45]
    slen_list=[25,30]
    buy_list=[4,6,8]
    sell_list=[0,2,4,6,9]
    return_list=[0,2,4]
    symbols = coin_whole_list
    for symbol in symbols:
        txt_file=output_txt+'%s.txt'%symbol
        if os.path.exists(txt_file):
            os.remove(txt_file)
        interval = '4h'
        if not os.path.exists(f"C:\\Trade\\data\\{symbol}_{interval}_spot.csv"):
            continue
        num_candles = 20000
        df = pd.read_csv(f"C:\\Trade\\data\\{symbol}_{interval}_spot.csv")
        df = df[-num_candles:]
        df['open_time'] = pd.to_datetime(df['open_time'], origin="1970-01-01 08:00:00", unit='ms')
        df['close_time'] = pd.to_datetime(df['close_time'], origin="1970-01-01 08:00:00", unit='ms')
        with open(txt_file, 'a+', encoding='utf-8') as file:
            for type in type_list:
                for alen in alen_list:
                    for clen in clen_list:
                        for slen in slen_list:
                            for buy_thresh in buy_list:
                                for sell_thresh in sell_list:
                                    for return_thresh in return_list:
                                        cfg['type'], cfg['clen'], cfg['alen'], cfg['slen'], cfg['buy_thresh'], cfg[
                                            'sell_thresh'], cfg['return_thresh']=type,clen,alen,slen,buy_thresh,sell_thresh,return_thresh
                                        df=wave_strategy3(df,cfg)
                                        df=calculate_profit(df,transaction_fee=0.00045)

                                        balance = df['balance']
                                        min_balance = min(balance)
                                        # 计算年化收益
                                        time_diff = pd.to_timedelta(df['close_time'].values[-1] - df['open_time'].values[0],
                                                                    unit='s')
                                        profit = (balance.iloc[-1] - balance.iloc[0]) / balance.iloc[0]
                                        annual_profit = profit / time_diff.total_seconds() * (86400 * 365) * 100
                                        print(cfg)
                                        file.write(str(cfg)+'\n')
                                        print('Final Balance:%.3f, Min Balance:%.3f, Annual_profit:%.3f%%'%(balance.iloc[-1],min_balance,annual_profit))
                                        file.write('Final Balance:%.3f, Min Balance:%.3f, Annual_profit:%.3f%%\n'%(balance.iloc[-1],min_balance,annual_profit))