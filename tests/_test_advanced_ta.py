from advanced_ta import __version__
import pandas as pd

def test_version():
    assert __version__ == '0.1.0'

from advanced_ta import LorentzianClassification

    # df here is the dataframe containing stock data as [['open', 'high', 'low', 'close', 'volume']]. Notice that the column names are in lower case.

filepath='D:\\Trade\\Lorentzian\\tests\\data\\BTCUSDT_1d_spot.csv'
df=pd.read_csv(filepath)
df=df[-500:]

lc = LorentzianClassification(df)
lc.dump('D:\\Trade\\Lorentzian\\output\\result.csv')
lc.plot('D:\\Trade\\Lorentzian\\output\\result.pdf')

#
# from advanced_ta import LorentzianClassification
# from ta.volume import money_flow_index as MFI
#
# # df here is the dataframe containing stock data as [['open', 'high', 'low', 'close', 'volume']]. Notice that the column names are in lower case.
# lc = LorentzianClassification(
#     df,
#     features=[
#         LorentzianClassification.Feature("RSI", 14, 2),  # f1
#         LorentzianClassification.Feature("WT", 10, 11),  # f2
#         LorentzianClassification.Feature("CCI", 20, 2),  # f3
#         LorentzianClassification.Feature("ADX", 20, 2),  # f4
#         LorentzianClassification.Feature("RSI", 9, 2),   # f5
#         MFI(df['high'], df['low'], df['close'], df['volume'], 14) #f6
#     ],
#     settings=LorentzianClassification.Settings(
#         source='close',
#         neighborsCount=8,
#         maxBarsBack=2000,
#         useDynamicExits=False
#     ),
#     filterSettings=LorentzianClassification.FilterSettings(
#         useVolatilityFilter=True,
#         useRegimeFilter=True,
#         useAdxFilter=False,
#         regimeThreshold=-0.1,
#         adxThreshold=20,
#         kernelFilter = LorentzianClassification.KernelFilter(
#             useKernelSmoothing = False,
#             lookbackWindow = 8,
#             relativeWeight = 8.0,
#             regressionLevel = 25,
#             crossoverLag = 2,
#         )
#     ))
# lc.dump('output/result.csv')
# lc.plot('output/result.jpg')