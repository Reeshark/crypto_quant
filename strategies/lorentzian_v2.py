import numpy as np
import pandas as pd
from get_factors import *
from visual.plot import plot_wave
import os

# status：
# 1：正在开多
# 0.5：临时看空
# 0：观望
# -0.5：临时看多
# -1：正在开空
#
# 整体过程：观望-开多-临时看空-返场-临时看空-结束(开空)-临时看多-返场-临时看多-结束(开多)
# 			做多-不做-----做多--不做------做空-------不做------做空-不做------做多
#
# 1.观望时：可以开多或开空
#
# 1.1开多条件：(lor信号多) || (prediction>=6) && 波浪趋势蓝色 && 波浪趋势<0
# 1.2开空条件：(lor信号空) || (prediction<=-6) && 波浪趋势粉色 && 波浪趋势>0
#
# 2.开多时：可以临时退场或结束交易
#
# 2.1 临时退场：lor信号空 || 1h lor 信号空 || ((prediction<0) && 波浪趋势粉色 && 波浪趋势处于高位)
# 2.2 退场后返场：((prediction>2) && 波浪趋势预判下一时刻或已经蓝色)
# 2.3 结束交易：出现开空条件时
#
# 3.开空时：可以临时退场或结束交易
#
# 3.1 临时退场：lor信号多 || 1h lor信号多 || ((prediction>0) && 波浪趋势蓝色 && 波浪趋势处于低位)
# 3.2 退场后返场：((prediction<-2) && 波浪趋势预判下一时刻或已经粉色)
# 3.3 结束交易：出现开多条件时
def wave_strategy(df):
    df= calculate_wave(df, src_type='hlc3', clen=10, alen=21, slen=4)
    df=calculate_macd(df)
    df=calculate_lorentzian(df)
    status=0
    status_list=[]
    strategy_signal=[]
    for index, row_info in enumerate(df.iterrows()):
        row=row_info[1]
        if status==0: #观望，等待多或空信号
            #开多条件：(lor信号多) | | (prediction >= 6) & & 波浪趋势蓝色 & & 波浪趋势 < 0
            if row['lor_signal']==1 or \
                (row['prediction']>=6 and row['wave_o']>row['wave_s'] and row['wave_o']<0):
                strategy_signal.append(1)
                status=1
                status_list.append(status)
                continue
            #开空条件：(lor信号空) | | (prediction <= -6) & & 波浪趋势粉色 & & 波浪趋势 > 0
            elif row['lor_signal'] == -1 or \
                        (row['prediction'] <= -6 and row['wave_o'] < row['wave_s'] and row['wave_o'] > 0):
                strategy_signal.append(-1)
                status=-1
                status_list.append(status)
                continue
        elif status==1: #持有多，等待临时或永久平仓
            #结束交易：出现开空条件时,由多转空
            if row['lor_signal'] == -1 or \
                        (row['prediction'] <= -6 and row['wave_o'] < row['wave_s'] and row['wave_o'] > 0):
                strategy_signal.append(-1)
                status=-1
                status_list.append(status)
                continue
            #临时退场，出现退场信号时终止交易：(prediction<0) && 波浪趋势粉色 && 波浪趋势处于高位
            elif row['prediction'] < 0 and row['wave_o'] < row['wave_s'] and row['wave_o'] > 75:
                strategy_signal.append(0)
                status=0.5
                status_list.append(status)
                continue
        elif status==-1: #持有空，等待临时或永久平仓
            #结束交易：出现开多条件时
            if row['lor_signal']==1 or \
                (row['prediction']>=6 and row['wave_o']>row['wave_s'] and row['wave_o']<0):
                strategy_signal.append(0)
                status=0
                status_list.append(status)
                continue
            #临时退场，出现退场信号时终止交易：(prediction>0) && 波浪趋势蓝色 && 波浪趋势处于低位
            elif row['prediction'] > 0 and row['wave_o'] > row['wave_s'] and row['wave_o'] < -75:
                strategy_signal.append(0)
                status=-0.5
                status_list.append(status)
                continue
        elif status==0.5: #开多临时退场，等待永久退场或返场
            #结束交易：出现开多条件时
            if row['lor_signal'] == -1 or \
                        (row['prediction'] <= -6 and row['wave_o'] < row['wave_s'] and row['wave_o'] > 0):
                strategy_signal.append(-1)
                status=-1
                status_list.append(status)
                continue
            #返场：(prediction>2) && 波浪趋势预判下一时刻或已经蓝色
            elif row['prediction'] > 2 and row['wave_o'] > row['wave_s']:
                strategy_signal.append(1)
                status=1
                status_list.append(status)
                continue
        elif status==-0.5: #开空临时退场，等待永久退场或返场
            #结束交易：出现开多条件时
            if row['lor_signal']==1 or \
                (row['prediction']>=6 and row['wave_o']>row['wave_s'] and row['wave_o']<0):
                strategy_signal.append(1)
                status=1
                status_list.append(status)
                continue
            #返场：(prediction<-2) && 波浪趋势预判下一时刻或已经粉色
            elif row['prediction'] < -2 and row['wave_o'] < row['wave_s']:
                strategy_signal.append(-1)
                status=-1
                status_list.append(status)
                continue
        #没有任何信号出现，维持上一时刻
        if not len(strategy_signal)==0:
            strategy_signal.append(strategy_signal[-1])
        else:
            strategy_signal.append(0)
        status_list.append(status)
    df['strategy_signal'] = strategy_signal
    df['status']=status_list
    return df


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
def wave_strategy2(df,df_1d):
    df= calculate_wave(df, src_type='hlc3', clen=10, alen=21, slen=4)
    df=calculate_macd(df)
    df=calculate_lorentzian(df)
    # 获取1d的wave
    df_1d = calculate_wave(df_1d, src_type='hlc3', clen=10, alen=21, slen=4)
    # 预测未来wave值
    wave_h = df_1d['wave_h']
    wave_h_s1 = wave_h.shift(1)
    wave_h_s2 = wave_h.shift(2)
    wave_h_s3 = wave_h.shift(3)
    wave_h_pred = 7/4.0*wave_h_s1-0.5*wave_h_s2-0.25*wave_h_s3
    df_1d['wave_h_pred'] = wave_h_pred
    df=align_signals(df,df_1d)
    status=0
    status_list=[]
    strategy_signal=[] # 观望：0 做多：1 做空：-1
    oper_signal=[] # 新出做多信号：1 新出做空信号：-1 新出平仓信号(包含多空):10 其余：0
    for index, row_info in enumerate(df.iterrows()):
        row=row_info[1]
        if status==0: #观望，等待多或空信号
            #开多条件：大周期(1d)多 && ((lor信号多) || (prediction>=6) && 波浪趋势蓝色)
            if (row['wave_1d_h']>0 and
                    (row['lor_signal']==1 or (row['prediction']>=6 and row['wave_h']>0))):
                strategy_signal.append(1)
                oper_signal.append(1)
                status=1
                status_list.append(status)
                continue
            #开空条件：大周期(1d)空 && ((lor信号空) || (prediction<=-6) && 波浪趋势粉色)
            elif (row['wave_1d_h']<0 and
                    (row['lor_signal']==-1 or (row['prediction']<=-6 and row['wave_h']<0))):
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
                    (row['prediction'] < -4 and row['wave_h'] < 0 and row['wave_o'] > 0):
                    strategy_signal.append(0)
                    oper_signal.append(10)
                    status = 0.5
                    status_list.append(status)
                    continue
            # 大周期反转
            elif (row['wave_1d_h'])<0:
                #结束交易：出现开空条件时,由多转空
                if row['lor_signal']==-1 or (row['prediction']<=-6 and row['wave_h']<0):
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
                        (row['prediction'] > 4 and row['wave_h'] > 0 and row['wave_o'] < 0):
                    strategy_signal.append(0)
                    oper_signal.append(10)
                    status = -0.5
                    status_list.append(status)
                    continue
            # 大周期反转
            elif (row['wave_1d_h']) > 0:
                # 结束交易：出现开多条件时,由空转多
                if row['lor_signal'] == 1 or (row['prediction'] >= 6 and row['wave_h'] > 0):
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
                    (row['prediction']>=2 and row['wave_h']>0):
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
                if row['lor_signal'] == -1 or (row['prediction'] <= -6 and row['wave_h'] < 0):
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
                        (row['prediction'] <= -2 and row['wave_h'] < 0):
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
                if row['lor_signal'] == 1 or (row['prediction'] >= 6 and row['wave_h'] > 0):
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


def wave_strategy3(df):
    buy_thresh,sell_thresh,return_thresh = 4,9,0
    df= calculate_wave(df, src_type='hlc3', clen=10, alen=21, slen=4)
    df=calculate_macd(df)
    df=calculate_lorentzian(df)
    df = calculate_wave_1d(df, src_type='hl2', clen=60, alen=30, slen=25)

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

def wave_strategy4(df):
    buy_thresh,sell_thresh,return_thresh = 4,2,0
    df= calculate_wave(df, src_type='hlc3', clen=10, alen=21, slen=4)
    df=calculate_macd(df)
    df=calculate_lorentzian(df)
    df = calculate_wave_1d(df, src_type='hl2', clen=60, alen=30, slen=25)

    status=0
    status_list=[]
    strategy_signal=[] # 观望：0 做多：1 做空：-1
    oper_signal=[] # 新出做多信号：1 新出做空信号：-1 新出平仓信号(包含多空):10 其余：0
    for index, row_info in enumerate(df.iterrows()):
        row=row_info[1]
        if status==0: #观望，等待多或空信号
            #开多条件：大周期(1d)多 && ((lor信号多) || (prediction>=6) && 波浪趋势蓝色)
            if (
                    (row['lor_signal']==1 or (row['prediction']>=buy_thresh and row['wave_h']>0))):
                strategy_signal.append(1)
                oper_signal.append(1)
                status=1
                status_list.append(status)
                continue
            #开空条件：大周期(1d)空 && ((lor信号空) || (prediction<=-6) && 波浪趋势粉色)
            elif (
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

def long_signal(row,buy_thresh=2):
    # if (row['wave_1d_h']>-10 and row['wave_h']>-5 and row['wave_h']<20 and
    #                 (row['lor_signal']==1 or (row['prediction']>=buy_thresh and row['wave_h']>0))):
    # if row['lor_signal']==1 or (row['prediction']>=buy_thresh and row['wave_h']>0):
    # if row['lor_signal'] == 1:
    if row['lor_signal'] == 1:
    # if (row['wave_h'] > 5 and row['wave_h'] < 20 and
    #             (row['lor_signal'] == 1 or (row['prediction'] >= buy_thresh and row['wave_h'] > 0))):
        return True
    else:
        return False

def short_signal(row,buy_thresh=-2):
    # if (row['wave_1d_h']<10 and row['wave_h']<5 and row['wave_h']>-20 and
    #                 (row['lor_signal']==-1 or (row['prediction']<=-buy_thresh and row['wave_h']<0))):
    # if row['lor_signal']==-1 or (row['prediction']<=-buy_thresh and row['wave_h']<0):
    if row['lor_signal']==-1:
    # if row['lor_signal'] == -1:
    # if (row['wave_h']<-5 and row['wave_h']>-20 and
    #                 (row['lor_signal']==-1 or (row['prediction']<=-buy_thresh and row['wave_h']<0))):
        return True
    else:
        return False

def long_sell(row,sell_thresh):
    #if row['lor_signal'] == -1 or row['wave_h'] < -7 or row['prediction'] < sell_thresh:
    if row['lor_signal'] == -1:
        return True
    else:
        return False

def short_sell(row,sell_thresh):
    #if row['lor_signal'] == 1 or row['wave_h'] > 7 or row['prediction'] > -sell_thresh:
    if row['lor_signal'] == 1:
        return True
    else:
        return False

def long_return(row,return_thresh):
    if row['lor_signal']==1 or (row['prediction']>=return_thresh and row['wave_h']>0):
        return True
    else:
        return False

def short_return(row,return_thresh):
    if row['lor_signal']==-1 or (row['prediction']<=-return_thresh and row['wave_h']<0):
        return True
    else:
        return False
def wave_strategy5(df,cfg):
    type,clen,alen,slen,buy_thresh,sell_thresh,return_thresh=(
        cfg['type'],cfg['clen'],cfg['alen'],cfg['slen'],cfg['buy_thresh'],cfg['sell_thresh'],cfg['return_thresh'])
    df= calculate_wave(df, src_type='hlc3', clen=10, alen=21, slen=4)
    df=calculate_macd(df)
    df=calculate_lorentzian(df)
    df = calculate_wave_1d(df, src_type=type, clen=clen, alen=alen, slen=slen)

    status=0
    status_list=[]
    strategy_signal=[] # 观望：0 做多：1 做空：-1
    oper_signal=[] # 新出做多信号：1 新出做空信号：-1 新出平仓信号(包含多空):10 其余：0
    for index, row_info in enumerate(df.iterrows()):
        row=row_info[1]
        if status==0: #观望，等待多或空信号
            #开多条件：大周期(1d)多 && ((lor信号多) || (prediction>=6) && 波浪趋势蓝色)
            if long_signal(row,buy_thresh):
                strategy_signal.append(1)
                oper_signal.append(1)
                status=1
                status_list.append(status)
                continue
            #开空条件：大周期(1d)空 && ((lor信号空) || (prediction<=-6) && 波浪趋势粉色)
            elif short_signal(row,buy_thresh):
                strategy_signal.append(-1)
                oper_signal.append(-1)
                status=-1
                status_list.append(status)
                continue
        elif status==1: #持有多，等待临时避险，或永久平仓(大周期反转)
            # 大周期没有反转
            if (row['wave_1d_h'])>=-10:
                #结束交易：出现开空条件时,由多转空
                if short_signal(row,buy_thresh):
                    strategy_signal.append(-1)
                    oper_signal.append(-1)
                    status=-1
                    status_list.append(status)
                    continue
                #临时退场：lor信号空 | | ((prediction < -4) & & 波浪趋势粉色 & & 波浪趋势 > 0)
                elif long_sell(row,sell_thresh):
                    strategy_signal.append(0)
                    oper_signal.append(10)
                    status = 0.5
                    status_list.append(status)
                    continue
            # 大周期反转
            elif (row['wave_1d_h'])<-10:
                #结束交易：出现开空条件时,由多转空
                if short_signal(row,buy_thresh):
                    strategy_signal.append(-1)
                    oper_signal.append(-1)
                    status=-1
                    status_list.append(status)
                    continue
                #退场观望，没出现信号时，退场观望等待后续信号
                elif long_sell(row,sell_thresh):
                    strategy_signal.append(0)
                    oper_signal.append(10)
                    status=0
                    status_list.append(status)
                    continue
        elif status == -1:  # 持有空，等待临时避险，或永久平仓(大周期反转)
            # 大周期没有反转
            if (row['wave_1d_h']) <= 10:
                # 结束交易：出现开多条件时,由空转多
                if long_signal(row,buy_thresh):
                    strategy_signal.append(1)
                    oper_signal.append(1)
                    status = 1
                    status_list.append(status)
                    continue
                # 临时退场：lor信号多 | | ((prediction > 4) & & 波浪趋势蓝色 & & 波浪趋势 < 0)
                elif short_sell(row,sell_thresh):
                    strategy_signal.append(0)
                    oper_signal.append(10)
                    status = -0.5
                    status_list.append(status)
                    continue
            # 大周期反转
            elif (row['wave_1d_h']) > 10:
                # 结束交易：出现开多条件时,由空转多
                if long_signal(row,buy_thresh):
                    strategy_signal.append(1)
                    oper_signal.append(1)
                    status = 1
                    status_list.append(status)
                    continue
                # 退场观望，没出现信号时，退场观望等待后续信号
                elif short_sell(row,sell_thresh):
                    strategy_signal.append(0)
                    oper_signal.append(10)
                    status = 0
                    status_list.append(status)
                    continue
        elif status==0.5: #开多临时退场，等待返场
            # 大周期没有反转
            if (row['wave_1d_h']) >= -10:
                #返场条件：((prediction>=2) && 波浪趋势预判下一时刻或已经蓝色)
                if long_return(row,return_thresh):
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
            elif (row['wave_1d_h'])<-10:
                # 结束交易：出现开空条件时,由多转空
                if short_signal(row,buy_thresh):
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
            if (row['wave_1d_h']) <= 10:
                # 返场条件：((prediction<=-2) && 波浪趋势预判下一时刻或已经粉色)
                if short_return(row,return_thresh):
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
            elif (row['wave_1d_h']) > 10:
                # 结束交易：出现开多条件时,由空转多
                if long_signal(row,buy_thresh):
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



def calculate_cur_profit(row,trade_price,highest_profit,profit_th,dir,cfg):
    if dir==1: #做多
        profit = (row['close_price'] - trade_price) / trade_price
        high_profit=(row['high_price'] - trade_price) / trade_price
    elif dir==-1: #做空
        profit = (trade_price-row['close_price']) / trade_price
        high_profit=(trade_price-row['low_price']) / trade_price

    if high_profit>highest_profit:
        highest_profit=high_profit
        profit_th = get_profit_threshold(highest_profit,cfg)
    return profit,highest_profit,profit_th

def wave_strategy_lor(df,cfg):
    df= calculate_wave(df, src_type='hlc3', clen=10, alen=21, slen=4)
    df = calculate_wave_1d(df, src_type='hlc3', clen=60, alen=30, slen=25)
    df=calculate_macd(df)
    #df=calculate_lorentzian(df)
    buy_thresh = 8
    status=0
    status_list=[]
    strategy_signal=[] # 观望：0 做多：1 做空：-1
    oper_signal=[] # 新出做多信号：1 新出做空信号：-1 新出平仓信号(包含多空):10 其余：0
    profit_list=[]
    highest_profit_list=[]
    profit_th_list=[]
    for index, row_info in enumerate(df.iterrows()):
        row=row_info[1]
        if status==0: #观望，等待多或空信号
            #开多条件：大周期(1d)多 && ((lor信号多) || (prediction>=6) && 波浪趋势蓝色)
            if long_signal(row,buy_thresh):
                strategy_signal.append(1)
                oper_signal.append(1)
                status=1
                status_list.append(status)
                profit=0
                highest_profit=0
                profit_th=get_profit_threshold(highest_profit,cfg)
                trade_price=row['close_price']
                profit_th_list.append(profit_th)
                profit_list.append(profit)
                highest_profit_list.append(highest_profit)
                continue
            #开空条件：大周期(1d)空 && ((lor信号空) || (prediction<=-6) && 波浪趋势粉色)
            elif short_signal(row,buy_thresh):
                strategy_signal.append(-1)
                oper_signal.append(-1)
                status=-1
                status_list.append(status)
                profit = 0
                highest_profit=0
                profit_th=get_profit_threshold(highest_profit,cfg)
                trade_price = row['close_price']
                profit_th_list.append(profit_th)
                profit_list.append(profit)
                highest_profit_list.append(highest_profit)
                continue
        elif status==1: #持有多，等待临时避险，或永久平仓(大周期反转)
            #计算收益率，最高收益，止盈止损阈值
            profit, highest_profit, profit_th=calculate_cur_profit(row,trade_price,highest_profit,profit_th,dir=1,cfg=cfg)
            #结束交易：出现开空条件时,由多转空
            if short_signal(row,buy_thresh):
                strategy_signal.append(-1)
                oper_signal.append(-1)
                status=-1
                status_list.append(status)
                profit = 0
                highest_profit=0
                profit_th=get_profit_threshold(highest_profit,cfg)
                profit_th_list.append(profit_th)
                profit_list.append(profit)
                highest_profit_list.append(highest_profit)
                continue
            #止盈止损:
            if profit<=profit_th:
                strategy_signal.append(0)
                oper_signal.append(0)
                status=0
                status_list.append(status)
                profit_th_list.append(profit_th)
                profit_list.append(profit)
                highest_profit_list.append(highest_profit)
                profit = 0
                highest_profit=0
                profit_th=get_profit_threshold(highest_profit,cfg)
                continue
        elif status == -1:  # 持有空，等待临时避险，或永久平仓(大周期反转)
            #计算收益率，最高收益，止盈止损阈值
            profit, highest_profit, profit_th=calculate_cur_profit(row,trade_price,highest_profit,profit_th,dir=-1,cfg=cfg)
            if long_signal(row,buy_thresh):
                strategy_signal.append(1)
                oper_signal.append(1)
                status = 1
                status_list.append(status)
                profit = 0
                highest_profit=0
                profit_th=get_profit_threshold(highest_profit,cfg)
                profit_th_list.append(profit_th)
                profit_list.append(profit)
                highest_profit_list.append(highest_profit)
                continue
            #止盈止损:
            if profit<=profit_th:
                strategy_signal.append(0)
                oper_signal.append(0)
                status=0
                status_list.append(status)
                profit_th_list.append(profit_th)
                profit_list.append(profit)
                highest_profit_list.append(highest_profit)
                profit = 0
                highest_profit=0
                profit_th=get_profit_threshold(highest_profit,cfg)
                continue
        #没有任何信号出现，维持上一时刻
        if not len(strategy_signal)==0:
            strategy_signal.append(strategy_signal[-1])
        else: #起始帧
            strategy_signal.append(0)
            profit=0
            highest_profit = 0
            profit_th = get_profit_threshold(highest_profit,cfg)
        oper_signal.append(0)
        status_list.append(status)
        profit_th_list.append(profit_th)
        profit_list.append(profit)
        highest_profit_list.append(highest_profit)
    df['strategy_signal'] = strategy_signal
    df['oper_signal'] = oper_signal
    df['status']=status_list
    df['profit']=profit_list
    df['highest_profit']=highest_profit_list
    df['profit_th']=profit_th_list
    return df

import pandas as pd

def dynamic_stop_loss_profit(df, stop_float, profit_table):
    # 初始化止盈价格和止损价格
    take_profit_prices = {}
    stop_loss_prices = {}

    # 遍历DataFrame
    for index, row in df.iterrows():
        if row['oper_signal'] == 1:  # 做多
            # 计算止盈价格
            profit = 0
            for profit_threshold, profit_setting in profit_table.items():
                if profit < profit_threshold:
                    profit = row['close'] * profit_setting / 100
                    take_profit_prices[index] = profit
                else:
                    break
            # 计算止损价格
            stop_loss_price = row['close'] * (1 - stop_float)
            stop_loss_prices[index] = stop_loss_price
        elif row['oper_signal'] == -1:  # 做空
            # 计算止盈价格
            profit = 0
            for profit_threshold, profit_setting in profit_table.items():
                if profit < profit_threshold:
                    profit = row['close'] * (1 + profit_setting / 100)
                    take_profit_prices[index] = profit
                else:
                    break
            # 计算止损价格
            stop_loss_price = row['close'] * (1 + stop_float)
            stop_loss_prices[index] = stop_loss_price

    # 确定是否达到止盈或止损
    for index, row in df.iterrows():
        if row['oper_signal'] == 1:  # 做多
            if row['close'] >= take_profit_prices.get(index, row['close']):  # 达到止盈
                df.at[index, 'signal_stop'] = 2
            elif row['close'] <= stop_loss_prices.get(index, row['close']):  # 达到止损
                df.at[index, 'signal_stop'] = -2
        elif row['oper_signal'] == -1:  # 做空
            if row['close'] <= take_profit_prices.get(index, row['close']):  # 达到止盈
                df.at[index, 'signal_stop'] = 2
            elif row['close'] >= stop_loss_prices.get(index, row['close']):  # 达到止损
                df.at[index, 'signal_stop'] = -2

    return df

# 示例用法
# 假设df是您的DataFrame
# stop_float = 0.03
# profit_table = {3: 0, 5: 2, 10: 5}
# df = dynamic_stop_loss_profit(df, stop_float, profit_table)

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

def calculate_stat(df):
    loss_list=[]
    return_list=[]
    max_loss=0
    max_return=0
    status=0
    open_price=0
    for index, row_info in enumerate(df.iterrows()):
        lor_signal=df['lor_signal'].values[index]
        cur_price = df['close_price'].values[index]
        if lor_signal==1: #出现做多信号
            status=1
            max_loss = 0
            max_return = 0
            open_price=cur_price
            loss_list.append(0)
            return_list.append(0)
            continue
        if lor_signal==-1: #出现做空信号
            status=-1
            max_loss = 0
            max_return = 0
            open_price=cur_price
            loss_list.append(0)
            return_list.append(0)
            continue
        if status==0: #起始状态
            loss_list.append(0)
            return_list.append(0)
            continue
        elif status==1: #做多状态
            cur_return=(df['high_price'].values[index]-open_price)/open_price
            cur_loss = (df['low_price'].values[index] - open_price)/open_price
            if cur_return>max_return:
                max_return=cur_return
            if cur_loss<max_loss:
                max_loss=cur_loss
            loss_list.append(max_loss)
            return_list.append(max_return)
            continue
        elif status==-1: #做空状态
            cur_return=(open_price-df['low_price'].values[index])/open_price
            cur_loss = (open_price- df['high_price'].values[index])/open_price
            if cur_return>max_return:
                max_return=cur_return
            if cur_loss<max_loss:
                max_loss=cur_loss
            loss_list.append(max_loss)
            return_list.append(max_return)
            continue
    df['loss_list']=loss_list
    df['return_list']=return_list

    return df

def get_profit_threshold(highest_profit,cfg):
    v1,v2,v3,v4,v5,v6,v7,v8,v9=cfg
    if highest_profit<v1: #如果没达到1%盈利，则设置1.7%止损
        return v2
    elif highest_profit<v3: #1%-2%,设置0.5%止损
        return v4
    elif highest_profit<v5: #2%-5%,设置0.5*最高价止盈
        return highest_profit*v6
    elif highest_profit<v7: #5%-10%,设置0.6*最高价止盈
        return highest_profit*v8
    else: #大于10%时，设置0.75*最高价止盈
        return highest_profit*v9

def get_profit_threshold2(highest_profit):
    if highest_profit<0.01: #如果没达到1%盈利，则设置1.7%止损
        return -0.017
    elif highest_profit<0.03: #1%-2%,设置0.5%止损
        return 0.000
    elif highest_profit<0.06: #2%-5%,设置0.5*最高价止盈
        return highest_profit*0.3
    elif highest_profit<0.1: #5%-10%,设置0.6*最高价止盈
        return highest_profit*0.5
    else: #大于10%时，设置0.75*最高价止盈
        return highest_profit*0.65


def calculate_sharpe_ratio(df, risk_free_rate=0.02):
    balances = df['balance']
    # 计算每个时间点的回报率
    returns = np.diff(balances) / balances[:-1]

    # 计算预期回报率（即平均回报率）
    expected_return = np.mean(returns) * 365  # 假设一年有252个交易日

    # 计算标准差（风险）
    std_dev = np.std(returns) * np.sqrt(365)  # 年化标准差

    # 计算夏普率
    sharpe_ratio = (expected_return - risk_free_rate) / std_dev

    return sharpe_ratio

def calculate_max_drawdown(df):
    balance = df['balance']
    cumulative_max = balance.cummax()
    # 计算回撤
    drawdowns = (cumulative_max - balance) / cumulative_max
    # 找到最大回撤
    max_drawdown = drawdowns.max()
    return max_drawdown * 100

if __name__ == '__main__':
    import copy
    symbol = 'BTCUSDT'
    interval = '4h'
    num_candles =4000
    df = pd.read_csv(f"D:\\Trade\\data\\{symbol}_{interval}_spot.csv")
    df = df[-num_candles:]
    df['open_time'] = pd.to_datetime(df['open_time'], origin="1970-01-01 08:00:00", unit='ms')
    df['close_time'] = pd.to_datetime(df['close_time'], origin="1970-01-01 08:00:00", unit='ms')
    df_init = calculate_lorentzian(df)
    max_balance=0
    # for v1 in [0.04,0.09,0.15]: #达到可以保底的盈利阈值
    #     for v2 in [-0.06,-0.1,-0.15,-0.2]: #止损百分比(没达到v1的要设止损)
    #         for v3 in [0.13,0.18,0.24]: #达到可以盈利的盈利阈值(第一档)
    #             print("%.3f,%.3f,%.3f"%(v1,v2,v3))
    #             for v4 in [0]: #保底的盈利百分比(没达到v3的要设保底)
    #                 for v5 in [0.3,0.4,0.5]: #第二档的盈利阈值
    #                     for v6 in [0.3,0.5,0.7]: #第一档止盈的比例
    #                         for v7 in [0.5,0.6,0.7]: #第三档盈利阈值
    #                             for v8 in [0.3,0.5,0.7]: #第二档止盈的比例
    #                                 for v9 in [0.5,0.7,0.9,1]: #第三档的止盈比例
    for v1 in [0.005, 0.01, 0.02]:  # 达到可以保底的盈利阈值
        for v2 in [-0.005, -0.01, -0.02]:  # 止损百分比(没达到v1的要设止损)
            for v3 in [0.07, 0.12, 0.17]:  # 达到可以盈利的盈利阈值(第一档)
                print("%.3f,%.3f,%.3f" % (v1, v2, v3))
                for v4 in [0]:  # 保底的盈利百分比(没达到v3的要设保底)
                    for v5 in [0.15, 0.25, 0.4]:  # 第二档的盈利阈值
                        for v6 in [0.3, 0.5, 0.7]:  # 第一档止盈的比例
                            for v7 in [0.2, 0.5, 0.7]:  # 第三档盈利阈值
                                for v8 in [0.3, 0.5, 0.7]:  # 第二档止盈的比例
                                    for v9 in [0.5, 0.7, 0.9]:  # 第三档的止盈比例
                                        if v3<v1 or v5<v3 or v7<v5:
                                            continue
                                        cfg=[v1,v2,v3,v4,v5,v6,v7,v8,v9]
                                        #cfg=[v1*2,v2*2,v3*2,v4*2,v5*2,v6,v7*2,v8,v9]
                                        df=copy.deepcopy(df_init)
                                        df = wave_strategy_lor(df, cfg)
                                        stop_float = 0.03
                                        profit_table = {3: 0, 5: 2, 10: 5}
                                        #df=dynamic_stop_loss_profit(df, stop_float, profit_table)
                                        df = calculate_stat(df)
                                        df=calculate_profit(df,transaction_fee=0.00045)

                                        #print(df['balance'].values[-1])
                                        dump_root="C:\\trade\\results\wave_trading\\24.11.19\\"
                                        os.makedirs(dump_root, exist_ok=True)
                                        # num_files=len(os.listdir(dump_root))
                                        # plot_wave(df,symbol,interval='4h',dump_file=dump_root+'test%d.pdf'%num_files)
                                        balance = df['balance']
                                        min_balance = min(balance)
                                        max_drawdown=calculate_max_drawdown(df)
                                        # 计算年化收益
                                        time_diff = pd.to_timedelta(df['close_time'].values[-1] - df['open_time'].values[0],
                                                                    unit='s')
                                        # 计算夏普率
                                        sharpe=calculate_sharpe_ratio(df)
                                        profit = (balance.iloc[-1] - balance.iloc[0]) / balance.iloc[0]
                                        annual_profit = profit / time_diff.total_seconds() * (86400 * 365) * 100
                                        if balance.iloc[-1]>=max_balance:
                                            print(cfg)
                                            print('Final Balance:%.3f, Min Balance:%.3f, Max Drawdown:%.3f Sharpe:%.3f, Annual_profit:%.3f%%' % (balance.iloc[-1], min_balance, max_drawdown,sharpe, annual_profit))
                                            max_balance=balance.iloc[-1]
