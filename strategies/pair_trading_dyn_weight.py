import numpy as np
import pandas as pd
from visual.plot import plot_pair_trading
import os

def pair_trading_singal(df1:pd.DataFrame, df2: pd.DataFrame, spread_type='simple'):
    # 假设我们有两个加密货币的价格数据，以Pandas Series的形式给出
    # 这里使用随机数据作为示例
    # crypto1=(df1['close_price']).to_numpy()
    # crypto2 = (df2['close_price']).to_numpy()
    df1, df2 = get_overlapping(df1, df2)
    if spread_type=='simple':
        returns_crypto1 = (df1['close_price'] - df1['open_price']) / df1['open_price']
        returns_crypto2 = (df2['close_price'] - df2['open_price']) / df2['open_price']
    elif spread_type=='log':
        returns_crypto1 = np.log(df1['close_price'] / df1['open_price'])
        returns_crypto2 = np.log(df2['close_price'] / df2['open_price'])

    # 计算收益率之差
    spread = returns_crypto1 - returns_crypto2

    # 计算SMA
    window_size = 20  # SMA窗口大小，可以根据需要调整
    sma = returns_crypto1.rolling(window=window_size).mean() - returns_crypto2.rolling(window=window_size).mean()

    # 计算标准差
    std_dev = spread.rolling(window=window_size).std()

    # 计算Bollinger带上下限
    bollinger_upper = sma + (2 * std_dev)
    bollinger_lower = sma - (2 * std_dev)

    df_pair=pd.DataFrame()
    df_pair['spread']=spread
    df_pair['bollinger_lower'] = bollinger_lower
    df_pair['bollinger_upper']=bollinger_upper
    df_pair['sma'] = sma
    # import pdb; pdb.set_trace()
    # 生成交易信号
    # 如果spread超过上带，做空crypto1并做多crypto2
    # 如果spread低于下带，做多crypto1并做空crypto2
    # 注意：这里没有实现实际的交易逻辑，只是生成信号
    status=0
    signals_1=[]
    signals_2=[]
    for _, row in df_pair.iterrows():
        if status==0: #等待信号
            if(row['spread']>=row['bollinger_upper']):
                status=1
                signals_1.append(-1)
                signals_2.append(1)
            elif(row['spread']<=row["bollinger_lower"]):
                status=-1
                signals_1.append(1)
                signals_2.append(-1)
            else:
                signals_1.append(0)
                signals_2.append(0)
        elif status==1:
            if row['spread']<row['sma']:
                status=0
                signals_1.append(0)
                signals_2.append(0)
            else:
                signals_1.append(-1)
                signals_2.append(1)
        else:
            if row['spread']>=row['sma']:
                status=0
                signals_1.append(0)
                signals_2.append(0)
            else:
                signals_1.append(1)
                signals_2.append(-1)

    df1['strategy_signal']= signals_1
    df1['return_rate'] = returns_crypto1
    # signals = np.where(spread > bollinger_upper, 1, 0)
    # signals += np.where(spread < bollinger_lower,-1, 0)
    df2['strategy_signal']= signals_2
    df2['return_rate'] = returns_crypto2.tolist()
    return df1, df2

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
    # 计算收益率之差




    # 计算标准差
    std_dev = pd.Series(spread).rolling(window=window_size).std()

    # 计算Bollinger带上下限
    bollinger_upper = sma + (2 * std_dev)
    bollinger_lower = sma - (2 * std_dev)

    df_pair=pd.DataFrame()
    df_pair['spread']=spread
    df_pair['bollinger_lower'] = bollinger_lower
    df_pair['bollinger_upper']=bollinger_upper
    df_pair['sma'] = sma
    # 生成交易信号
    # 如果spread超过上带，做空crypto1并做多crypto2
    # 如果spread低于下带，做多crypto1并做空crypto2
    # 注意：这里没有实现实际的交易逻辑，只是生成信号
    status=0
    signals_1=[]
    signals_2=[]
    record_price=0 #标记开单信号
    for idx,cur_spread in enumerate(spread):
        if status==0: #等待信号
            if cur_spread>=bollinger_upper[idx]: #上穿信号
                status=1
                signals_1.append(-1)
                signals_2.append(1)
                record_price = cur_spread  # 标记开单信号
                continue
            elif cur_spread<=bollinger_lower[idx]: #下穿信号
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
            # # if cur_spread < 0:  # 归位零线
            #     status=0
            #     signals_1.append(0)
            #     signals_2.append(0)
            #     continue
            if cur_spread<sma[idx] and cur_spread<record_price: #归位均线+保底
                status=0
                signals_1.append(0)
                signals_2.append(0)
                record_price = 0  # 标记开单信号
                continue
            if cur_spread<=bollinger_lower[idx] and cur_spread<record_price: #下穿信号+保底
                status=-1
                signals_1.append(1)
                signals_2.append(-1)
                record_price = cur_spread  # 标记开单信号
            # if cur_spread<=bollinger_lower[idx]: #下穿信号
            #     status=-1
            #     signals_1.append(1)
            #     signals_2.append(-1)
            else: #保持
                signals_1.append(-1)
                signals_2.append(1)
                continue
        elif status==-1: #跟踪信号，等待终止条件
            # if cur_spread>sma[idx]: #归位均线
            # # if cur_spread > 0:  # 归位零线
            #     status=0
            #     signals_1.append(0)
            #     signals_2.append(0)
            #     continue
            if cur_spread>sma[idx] and cur_spread>record_price: #归位均线+保底
                status=0
                signals_1.append(0)
                signals_2.append(0)
                record_price = 0  # 标记开单信号
                continue
            if cur_spread>=bollinger_upper[idx] and cur_spread>record_price: #上穿信号+保底
                status=1
                signals_1.append(-1)
                signals_2.append(1)
                record_price = cur_spread  # 标记开单信号
                continue
            # if cur_spread>=bollinger_upper[idx]: #上穿信号
            #     status=1
            #     signals_1.append(-1)
            #     signals_2.append(1)
            #     continue
            else: #保持
                signals_1.append(1)
                signals_2.append(-1)
                continue
    # signals = np.where(spread > bollinger_upper, -1, 0)
    # signals += np.where(spread < bollinger_lower, 1, 0)
    df1['strategy_signal']=[0]+signals_1
    df1['return_rate'] = [0] + returns_crypto1.tolist()
    # signals = np.where(spread > bollinger_upper, 1, 0)
    # signals += np.where(spread < bollinger_lower,-1, 0)
    df2['strategy_signal']=[0]+signals_2
    df2['return_rate'] = [0] + returns_crypto2.tolist()

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

if __name__ == '__main__':
    symbols = ['STXUSDT','JASMYUSDT']
    internal='15m'
    balance_ratio=[0.5,0.5]
    init_balance=10000
    num_candles=1000
    transaction_fee=0.00045
    offset=4669
    df1 = pd.read_csv(f"D:\\Trade\\data\\{symbols[0]}_{internal}_contract.csv")
    df2 = pd.read_csv(f"D:\\Trade\\data\\{symbols[1]}_{internal}_contract.csv")
    df1,df2=get_overlapping(df1,df2)
    df1 = df1[-num_candles-offset:-offset]  # extract the latest n candles
    df2 = df2[-num_candles-offset:-offset]  # extract the latest n candles
    df1,df2,df_pair=pair_trading(df1,df2,symbols,spread_type='price_diff')
    df1=calculate_profit(df1,balance=init_balance*balance_ratio[0],transaction_fee=transaction_fee)
    df2 = calculate_profit(df2, balance=init_balance * balance_ratio[1],transaction_fee=transaction_fee)
    file_name = '%s--%s_%s_%d_%f_9.27-10.7-均线保底.pdf' % (symbols[0], symbols[1], internal,num_candles,transaction_fee)
    dump_file='D:\\Trade\\results\\pair_trading\\24.11.25\\'
    os.makedirs(dump_file,exist_ok=True)
    plot_pair_trading(df1,df2,df_pair,symbols,internal,dump_file=dump_file+'%s'%file_name)