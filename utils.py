from datetime import datetime
import time
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def change_normal_to_log_price(data):
    price_cols = ['open_price', 'high_price', 'low_price', 'close_price']
    data[price_cols] = np.log(data[price_cols])
    return data

def change_log_to_normal_price(data):
    price_cols = ['open_price', 'high_price', 'low_price', 'close_price']
    data[price_cols] = np.exp(data[price_cols])
    return data

# def convert_time_to_YMDH(data):
#     for d in data:
#         open_time = datetime.fromtimestamp(d["open_time"]/1000)
#         close_time = datetime.fromtimestamp(d["close_time"]/1000)
#         d["open_time"] = open_time.strftime('%Y-%m-%d-%H')
#         d["close_time"] = close_time.strftime('%Y-%m-%d-%H')
#     return data
def convert_time_to_YMDH(data):
    time_data = datetime.fromtimestamp(data/1000)
    return time_data.strftime('%Y-%m-%d-%H')

def convert_YMDH_to_time(YMDH_str):
    time_stamp = int(time.mktime(datetime.strptime(YMDH_str, '%Y-%m-%d-%H').timetuple()) * 1000)
    
    # time_str = datetime.fromtimestamp(time_stamp/1000).strftime('%Y-%m-%d-%H')
    
    return time_stamp 

# print(convert_time_to_YMDH(1701230040000))
# print(convert_YMDH_to_time('2023-01-01-00'))

def draw_some_plot(x_datas, y_datas, labels, x_label, y_label, fig_path):
    _, ax = plt.subplots()
    for i in range(len(x_datas)):
        x_data = x_datas[i]
        y_data = y_datas[i]
        ax.bar(x_data, y_data, label=labels[i])
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.legend()
    plt.savefig(fig_path)
    plt.cla()


def cal_APR(profilt, holding_days):
    return profilt/holding_days*365

def cal_max_drawdown(profit_list):
    drawdown_list = []
    for i in range(len(profit_list)):
        for j in range(i+1, len(profit_list)):
            drawdown = (profit_list[j] - profit_list[i])/(1+profit_list[i])
            drawdown_list.append(drawdown)
    return min(drawdown_list)

def calculate_ma(data, period):
    """
    计算给定数据的MA（moving average）
    :param data: 包含BTC数据的DataFrame对象
    :param period: 期限，即计算MA的时间窗口大小
    :return: 包含MA数据的新DataFrame对象
    """
    # # 将open_time列转换为日期时间索引
    # data['open_time'] = pd.to_datetime(data['open_time'], unit='ms')
    # data.set_index('open_time', inplace=True)

    # 计算MA数据并将其添加到新数据框中
    ma = data['close_price'].rolling(window=period).mean()
    data['MA' + str(period)] = ma

    return data

def calculate_ema(data, period):
    ema = data['close_price'].ewm(span=period).mean()
    data['EMA'+ str(period)] = ema
    return data



def calculate_ma_multi_periods(data, periods, drop_nan=False):
    """
    计算给定数据多个MA（moving average）
    :param data: 包含BTC数据的DataFrame对象
    :param periods: 期限list，即计算MA的时间窗口大小
    :return: 包含多个MA数据的新DataFrame对象
    """
    # 将open_time列转换为日期时间索引
    data['open_time'] = pd.to_datetime(data['open_time'], unit='ms')
    # data.set_index('open_time', inplace=True)
    # 针对不同的period计算MA数据并将其添加到新数据框中
    ma_data = pd.DataFrame(index=data.index)  # 用于存储MA数据的新数据框
    for period in periods:
        ma = data['close_price'].rolling(window=period).mean()
        ma_data['MA' + str(period)] = ma
    # 将原始数据和MA数据合并到一起
    ma_data = pd.concat([data, ma_data], axis=1)
    if drop_nan:
        ma_data.dropna(inplace=True)
    return ma_data

def gmma(data, ma_t=1):
    """
    基于ma_data绘制GMMA图表
    data: DataFrame，包含日期和价格的列
    ma_t: 方差阈值，用于判断均线是否处于收敛状态
    return: GMMA图表
    """
    #先变为对数价格
    price_cols = ['open_price', 'high_price', 'low_price', 'close_price', 'turnover', 'active_buying_turnover']
    data[price_cols] = np.log(data[price_cols])


    ma_periods_short = [3, 5, 8, 10, 12, 15]
    ma_periods_long = [30, 35, 40, 45, 50, 60]

    # 计算多个时间周期的移动平均线
    ma_data = calculate_ma_multi_periods(data, ma_periods_short + ma_periods_long, drop_nan=True)
    ma_data['open_time'] = data['open_time']

    # 判断是否收敛以及是买入还是卖出
    short_columns = ['MA' + str(period) for period in ma_periods_short]
    long_columns = ['MA' + str(period) for period in ma_periods_long]
    ma_data['short_mean'] = ma_data[short_columns].mean(axis=1)
    ma_data['long_mean'] = ma_data[long_columns].mean(axis=1)
    ma_data['short_std'] = ma_data[short_columns].std(axis=1)/ma_data['short_mean']
    print(ma_data['short_std'].min())
    print(ma_data['short_std'].max())
    ma_data['long_std'] = ma_data[long_columns].std(axis=1)/ma_data['long_mean']
    ma_data['convergence'] = (ma_data['short_std'] <= ma_t) & (ma_data['long_std'] <= ma_t)
    ma_data['signal'] = np.where((ma_data['short_mean'] > ma_data['long_mean']), 'Short', 'Long')
    
    df = ma_data
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    # df = df.set_index('open_time')
    print(df['convergence']==True)
    df['buy_sell'] = 'hold'
    df.loc[(df['convergence']==True) & (df['signal']=='Long'), 'buy_sell'] = 'buy'
    df.loc[(df['convergence']==True) & (df['signal']=='Short'), 'buy_sell'] = 'sell'
    plt.plot(df['open_time'], df['close_price'])
    # print(df[df['buy_sell'] == 'buy']['open_time'])
    plt.scatter(df[df['buy_sell'] == 'buy']['open_time'], df[df['buy_sell'] == 'buy']['close_price'], marker='^', color='g', s=50)
    plt.scatter(df[df['buy_sell'] == 'sell']['open_time'], df[df['buy_sell'] == 'sell']['close_price'], marker='v', color='r', s=50)
    plt.savefig('test_debug.png')
    return ma_data

def RSI(data):
    # data = change_normal_to_log_price(data)
    delta = data['close_price'].diff()
    gain = delta.where(delta > 0, 0)
    # print(gain)
    loss = -delta.where(delta < 0, 0)
    # print(loss)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    # rsi = 100 - (100 / (1 + rs))
    # rsi = np.where(avg_loss == 0, 100, np.where(avg_gain == 0, 0, 100 - (100 / (1 + avg_gain / avg_loss))))
    rsi = 100 - (100 / (1 + avg_gain / avg_loss)).replace(np.inf, np.nan).fillna(method='bfill')
    rsi_mean = rsi.rolling(window=14).mean()
    hist = rsi  - rsi_mean
    cross_idx_above = np.argwhere((hist>=0) & (hist.shift(1)<0))[:, 0]
    cross_idx_below = np.argwhere((hist<0) & (hist.shift(1)>0))[:, 0]
    rsi_cross_signal = []
    for i, row in data.iterrows():
        if(i in cross_idx_above):
            rsi_cross_signal.append(1) #buy
        elif(i in cross_idx_below):
            rsi_cross_signal.append(-1) #sell
        else:
            rsi_cross_signal.append(0) #holding
    data['RSI_CROSS'] = rsi_cross_signal

    #draw_plot
    # open_time = pd.to_datetime(data['open_time'], unit='ms')
    # colors = []
    # for i, row in data.iterrows():
    #     if i in cross_idx_above:
    #         colors.append('green')
    #     elif i in cross_idx_below:
    #         colors.append('red')
    #     else:
    #         colors.append('/')
    # plt.figure(figsize=(10, 5))
    # plt.plot(open_time, data['close_price'], color='blue', linewidth=1)
    # for i, color in enumerate(colors):
    #     if color == 'red':
    #         plt.scatter(open_time[i], data['close_price'][i], color=color, s=10)
    #     elif color == 'green':
    #         plt.scatter(open_time[i], data['close_price'][i], color=color, s=30)

    # plt.title('Open Time - Close Price')
    # plt.xlabel('Open Time')
    # plt.ylabel('Close Price')
    # plt.show()

    return data

def MACD(data, fastLength = 12, slowLength=26, signalLength=9):
    # fastLength = 12
    # slowLength=26
    # signalLength=9
    data = calculate_ema(data, period=fastLength)
    data = calculate_ema(data, period=slowLength)
    macd = data['EMA'+str(fastLength)] - data['EMA'+str(slowLength)]
    signal = macd.ewm(span=signalLength).mean()
    # signal = calculate_ma(macd, signalLength)['MA'+str(signalLength)]
    hist = macd - signal
    macd_isabove = macd >= signal
    macd_isbelow = macd < signal
    hist_a_isup = (hist > hist.shift(1)) & (hist > 0)
    hist_a_isdown = (hist < hist.shift(1)) & (hist > 0)
    hist_b_isdown = (hist < hist.shift(1)) & (hist <= 0)
    hist_b_isup = (hist > hist.shift(1)) & (hist <= 0)
    # macd_color = np.where(macd_isabove, 'lime', 'red')
    # signal_color = np.where(macd_isabove, 'yellow', 'lime')
    # hist_color = np.where(hist_a_isup, 'aqua', np.where(hist_a_isdown, 'blue', np.where(hist_b_isdown, 'red', np.where(hist_b_isup, 'maroon', 'gray'))))
    # _, ax = plt.subplots()
    cross_idx_above = np.argwhere((hist>=0) & (hist.shift(1)<0))[:, 0]
    corss_idx_below = np.argwhere((hist<0) & (hist.shift(1)>0))[:, 0]
    macd_cross_signal = []
    for i, row in data.iterrows():
        if(i in cross_idx_above):
            macd_cross_signal.append(1) #buy
        elif(i in corss_idx_below):
            macd_cross_signal.append(-1) #sell
        else:
            macd_cross_signal.append(0) #holding
    data['MACD_CROSS'] = macd_cross_signal
    return data

    #draw_plot
    # print(cross_idx_above)
    # print(corss_idx_below)

    # open_time = pd.to_datetime(data['open_time'], unit='ms')
    # colors = []
    # for i, row in data.iterrows():
    #     if i in cross_idx_above:
    #         colors.append('green')
    #     elif i in corss_idx_below:
    #         colors.append('red')
    #     else:
    #         colors.append('/')
    # plt.figure(figsize=(10, 5))
    # plt.plot(open_time, data['close_price'], color='blue', linewidth=1)
    # print(colors)
    # for i, color in enumerate(colors):
    #     if color == 'red':
    #         plt.scatter(open_time[i], data['close_price'][i], color=color, s=10)
    #     elif color == 'green':
    #         plt.scatter(open_time[i], data['close_price'][i], color=color, s=30)

    # plt.title('Open Time - Close Price')
    # plt.xlabel('Open Time')
    # plt.ylabel('Close Price')
    # plt.show()

    # ax.plot(macd, color=macd_color, linewidth=4)
    # ax.plot(signal, color=signal_color, linewidth=2)
    # ax.bar(hist.index, hist, color=hist_color)
    # ax.hlines(0, hist.index[0], hist.index[-1], colors='white', linewidth=2)
    # cross_idx0 = np.argwhere((macd > signal) & (macd.shift(1) < signal.shift(1)))[:, 0]
    
    # print(cross_idx)
    # print(data)
    # ax.plot(cross_idx, macd[cross_idx], '.', markersize=20, color=macd_color[cross_idx])
    # plt.show()


if __name__ == '__main__':
    data = pd.read_csv('/Users/bytedance/Downloads/GUO_Quatum_Trading/Binacne_Data/BTCUSDT/BTCUSDT_1d_spot.csv')
    # data = change_normal_to_log_price(data)
    ma_data = RSI(data)
    ma_data.to_csv('test_debug.csv', index=False)
    print(ma_data)

