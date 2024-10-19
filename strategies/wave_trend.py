from get_factors import *
from visual.plot import plot_trend
import os

def get_profit_threshold(highest_profit):
    if highest_profit<0.03: #如果没达到3%盈利，则设置3%止损
        return -0.025
    elif highest_profit<0.05: #3%-5%,设置0%止损
        return highest_profit/10
    elif highest_profit<0.07: #5%-7%,设置2%止盈
        return highest_profit/3
    elif highest_profit<0.1: #7%-10%,设置2%止盈
        return highest_profit/2
    else: #大于10%时，设置highest_profit/2止盈
        return highest_profit/1.5

def long_buy(row,buy_thresh=2):
    if (row['wave_h'] > buy_thresh or row['lor_signal'] == 1) and row['wave_1d_h'] > -15:
        return True
    else:
        return False

def short_buy(row,buy_thresh=-2):
    if (row['wave_h'] < buy_thresh or row['lor_signal'] == -1) and row['wave_1d_h'] < 15:
        return True
    else:
        return False

def long_sell(row,sell_thresh=-10):
    if row['wave_h'] < sell_thresh:
        return True
    else:
        return False

def short_sell(row,sell_thresh=10):
    if row['wave_h'] > sell_thresh:
        return True
    else:
        return False

def calculate_cur_profit(row,trade_price,highest_profit,profit_th,dir):
    if dir==1: #做多
        profit = (row['close_price'] - trade_price) / trade_price
        high_profit=(row['high_price'] - trade_price) / trade_price
    elif dir==-1: #做空
        profit = (trade_price-row['close_price']) / trade_price
        high_profit=(trade_price-row['low_price']) / trade_price

    if high_profit>highest_profit:
        highest_profit=high_profit
        profit_th = get_profit_threshold(highest_profit)
    return profit,highest_profit,profit_th

def wave_trend(df):
    df= calculate_wave(df, src_type='hlc3', clen=10, alen=21, slen=4)
    df = calculate_wave_1d(df, src_type='hlc3', clen=60, alen=30, slen=25)
    df=calculate_macd(df)
    df=calculate_lorentzian(df)
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
            if long_buy(row):
                strategy_signal.append(1)
                oper_signal.append(1)
                status=1
                status_list.append(status)
                profit=0
                highest_profit=0
                profit_th=get_profit_threshold(highest_profit)
                trade_price=row['close_price']
                profit_th_list.append(profit_th)
                profit_list.append(profit)
                highest_profit_list.append(highest_profit)
                continue
            #开空条件：大周期(1d)空 && ((lor信号空) || (prediction<=-6) && 波浪趋势粉色)
            elif short_buy(row):
                strategy_signal.append(-1)
                oper_signal.append(-1)
                status=-1
                status_list.append(status)
                profit = 0
                highest_profit=0
                profit_th=get_profit_threshold(highest_profit)
                trade_price = row['close_price']
                profit_th_list.append(profit_th)
                profit_list.append(profit)
                highest_profit_list.append(highest_profit)
                continue
        elif status==1: #持有多，等待临时避险，或永久平仓(大周期反转)
            #计算收益率，最高收益，止盈止损阈值
            profit, highest_profit, profit_th=calculate_cur_profit(row,trade_price,highest_profit,profit_th,dir=1)
            #结束交易：出现开空条件时,由多转空
            if short_buy(row):
                strategy_signal.append(-1)
                oper_signal.append(-1)
                status=-1
                status_list.append(status)
                profit = 0
                highest_profit=0
                profit_th=get_profit_threshold(highest_profit)
                profit_th_list.append(profit_th)
                profit_list.append(profit)
                highest_profit_list.append(highest_profit)
                continue
            #止盈止损:
            #if profit<=profit_th or long_sell(row):
            if long_sell(row):
                strategy_signal.append(0)
                oper_signal.append(0)
                status=0
                status_list.append(status)
                profit_th_list.append(profit_th)
                profit_list.append(profit)
                highest_profit_list.append(highest_profit)
                profit = 0
                highest_profit=0
                profit_th=get_profit_threshold(highest_profit)
                continue
        elif status == -1:  # 持有空，等待临时避险，或永久平仓(大周期反转)
            #计算收益率，最高收益，止盈止损阈值
            profit, highest_profit, profit_th=calculate_cur_profit(row,trade_price,highest_profit,profit_th,dir=-1)
            if long_buy(row):
                strategy_signal.append(1)
                oper_signal.append(1)
                status = 1
                status_list.append(status)
                profit = 0
                highest_profit=0
                profit_th=get_profit_threshold(highest_profit)
                profit_th_list.append(profit_th)
                profit_list.append(profit)
                highest_profit_list.append(highest_profit)
                continue
            #止盈止损:
            #if profit<=profit_th or short_sell(row):
            if short_sell(row):
                strategy_signal.append(0)
                oper_signal.append(0)
                status=0
                status_list.append(status)
                profit_th_list.append(profit_th)
                profit_list.append(profit)
                highest_profit_list.append(highest_profit)
                profit = 0
                highest_profit=0
                profit_th=get_profit_threshold(highest_profit)
                continue
        #没有任何信号出现，维持上一时刻
        if not len(strategy_signal)==0:
            strategy_signal.append(strategy_signal[-1])
        else: #起始帧
            strategy_signal.append(0)
            profit=0
            highest_profit = 0
            profit_th = get_profit_threshold(highest_profit)
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
    symbol='JASMYUSDT'
    interval='4h'
    num_candles=20000
    df = pd.read_csv(f"C:\\Trade\\data\\{symbol}_{interval}_spot.csv")
    df=df[-num_candles:]
    df['open_time'] = pd.to_datetime(df['open_time'], origin="1970-01-01 08:00:00", unit='ms')
    df['close_time'] = pd.to_datetime(df['close_time'], origin="1970-01-01 08:00:00", unit='ms')
    df = wave_trend(df)
    df = calculate_profit(df, transaction_fee=0.00045)
    dump_root="C:\\trade\\results\wave_trading\\24.10.12\\"
    os.makedirs(dump_root, exist_ok=True)
    num_files=len(os.listdir(dump_root))
    balance = df['balance']
    min_balance = min(balance)
    # 计算年化收益
    time_diff = pd.to_timedelta(df['close_time'].values[-1] - df['open_time'].values[0],
                                unit='s')
    profit = (balance.iloc[-1] - balance.iloc[0]) / balance.iloc[0]
    annual_profit = profit / time_diff.total_seconds() * (86400 * 365) * 100
    print('Final Balance:%.3f, Min Balance:%.3f, Annual_profit:%.3f%%' % (balance.iloc[-1], min_balance, annual_profit))
    # plot figure
    plot_trend(df,symbol,interval='4h',dump_file=dump_root+'test%d.pdf'%num_files)