import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from ta.momentum import rsi as RSI
from advanced_ta import LorentzianClassification
from advanced_ta import __version__
from advanced_ta.LorentzianClassification.Types import Feature, Settings
from visual.plot import plot_price_with_adx
from ta.trend import cci as CCI, adx as ADX, ema_indicator as EMA, sma_indicator as SMA
from sklearn.preprocessing import MinMaxScaler
# 计算ADX指标的函数
def calculate_ADX(df, len_period=14, th_period=20):
    high = df['high_price']
    low = df['low_price']
    close = df['close_price']
    # 计算真实波动范围（True Range）
    TrueRange = pd.concat([
        high - low,
        abs(high - close.shift(1)),
        abs(low - close.shift(1))
    ], axis=1).max(axis=1)

    # 计算+DI和-DI
    DirectionalMovementPlus = (high - high.shift(1)).where((high - high.shift(1)) > 0, 0)
    DirectionalMovementMinus = (low.shift(1) - low).where((low.shift(1) - low) > 0, 0)

    # 计算平滑的真实波动范围（Smoothed True Range）
    SmoothedTrueRange = TrueRange.ewm(alpha=1 / len_period, adjust=False).mean()

    # 计算平滑的方向运动指标（Smoothed Directional Movement）
    SmoothedDirectionalMovementPlus = DirectionalMovementPlus.ewm(alpha=1 / len_period, adjust=False).mean()
    SmoothedDirectionalMovementMinus = DirectionalMovementMinus.ewm(alpha=1 / len_period, adjust=False).mean()

    # 计算DI+
    DIPlus = SmoothedDirectionalMovementPlus / SmoothedTrueRange.replace({0: np.nan}) * 100

    # 计算DI-
    DIMinus = SmoothedDirectionalMovementMinus / SmoothedTrueRange.replace({0: np.nan}) * 100

    # 计算DX
    DX = (abs(DIPlus - DIMinus) / (DIPlus + DIMinus)).fillna(0) * 100

    # 计算ADX
    ADX = DX.rolling(len_period).mean()

    # 计算+DI和-DI的信号线
    PlusDI = DIPlus.rolling(th_period).mean()
    MinusDI = DIMinus.rolling(th_period).mean()
    df['ADX'] = ADX
    return df

def normalize(src: np.array, range_min=0, range_max=1) -> np.array:
    """
    function Rescales a source value with an unbounded range to a bounded range
    param src: <np.array> The input series
    param range_min: <float> The minimum value of the unbounded range
    param range_max: <float> The maximum value of the unbounded range
    returns <np.array> The normalized series
    """
    scaler = MinMaxScaler(feature_range=(0, 1))
    return range_min + (range_max - range_min) * scaler.fit_transform(src.reshape(-1,1))[:,0]

def calculate_wt(df, n1=10, n2=11):
    """
    function Returns the normalized WaveTrend Classic series ideal for use in ML algorithms
    param src: <np.array> The input series
    param n1: <int> The first smoothing length for WaveTrend Classic
    param n2: <int> The second smoothing length for the WaveTrend Classic
    returns <np.array> The normalized WaveTrend Classic series
    """
    src=df['close_price']
    ema1 = EMA(src, n1)
    ema2 = EMA(abs(src - ema1), n1)
    ci = (src - ema1) / (0.015 * ema2)
    wt1 = EMA(ci, n2)  # tci
    wt2 = SMA(wt1, 4)
    df['WT']=normalize((wt1 - wt2).values)
    return df

def calculate_macd(df, short_period=12, long_period=26, signal_period=9):
    """
    计算MACD指标
    :param df: 包含收盘价的DataFrame，列名为'Close'
    :param short_period: 短期EMA周期，默认为12
    :param long_period: 长期EMA周期，默认为26
    :param signal_period: 信号线周期，默认为9
    :return: 返回包含原始DataFrame和MACD指标的DataFrame
    """
    # 计算短期和长期的EMA
    short_ema = df['close_price'].ewm(span=short_period, adjust=False).mean()
    long_ema = df['close_price'].ewm(span=long_period, adjust=False).mean()

    # 计算MACD
    macd = short_ema - long_ema

    # 计算信号线
    signal_line = macd.ewm(span=signal_period, adjust=False).mean()

    # 计算MACD直方图
    histogram = macd - signal_line

    # 将MACD指标添加到原始DataFrame中
    df['MACD'] = macd
    df['MACD_Signal Line'] = signal_line
    df['MACD_Histogram'] = histogram
    return df
def calculate_rsi(df, rsi_length=14, ma_type='SMA', ma_length=14):
    rsi = RSI(df['close_price'], 14)
    df['RSI'] = rsi
    rsi_ema=EMA(rsi,7)
    df['RSI_EMA7']=rsi_ema
    rsi_ema=EMA(rsi,14)
    df['RSI_EMA']=rsi_ema
    rsi_ema2=EMA(rsi_ema,14)
    df['RSI_EMA2']=rsi_ema2
    return df



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

def get_lorentzian_signal(ma_data):
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
    ma_data['lor_signal']=signal
    return ma_data

def calculate_lorentzian(df):
    df['date'] = df['open_time']
    df['open'] = df['open_price']
    df['high'] = df['high_price']
    df['low'] = df['low_price']
    df['close'] = df['close_price']
    maxBarsBack=min(20000,df.shape[0]) # the max candles of input is 20000
    settings = Settings(source=df['close'],maxBarsBack=maxBarsBack)
    lc = LorentzianClassification(df,settings=settings,num_feat=5)
    ma_data = lc.df
    ma_data = get_lorentzian_signal(ma_data)
    return ma_data




if __name__ == '__main__':
    symbols=['BTCUSDT']
    #internals=['1d','15m','1h','4h']
    internals=['1h']
    num_candles=6000
    for symbol in symbols:
        for internal in internals:
            print('Backtesting:%s_%s_%s'%(symbol,internal,num_candles))
            df = pd.read_csv(f"D:\\Trade\\informer-Amazon\\utils\\Binacne_Data\\{symbol}\\{symbol}_{internal}_spot.csv")
            df = df[-num_candles:]
            df = calculate_ADX(df)
            df = calculate_rsi(df)
            df['open_time']=pd.to_datetime(df['open_time'], unit='ms')
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
            #plot_price_and_adx(df)
            plot_price_with_adx(df,symbol,internal,ADX_thr=40,RSI_thr=[35,65])
            print('testing')


































