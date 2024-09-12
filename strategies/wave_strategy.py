import numpy as np
import pandas as pd

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

class Bar:
    def __init__(self, open, high, low, close):
        self.o = open
        self.h = high
        self.l = low
        self.c = close

class Osc:
    def __init__(self, o, s, h):
        self.o = o
        self.s = s
        self.h = h

def src(b, src_type):
    if src_type == 'open':
        return b.o
    elif src_type == 'high':
        return b.h
    elif src_type == 'low':
        return b.l
    elif src_type == 'close':
        return b.c
    elif src_type == 'oc2':
        return np.average([b.o, b.c])
    elif src_type == 'hl2':
        return np.average([b.h, b.l])
    elif src_type == 'hlc3':
        return np.average([b.h, b.l, b.c])
    elif src_type == 'ohlc4':
        return np.average([b.o, b.h, b.l, b.c])
    elif src_type == 'hlcc4':
        return np.average([b.h, b.l, b.c, b.c])

def stdev(data, length):
    mean = np.mean(data[-length:])
    variance = np.mean((data[-length:] - mean) ** 2)
    return np.sqrt(variance)

def wave(b, src_type, clen, alen, slen):
    x = src(b, src_type)
    m = np.convolve(x, np.ones(clen)/clen, mode='valid')
    d = stdev(x, clen)
    o = np.convolve((x[m.index] - m) / d * 100, np.ones(alen)/alen, mode='valid')
    s = np.convolve(o, np.ones(slen)/slen, mode='valid')
    return Osc(o[-1], s[-1], o[-1] - s[-1])

# Example usage
data = {
    'open': [100, 101, 102, 103],
    'high': [105, 106, 107, 108],
    'low': [95, 96, 97, 98],
    'close': [104, 105, 106, 107]
}
df = pd.DataFrame(data)
df['bar'] = df.apply(lambda row: Bar(row['open'], row['high'], row['low'], row['close']), axis=1)

src_type = 'hlc3'
clen = 10
alen = 21
slen = 4
for index, row in df.iterrows():
    bar = row['bar']
    result = wave(bar, src_type, clen, alen, slen)
    print(f"Bar {index}: Oscillator = {result.o}, Signal = {result.s}, Histogram = {result.h}")