import pandas as pd
import numpy as np
import utils
import matplotlib.pyplot as plt
from advanced_ta import __version__
import pandas as pd

def test_version():
    assert __version__ == '0.1.0'

from advanced_ta import LorentzianClassification

def macd_cross_simple_strategy(data, signal, initial_balance=10000, holding_days=7, \
                               bear_mode=True, stop_loss=float('-inf'), stop_profit=float('inf')):
    trades = pd.DataFrame(
        columns=['Type', 'Sell Date YMD', 'Buy Date', 'Buy Price', 'Sell Date', 'Sell Price', 'Balance', 'P/L'])
    df = data
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')

    # 筛选最近n年的数据回测
    # start_date = pd.to_datetime('today') - pd.DateOffset(years=1)
    # mask = (df['open_time'] >= start_date)
    # df = df.loc[mask]
    if bear_mode:
        max_close_price_index = df['close_price'].idxmax()
        highest_close_date = df.loc[max_close_price_index]['open_time']
        mask = (df['open_time'] >= highest_close_date)
        df = df.loc[mask]
        min_close_price_index = df['close_price'].idxmin()
        lowest_close_date = df.loc[min_close_price_index]['open_time']
        mask = (df['open_time'] <= lowest_close_date)
        df = df.loc[mask]

    hold_period = holding_days
    initial_balance = initial_balance
    balance = initial_balance
    positions = 0
    for i, row in df.iterrows():
        # 检查是否有持仓
        if (positions == 0):
            if (row[signal] == 1):  # 做多
                positions = balance / row['close_price']
                trades = trades._append({'Type': 'buy', 'Buy Date': i, 'Buy Price': row['close_price']},
                                        ignore_index=True)
            elif (row[signal] == -1):  # 做空
                positions = balance / row['close_price']
                trades = trades._append({'Type': 'sell', 'Buy Date': i, 'Buy Price': row['close_price']},
                                        ignore_index=True)
            else:
                pass
        else:
            if (trades.loc[len(trades) - 1, 'Type'] == 'buy'):  # 持有多单
                # 检查是否满足平单条件
                buy_price = trades.loc[len(trades) - 1, 'Buy Price']
                if row[signal] == -1 or (i - trades.loc[len(trades) - 1, 'Buy Date'] >= hold_period) or \
                        (row['close_price'] - buy_price) / buy_price <= stop_loss or (
                        row['close_price'] - buy_price) / buy_price >= stop_profit:
                    balance = positions * row['close_price']
                    positions = 0
                    trades.loc[len(trades) - 1, 'Sell Date YMD'] = row['open_time']
                    trades.loc[len(trades) - 1, 'Balance'] = balance
                    trades.loc[len(trades) - 1, 'Sell Date'] = i
                    trades.loc[len(trades) - 1, 'Sell Price'] = row['close_price']
                    trades.loc[len(trades) - 1, 'P/L'] = trades.loc[len(trades) - 1, 'Sell Price'] / trades.loc[
                        len(trades) - 1, 'Buy Price'] - 1
                # 检查是否满足开单条件
                if (row[signal] == -1):
                    positions = balance / row['close_price']
                    trades = trades._append({'Type': 'sell', 'Buy Date': i, 'Buy Price': row['close_price']},
                                            ignore_index=True)

            else:  # 持有空单
                # 检查是否满足平单条件
                buy_price = trades.loc[len(trades) - 1, 'Buy Price']
                if row[signal] == 1 or (i - trades.loc[len(trades) - 1, 'Buy Date'] >= hold_period) or \
                        (buy_price - row['close_price']) / buy_price <= stop_loss or (
                        buy_price - row['close_price']) / buy_price >= stop_profit:
                    balance = positions * (buy_price - row['close_price']) + balance
                    positions = 0
                    trades.loc[len(trades) - 1, 'Sell Date YMD'] = row['open_time']
                    trades.loc[len(trades) - 1, 'Balance'] = balance
                    trades.loc[len(trades) - 1, 'Sell Date'] = i
                    trades.loc[len(trades) - 1, 'Sell Price'] = row['close_price']
                    trades.loc[len(trades) - 1, 'P/L'] = 1 - trades.loc[len(trades) - 1, 'Sell Price'] / trades.loc[
                        len(trades) - 1, 'Buy Price']

                # 检查是否满足开单条件
                if row[signal] == 1:
                    positions = balance / row['close_price']
                    trades = trades._append({'Type': 'buy', 'Buy Date': i, 'Buy Price': row['close_price']},
                                            ignore_index=True)

    trades['Sell Date YMD'] = pd.to_datetime(trades['Sell Date YMD'])

    # 统计交易记录
    trades['Days Held'] = (trades['Sell Date'] - trades['Buy Date'])
    trades['Profit/Loss'] = trades['P/L'] * initial_balance

    # 统计平均盈利、胜率、最大回撤和连续亏损次数
    winning_trades = trades[trades['P/L'] > 0]
    losing_trades = trades[trades['P/L'] < 0]
    # print(losing_trades)
    avg_profit = trades['Profit/Loss'].mean()
    win_rate = len(winning_trades) / len(trades)
    drawdown = (trades['Balance'].cummax() - trades['Balance']) / trades['Balance'].cummax()
    max_drawdown = drawdown.max()
    loss_streaks = np.diff(np.where(
        np.concatenate(([losing_trades.index[0] - 1], losing_trades.index, [losing_trades.index[-1] + 1])) != 1)[0])[
                   ::2].max()
    run_days = trades.loc[len(trades) - 1, 'Buy Date'] - trades.loc[0, 'Buy Date']
    P_mean = trades.loc[trades['P/L'] > 0, 'P/L'].mean()  # 大于0的均值
    L_mean = trades.loc[trades['P/L'] < 0, 'P/L'].mean()  # 小于0的均值
    Profit_and_Loss_Ratio = -1 * (P_mean / L_mean)

    # 输出结果
    print('运行时间：', run_days)
    print('平均盈利：', avg_profit)
    print('盈亏比：', Profit_and_Loss_Ratio)
    print('收益率：', (balance - initial_balance) / initial_balance)
    print('年化收益率：', (balance - initial_balance) * 365 / (initial_balance * run_days))
    print('胜率：', win_rate)
    print('最大回撤：', max_drawdown)
    print('连续亏损次数：', loss_streaks)

    # 画图
    _, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    print(data['open_time'])
    ax1.plot(df['open_time'], df['close_price'] / df['close_price'].values[0], 'g-', label=f"Spot_price")
    ax1.set_xlabel('Date')
    ax1.set_ylabel(f"Spot_price", color='g')
    ax1.tick_params('y', colors='g')

    ax2.plot(trades['Sell Date YMD'], trades['Balance'], 'b-', label=f"Blance")
    ax2.set_ylabel(f"Balance", color='b')
    ax2.tick_params('y', colors='b')

    ax2.axhline(y=initial_balance, linestyle=':', color='r')

    ax1.legend(loc="upper left")
    ax2.legend(loc="upper right")

    plt.savefig("macd_cross_contrast_strategy.png")


def macd_cross_only_buy_or_sell_strategy(data, data_w, signal, initial_balance=10000, holding_days=7, \
                                         bear_mode=True, stop_loss=float('-inf'), stop_profit=float('inf'),
                                         transaction_fee=0.00045,save_fig=""):
    trades = pd.DataFrame(
        columns=['Type', 'Sell Date YMD', 'Buy Date YMD', 'Buy Date', 'Buy Price', 'Sell Date', 'Sell Price', 'Balance',
                 'P/L'])
    # 写入大周期牛熊判断
    buy_or_sell = []
    if data_w != None:
        for idx, row in data.iterrows():
            data_w_choose = data_w.loc[data_w['open_time'] <= row['open_time']]
            data_w_choose = data_w_choose.loc[data_w_choose[signal] != 0]
            if (len(data_w_choose) == 0):
                buy_or_sell.append(0)
            else:
                # print(data_w_choose)
                buy_or_sell.append(data_w_choose[signal].values[-1])
    else:
        buy_or_sell = data[signal].values.tolist()

    data['buy_or_sell'] = buy_or_sell
    df = data
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
    # print(df)

    # 筛选最近n年的数据回测
    # start_date = pd.to_datetime('today') - pd.DateOffset(years=0.1)
    start_date = pd.to_datetime('today') - pd.DateOffset(months=12)
    # end_date = pd.to_datetime('today') - pd.DateOffset(months=31)
    mask = (df['open_time'] >= start_date)  # & (df['open_time']<=end_date)
    df = df.loc[mask]

    if bear_mode:
        max_close_price_index = df['close_price'].idxmax()
        highest_close_date = df.loc[max_close_price_index]['open_time']
        mask = (df['open_time'] >= highest_close_date)
        df = df.loc[mask]
        min_close_price_index = df['close_price'].idxmin()
        lowest_close_date = df.loc[min_close_price_index]['open_time']
        mask = (df['open_time'] <= lowest_close_date)
        df = df.loc[mask]

    hold_period = holding_days
    initial_balance = initial_balance
    balance = initial_balance
    positions = 0
    for i, row in df.iterrows():
        # 多头空头持有不同时间
        # if(row['buy_or_sell']==1):
        #     hold_period = 20
        # else:
        #     hold_period = 5
        # 检查是否有持仓
        if (positions == 0):
            if (row[signal] == 1 and row['buy_or_sell'] == 1):  # 做多
                positions = balance / row['close_price']
                trades = trades._append(
                    {'Type': 'buy', 'Buy Date': i, 'Buy Date YMD': row['close_time'], 'Buy Price': row['close_price']},
                    ignore_index=True)
            elif (row[signal] == -1 and row['buy_or_sell'] == -1):  # 做空
                positions = balance / row['close_price']
                trades = trades._append(
                    {'Type': 'sell', 'Buy Date': i, 'Buy Date YMD': row['close_time'], 'Buy Price': row['close_price']},
                    ignore_index=True)
            else:
                pass
        else:
            if (trades.loc[len(trades) - 1, 'Type'] == 'buy'):  # 持有多单
                # 检查是否满足平单条件
                buy_price = trades.loc[len(trades) - 1, 'Buy Price']
                if row[signal] == -1 or (i - trades.loc[len(trades) - 1, 'Buy Date'] >= hold_period) or \
                        (row['close_price'] - buy_price) / buy_price <= stop_loss or (
                        row['close_price'] - buy_price) / buy_price >= stop_profit:
                    balance = (positions * row['close_price']) * (1 - transaction_fee)
                    positions = 0
                    trades.loc[len(trades) - 1, 'Sell Date YMD'] = row['open_time']
                    trades.loc[len(trades) - 1, 'Balance'] = balance
                    trades.loc[len(trades) - 1, 'Sell Date'] = i
                    trades.loc[len(trades) - 1, 'Sell Price'] = row['close_price']
                    # trades.loc[len(trades)-1, 'P/L'] = trades.loc[len(trades)-1, 'Sell Price'] / trades.loc[len(trades)-1, 'Buy Price'] - 1
                    if (len(trades) == 1):
                        balance_ago = initial_balance
                    else:
                        balance_ago = trades.loc[len(trades) - 2, 'Balance']
                    trades.loc[len(trades) - 1, 'P/L'] = balance / balance_ago - 1
                # 检查是否满足开单条件
                if (row[signal] == -1 and row['buy_or_sell'] == -1):
                    positions = balance * (1 - transaction_fee) / row['close_price']
                    trades = trades._append({'Type': 'sell', 'Buy Date': i, 'Buy Date YMD': row['close_time'],
                                             'Buy Price': row['close_price']}, ignore_index=True)

            else:  # 持有空单
                # 检查是否满足平单条件
                buy_price = trades.loc[len(trades) - 1, 'Buy Price']
                if row[signal] == 1 or (i - trades.loc[len(trades) - 1, 'Buy Date'] >= hold_period) or \
                        (buy_price - row['close_price']) / buy_price <= stop_loss or (
                        buy_price - row['close_price']) / buy_price >= stop_profit:
                    balance = (positions * (buy_price - row['close_price']) + balance) * (1 - transaction_fee)
                    positions = 0
                    trades.loc[len(trades) - 1, 'Sell Date YMD'] = row['open_time']
                    trades.loc[len(trades) - 1, 'Balance'] = balance
                    trades.loc[len(trades) - 1, 'Sell Date'] = i
                    trades.loc[len(trades) - 1, 'Sell Price'] = row['close_price']
                    # trades.loc[len(trades)-1, 'P/L'] = 1-trades.loc[len(trades)-1, 'Sell Price'] / trades.loc[len(trades)-1, 'Buy Price']
                    if (len(trades) == 1):
                        balance_ago = initial_balance
                    else:
                        balance_ago = trades.loc[len(trades) - 2, 'Balance']
                    trades.loc[len(trades) - 1, 'P/L'] = balance / balance_ago - 1

                # 检查是否满足开单条件
                if (row[signal] == 1 and row['buy_or_sell'] == 1):
                    positions = balance * (1 - transaction_fee) / row['close_price']
                    trades = trades._append({'Type': 'buy', 'Buy Date': i, 'Buy Date YMD': row['close_time'],
                                             'Buy Price': row['close_price']}, ignore_index=True)

    # print(trades)
    trades['Sell Date YMD'] = pd.to_datetime(trades['Sell Date YMD'])

    # 统计交易记录
    # trades['Days Held'] = (trades['Sell Date'] - trades['Buy Date'])
    trades['Days Held'] = (trades['Sell Date YMD'] - trades['Buy Date YMD'])
    trades['Profit/Loss'] = trades['P/L'] * initial_balance

    # 统计平均盈利、胜率、最大回撤和连续亏损次数
    winning_trades = trades[trades['P/L'] > 0]
    # print(losing_trades)
    avg_profit = trades['Profit/Loss'].mean()
    win_rate = len(winning_trades) / len(trades)
    balance_array = trades['Balance'].values
    balance_array = np.insert(balance_array, 0, initial_balance)
    # drawdown = (trades['Balance'].cummax() - trades['Balance']) / trades['Balance'].cummax()
    # max_drawdown = drawdown.max()
    drawdown = (np.maximum.accumulate(balance_array) - balance_array) / np.maximum.accumulate(balance_array)
    max_drawdown = np.nanmax(drawdown)
    max_index = np.nanargmax(drawdown) - 1
    # loss_streaks = np.diff(np.where(np.concatenate(([losing_trades.index[0] - 1], losing_trades.index, [losing_trades.index[-1] + 1])) != 1)[0])[::2].max()
    # 最大连续亏损
    losing_trades = trades['P/L'] < 0
    change_points = np.diff(losing_trades.astype(int))
    start_points = np.where(change_points == 1)[0] + 1
    end_points = np.where(change_points == -1)[0] + 1
    if losing_trades.iloc[0]:
        start_points = np.insert(start_points, 0, 0)
    if losing_trades.iloc[-1]:
        end_points = np.append(end_points, len(losing_trades))
    lengths = end_points - start_points
    if len(lengths) > 0:
        max_length_index = np.argmax(lengths)
        loss_streaks = lengths[max_length_index]
        start_index = start_points[max_length_index]
    else:
        loss_streaks = 0
        start_index = None

    # 运行时间
    run_days = trades.loc[len(trades) - 1, 'Buy Date YMD'] - trades.loc[0, 'Buy Date YMD']
    P_mean = trades.loc[trades['P/L'] > 0, 'P/L'].mean()  # 大于0的均值
    L_mean = trades.loc[trades['P/L'] < 0, 'P/L'].mean()  # 小于0的均值
    Profit_and_Loss_Ratio = -1 * (P_mean / L_mean)

    # 输出结果
    # print(trades)
    out_results = {}
    # out_results['运行时间'] = run_days
    # out_results['总单数'] = len(trades) - 1
    # out_results['平均每单盈利'] = avg_profit
    # out_results['平均每单持有时间'] = trades['Days Held'].mean()
    out_results['盈亏比'] = Profit_and_Loss_Ratio
    out_results['收益率'] = (balance - initial_balance) / initial_balance
    out_results['年化收益率'] = (balance - initial_balance) * 365 / (
                initial_balance * run_days.total_seconds() / (24 * 3600))
    out_results['胜率'] = win_rate
    out_results['最大回撤'] = max_drawdown
    # out_results['最大回撤结束时间'] = trades.iloc[max_index]['Sell Date YMD']
    # out_results['最大连续亏损次数'] = loss_streaks

    for key in out_results:
        print(key + ": ", out_results[key])

    # print('运行时间：', run_days)
    # print('总单数：', len(trades)-1)
    # print('平均每单盈利：', avg_profit)
    # print('平均每单持有时间：', trades['Days Held'].mean())
    # print('盈亏比：', Profit_and_Loss_Ratio)
    # print('收益率：', (balance-initial_balance)/initial_balance)
    # print('年化收益率：', (balance-initial_balance)*365/(initial_balance*run_days.total_seconds()/(24 * 3600)))
    # print('胜率：', win_rate)
    # print('最大回撤：', max_drawdown)
    # print('最大回撤结束时间：', trades.iloc[max_index]['Sell Date YMD'])
    # print('最大连续亏损次数：', loss_streaks)
    # if (start_index != None):
    #     print('连续亏损的单子列表：')
    #     print(trades.iloc[start_index:start_index + loss_streaks])

    # 画图
    _, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    # print(data['open_time'])
    ax1.plot(df['open_time'], df['close_price'] / df['close_price'].values[0], 'k-', label=f"Spot_price")
    ax1.set_xlabel('Date')
    ax1.set_ylabel(f"Spot_price", color='g')
    ax1.tick_params('y', colors='g')

    ax2.plot(trades['Sell Date YMD'], trades['Balance'], 'b-', label=f"Blance")
    ax2.set_ylabel(f"Balance", color='b')
    ax2.tick_params('y', colors='b')

    ax2.axhline(y=initial_balance, linestyle=':', color='r')

    ax1.legend(loc="upper left")
    ax2.legend(loc="upper right")

    # 画Lorentzian的买卖信号
    xs_long, ys_long, xs_short, ys_short=get_signal_points(df)
    ax1.plot(xs_long,ys_long,'o',color='green')
    ax1.plot(xs_short, ys_short, 'o', color='red')
    plt.savefig(save_fig)

def get_signal_points(df):
    xs_long=[]
    ys_long=[]
    xs_short = []
    ys_short = []
    for index, row in enumerate(df.iterrows()):
        if row[1]['signal']==1:
            xs_long.append(row[1]['open_time'])
            ys_long.append(row[1]['close_price'] / df['close_price'].values[0])
        elif row[1]['signal']==-1:
            xs_short.append(row[1]['open_time'])
            ys_short.append(row[1]['close_price'] / df['close_price'].values[0])
    return xs_long,ys_long,xs_short,ys_short

def get_signal(ma_data):
    signal=[]
    status='hold' # hold, long, short
    for index, row in enumerate(ma_data.iterrows()):
        if row[1]['startLongTrade']>0 and status !='long':
            signal.append(1)
            status='long'
        elif row[1]['startShortTrade']>0 and status !='short':
            signal.append(-1)
            status='short'
        else:
            signal.append(0)
    ma_data['signal']=signal
    return ma_data

#if __name__ == '__main__':
# filepath = 'D:\\Trade\\Lorentzian\\tests\\data\\BTCUSDT_1d_spot.csv'
# df = pd.read_csv(filepath)
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
# symbol = 'ETHUSDT'
# symbol = 'SOLUSDT'
symbols=['BTCUSDT']
internals=['1d','15m','1h','4h']
#internals=['1d','4h']
num_candles=6000
for symbol in symbols:
    for internal in internals:
        print('Backtesting:%s_%s_%s'%(symbol,internal,num_candles))
        df = pd.read_csv(f"D:\\Trade\\informer-Amazon\\utils\\Binacne_Data\\{symbol}\\{symbol}_{internal}_spot.csv")
        output_fig=f"D:\\Trade\\Lorentzian\\output\\{symbol}_{internal}_{num_candles}.png"
        df = df[-num_candles:]
        df['date']=df['open_time']
        df['open']=df['open_price']
        df['high']=df['high_price']
        df['low']=df['low_price']
        df['close']=df['close_price']
        # filepath = 'D:\\Trade\\Lorentzian\\tests\\data\\BTCUSDT_1d_spot.csv'
        # df = pd.read_csv(filepath)
        lc = LorentzianClassification(df)
        #lc.dump('D:\\Trade\\Lorentzian\\output\\result.csv')
        #lc.plot('D:\\Trade\\Lorentzian\\output\\result2.pdf')
        ma_data=lc.df
        ma_data=get_signal(ma_data)
        ma_data = ma_data.reset_index(drop=True)

        #ma_data = utils.MACD(data, fastLength=12, slowLength=26, signalLength=9)
        # ma_data = utils.MACD(data,fastLength = 10, slowLength=20, signalLength=5)

        macd_cross_only_buy_or_sell_strategy(ma_data, None, "signal", initial_balance=10000, holding_days=10000,
                                             bear_mode=False, transaction_fee=0.0,stop_loss=-0.02,save_fig=output_fig)






