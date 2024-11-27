import numpy as np
import pandas as pd
from visual.plot import plot_pair_trading
import os
from statsmodels.tsa.stattools import coint, adfuller

def pair_trading(df1,df2,symbols,spread_type='price_diff'):
    # 假设我们有两个加密货币的价格数据，以Pandas Series的形式给出
    # 这里使用随机数据作为示例
    crypto1=(df1['close_price']).to_numpy()
    crypto2 = (df2['close_price']).to_numpy()

    if spread_type=='simple':
        returns_crypto1 = (crypto1[1:] - crypto1[:-1]) / crypto1[:-1]
        returns_crypto2 = (crypto2[1:] - crypto2[:-1]) / crypto2[:-1]
        spread = returns_crypto1 - returns_crypto2
        weight=1
        # 计算SMA
        window_size = 20  # SMA窗口大小，可以根据需要调整
        sma = pd.Series(returns_crypto1).rolling(window=window_size).mean() - weight * pd.Series(
            returns_crypto2).rolling(window=window_size).mean()
    elif spread_type=='log':
        returns_crypto1 = np.log(crypto1 / np.roll(crypto1, 1)).dropna()
        returns_crypto2 = np.log(crypto2 / np.roll(crypto2, 1)).dropna()
        spread = returns_crypto1 - returns_crypto2
        weight=1
        # 计算SMA
        window_size = 20  # SMA窗口大小，可以根据需要调整
        sma = pd.Series(returns_crypto1).rolling(window=window_size).mean() - weight * pd.Series(
            returns_crypto2).rolling(window=window_size).mean()
    elif spread_type=='price_diff':
        # crypto1_mean=np.mean(crypto1)
        # crypto2_mean=np.mean(crypto2)
        weight=crypto1[0]/crypto2[0]
        spread = (crypto1 - weight*crypto2)[1:]
        returns_crypto1 =crypto1[1:]
        returns_crypto2 =crypto2[1:]
        # 计算SMA
        window_size = 20  # SMA窗口大小，可以根据需要调整
        sma = pd.Series(returns_crypto1).rolling(window=window_size).mean() - weight * pd.Series(
            returns_crypto2).rolling(window=window_size).mean()
    elif spread_type=='ratio':
        crypto1_mean=np.mean(crypto1)
        crypto2_mean=np.mean(crypto2)
        weight=crypto1_mean/crypto2_mean
        spread = ((crypto1/crypto2 - weight)/weight)[1:]
        # spread = (crypto1 / crypto2)[1:]
        returns_crypto1 =crypto1[1:]
        returns_crypto2 =crypto2[1:]
        # 计算SMA
        window_size = 20  # SMA窗口大小，可以根据需要调整
        sma = (pd.Series(returns_crypto1).rolling(window=window_size).mean()/pd.Series(
            returns_crypto2).rolling(window=window_size).mean()-weight)/weight
        # sma = pd.Series(returns_crypto1).rolling(window=window_size).mean()/pd.Series(
        #     returns_crypto2).rolling(window=window_size).mean()
    elif spread_type=='dyn_price_diff':
        weight_list=[]
        weight_ratio=0.05
        mean_length=100
        for i in range(len(crypto1)):
            if i==0:
                cur_weight=crypto1[i]/crypto2[i]
                weight_list.append(cur_weight)
            elif i<=mean_length:
                weight=np.mean(weight_list)
                cur_weight=crypto1[i]/crypto2[i]
                cur_weight=(1-weight_ratio)*weight+weight_ratio*cur_weight
                weight_list.append(cur_weight)
            else:
                weight=np.mean(weight_list[-mean_length:])
                cur_weight=crypto1[i]/crypto2[i]
                cur_weight=(1-weight_ratio)*weight+weight_ratio*cur_weight
                weight_list.append(cur_weight)
        # crypto1_mean=np.mean(crypto1)
        # crypto2_mean=np.mean(crypto2)
        #weight=crypto1[0]/crypto2[0]
        weight_list=np.array(weight_list)
        spread = (crypto1 - weight_list*crypto2)[1:]
        returns_crypto1 =crypto1[1:]
        returns_crypto2 =crypto2[1:]
        # 计算SMA
        window_size = 30  # SMA窗口大小，可以根据需要调整
        sma = pd.Series(returns_crypto1).rolling(window=window_size).mean() - weight_list[1:] * pd.Series(
            returns_crypto2).rolling(window=window_size).mean()





    # 计算标准差
    std_dev = pd.Series(spread).rolling(window=window_size).std()
    zscore=(spread-sma)/std_dev
    # 计算Bollinger带上下限
    bollinger_upper = sma + (2 * std_dev)
    bollinger_lower = sma - (2 * std_dev)

    df_pair=pd.DataFrame()
    df_pair['spread']=spread
    df_pair['bollinger_lower'] = bollinger_lower
    df_pair['bollinger_upper']=bollinger_upper
    df_pair['sma'] = sma
    df_pair['zscore'] = zscore
    # 生成交易信号
    # 如果spread超过上带，做空crypto1并做多crypto2
    # 如果spread低于下带，做多crypto1并做空crypto2
    # 注意：这里没有实现实际的交易逻辑，只是生成信号
    status=0
    signals_1=[]
    signals_2=[]
    adf_list=[]
    coint_list=[]
    record_price=0 #标记开单信号
    coint_length=500
    adf_threhold=0.1
    for idx,cur_spread in enumerate(spread):
        if idx>coint_length:
            #计算最近n根k线的稳定性
            pvalue_adf = adfuller(spread[max(idx-coint_length,0):idx])[1]
            coint_t, pvalue, crit_value = coint(crypto1[max(idx-coint_length,0):idx], crypto2[max(idx-coint_length,0):idx])
        else:
            pvalue_adf=1
            pvalue=1
        adf_list.append(pvalue_adf)
        coint_list.append(pvalue)
        if status==0: #等待信号
            if cur_spread>=bollinger_upper[idx] and pvalue_adf<=adf_threhold: #上穿信号
                status=1
                signals_1.append(-1)
                signals_2.append(1)
                record_price = cur_spread  # 标记开单信号
                continue
            elif cur_spread<=bollinger_lower[idx] and pvalue_adf<=adf_threhold: #下穿信号
                status=-1
                signals_1.append(1)
                signals_2.append(-1)
                record_price = cur_spread
                continue
            else: #无事发生
                signals_1.append(0)
                signals_2.append(0)
                continue
        elif status==1: #跟踪信号，等待终止条件
            # if cur_spread<sma[idx]: #归位均线
            #     status=0
            #     signals_1.append(0)
            #     signals_2.append(0)
            #     continue
            # if cur_spread<sma[idx] and cur_spread<record_price: #归位均线+保底
            #     status=0
            #     signals_1.append(0)
            #     signals_2.append(0)
            #     record_price = 0  # 标记开单信号
            #     continue
            # if cur_spread<=bollinger_lower[idx] and cur_spread<record_price: #下穿信号+保底
            #     status=-1
            #     signals_1.append(1)
            #     signals_2.append(-1)
            #     record_price = cur_spread  # 标记开单信号
            if cur_spread<=bollinger_lower[idx] and pvalue_adf<=adf_threhold: #下穿信号且稳定，直接反转
                status=-1
                signals_1.append(1)
                signals_2.append(-1)
            elif cur_spread<=bollinger_lower[idx] or pvalue_adf>=adf_threhold*2: #下穿但不稳定，平仓等待
                status=0
                signals_1.append(0)
                signals_2.append(0)
            else: #保持
                signals_1.append(-1)
                signals_2.append(1)
                continue
            # if cur_spread<=bollinger_lower[idx]: #下穿信号
            #     status=-1
            #     signals_1.append(1)
            #     signals_2.append(-1)
            # else: #保持
            #     signals_1.append(-1)
            #     signals_2.append(1)
            #     continue
        elif status==-1: #跟踪信号，等待终止条件
            # if cur_spread>sma[idx]: #归位均线
            #     status=0
            #     signals_1.append(0)
            #     signals_2.append(0)
            #     continue
            # if cur_spread>sma[idx] and cur_spread>record_price: #归位均线+保底
            #     status=0
            #     signals_1.append(0)
            #     signals_2.append(0)
            #     record_price = 0  # 标记开单信号
            #     continue
            # if cur_spread>=bollinger_upper[idx] and cur_spread>record_price: #上穿信号+保底
            #     status=1
            #     signals_1.append(-1)
            #     signals_2.append(1)
            #     record_price = cur_spread  # 标记开单信号
            #     continue
            if cur_spread>=bollinger_upper[idx] and pvalue_adf<=adf_threhold: #上穿信号且稳定，直接反转
                status=1
                signals_1.append(-1)
                signals_2.append(1)
                continue
            elif cur_spread>=bollinger_upper[idx] or pvalue_adf>=adf_threhold*2: #上穿但不稳定，平仓等待
                status=0
                signals_1.append(0)
                signals_2.append(0)
            else: #保持
                signals_1.append(1)
                signals_2.append(-1)
                continue
            # if cur_spread>=bollinger_upper[idx]: #上穿信号
            #     status=1
            #     signals_1.append(-1)
            #     signals_2.append(1)
            #     continue
            # else: #保持
            #     signals_1.append(1)
            #     signals_2.append(-1)
            #     continue
    # signals = np.where(spread > bollinger_upper, -1, 0)
    # signals += np.where(spread < bollinger_lower, 1, 0)
    df1['strategy_signal']=[0]+signals_1
    df1['return_rate'] = [0] + returns_crypto1.tolist()
    # signals = np.where(spread > bollinger_upper, 1, 0)
    # signals += np.where(spread < bollinger_lower,-1, 0)
    df2['strategy_signal']=[0]+signals_2
    df2['return_rate'] = [0] + returns_crypto2.tolist()
    df_pair['adf']=adf_list
    df_pair['coint']=coint_list
    #df_pair 补充第一行使其与df1 df2对齐
    first_row = df_pair.iloc[0].copy()
    # 将第一行的数据作为新行插入到最开始
    df_pair = pd.concat([pd.DataFrame([first_row], columns=df_pair.columns), df_pair], ignore_index=True)
    return df1,df2,df_pair



def get_overlapping(df1,df2):
    df1_start=min(df1['open_time'].values)
    df2_start=min(df2['open_time'].values)
    start=max(df1_start,df2_start)
    df1_end=max(df1['close_time'].values)
    df2_end=max(df2['close_time'].values)
    end=min(df1_end,df2_end)
    df1=df1[df1['open_time']>=start]
    df2 = df2[df2['open_time'] >= start]
    df1=df1[df1['close_time']<=end]
    df2 = df2[df2['close_time'] <= end]
    df1 = df1.reset_index(drop=True)
    df2 = df2.reset_index(drop=True)
    df1['open_time'] = pd.to_datetime(df1['open_time'], unit='ms')
    df1['close_time'] = pd.to_datetime(df1['close_time'], unit='ms')
    df2['open_time'] = pd.to_datetime(df2['open_time'], unit='ms')
    df2['close_time'] = pd.to_datetime(df2['close_time'], unit='ms')
    return df1,df2

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

def calculate_profit_pair(df1,df2,balance_ratio=[0.5,0.5],balance=10000.0,transaction_fee=0.00045):
    cur_balance1=[]
    cur_balance2 = []
    last_signal=0
    status=0 #0:空仓 1：多1空2 -1：空1多2
    vol1,vol2=0,0
    balance1=balance*balance_ratio[0] #按比例分配
    balance2=balance*balance_ratio[1]
    for index, row_info in enumerate(df1.iterrows()):
        if index==0:
            cur_balance1.append(balance1)
            cur_balance2.append(balance2)
            continue
        last_price1=df1['close_price'].values[index-1]
        cur_price1=df1['close_price'].values[index]
        last_price2=df2['close_price'].values[index-1]
        cur_price2=df2['close_price'].values[index]
        # 0 holding 1 long -1 short
        cur_signal=df1['strategy_signal'].values[index]
        if cur_signal==1 and last_signal!=1:#开多1空2
            balance=balance1+balance2 #两个币的资金池重新分配
            balance-=balance*transaction_fee #手续费(包含了两个币的)
            balance1=balance*balance_ratio[0]
            balance2 = balance * balance_ratio[1]
            vol1=balance1/cur_price1 #分到币1的币量
            vol2 = balance2 / cur_price2  # 分到币2的币量
            status=1
            profit1=0
            profit2 = 0
        elif cur_signal==-1 and last_signal!=-1:#开空1多2
            balance=balance1+balance2 #两个币的资金池重新分配
            balance-=balance*transaction_fee #手续费(包含了两个币的)
            balance1=balance*balance_ratio[0]
            balance2 = balance * balance_ratio[1]
            vol1=balance1/cur_price1 #分到币1的币量
            vol2 = balance2 / cur_price2  # 分到币2的币量
            status=-1
            profit1=0
            profit2 = 0
        elif cur_signal==0 and last_signal!=0:#平单
            balance = balance1 + balance2  # 两个币的资金池重新分配
            balance-=balance*transaction_fee #手续费(包含了两个币的)
            balance1=balance*balance_ratio[0]
            balance2 = balance * balance_ratio[1]
            vol1=0
            vol2 =0
            status=0
            profit1=0
            profit2 = 0
        elif status==0: #空仓
            profit1 = 0
            profit2 = 0
        elif status==1: #状态1
            profit1=(cur_price1-last_price1)*vol1
            profit2 = (last_price2-cur_price2) * vol2
        elif status==-1: #状态2
            profit1=(last_price1-cur_price1)*vol1
            profit2 = (cur_price2 - last_price2) * vol2
        balance1+=profit1
        balance2 += profit2
        cur_balance1.append(balance1)
        cur_balance2.append(balance2)
        last_signal=cur_signal
    df1['balance']=cur_balance1
    df2['balance'] = cur_balance2
    return df1,df2

if __name__ == '__main__':
    symbols = ['LUNA2USDT','DOTUSDT']
    internal='15m'
    balance_ratio=[0.5,0.5]
    init_balance=10000
    num_candles=3000
    transaction_fee=0.00045
    offset=1669
    df1 = pd.read_csv(f"D:\\Trade\\data\\{symbols[0]}_{internal}_contract.csv")
    df2 = pd.read_csv(f"D:\\Trade\\data\\{symbols[1]}_{internal}_contract.csv")
    df1,df2=get_overlapping(df1,df2)
    df1 = df1[-num_candles-offset:-offset]  # extract the latest n candles
    df2 = df2[-num_candles-offset:-offset]  # extract the latest n candles
    df1,df2,df_pair=pair_trading(df1,df2,symbols,spread_type='dyn_price_diff')
    df1,df2=calculate_profit_pair(df1, df2, balance_ratio, transaction_fee=transaction_fee)
    file_name = '%s--%s_%s_%d_%f_穿线回归.pdf' % (symbols[0], symbols[1], internal,num_candles,transaction_fee)
    dump_file='D:\\Trade\\results\\pair_trading\\24.11.27\\'
    os.makedirs(dump_file,exist_ok=True)
    plot_pair_trading(df1,df2,df_pair,symbols,internal,dump_file=dump_file+'%s'%file_name)