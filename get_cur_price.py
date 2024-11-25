import requests
import json
import os
import time
import pandas as pd
from datetime import datetime, timezone, timedelta

def get_symbols(api_key):
    # api_key = "6pt5lBHzwSTX0URrwbmbBwf97EnX4KZuQ2pCjCzKG8mkHXCoOlUttDew0fLcJ3af"

    base_url = "https://api.binance.com/api/v3/exchangeInfo"
    headers = {
            "X-MBX-APIKEY": api_key
        }
    response = requests.get(base_url, headers=headers)
    data = response.json()
    symbols = data["symbols"]
    return symbols

def get_topN_trading_coin(N):
    url = "https://api.binance.com/api/v3/ticker/24hr"
    response = requests.get(url)
    market_data = response.json()
    # print(market_data)
    if(N>len(market_data)):
        print(f"{N} is so big that the market only has {len(market_data)} trading pairs!")
        return
    stablecoins = ['USDT', 'BUSD', 'USDC', 'TUSD', 'PAX', 'BKRW', 'IDRT', \
                   'BKRW', 'EUR', 'NGN', 'RUB', 'TRY', 'UAH', 'AUD', 'GBP', \
                    'DAI', 'BIDR', 'FDUSD']
    market_data_sorted = sorted(market_data, key=lambda entry: float(entry["quoteVolume"]), reverse=True)
    filtered_pairs = []
    for pair in market_data_sorted:
        if(len(filtered_pairs)==N):
            break
        symbol = pair['symbol']
        base, quote = symbol[:-len('USDT')], 'USDT'
        if symbol.endswith("USDT") and base not in stablecoins:
            filtered_pairs.append(pair["symbol"])
            # filtered_pairs.append(symbol[:-len('USDT')]+'BTC')
    return filtered_pairs

def generate_spot_trading_data(symbol= "BTCUSDT", interval= "1h"):
    #os.makedirs(f"./Binacne_Data/{symbol}", exist_ok=True)
    columns = ["open_time", "open_price", "high_price", "low_price", "close_price",
           "volume", "close_time", "turnover", "tickcount", "active_buying_volume",
           "active_buying_turnover", "Unknown"]
    if(os.path.exists(os.path.join(f"C:/Trade/data/{symbol}_{interval}_spot.csv"))):
        #df = pd.read_csv(os.path.join(f"C:/Trade/data/{symbol}_{interval}_spot.csv"))
        os.remove(os.path.join(f"C:/Trade/data/{symbol}_{interval}_spot.csv"))
        df = pd.DataFrame(columns=columns)
    else:
        df = pd.DataFrame(columns=columns)
    def get_klines(df=None):
        klines = []
        now = datetime.now(timezone.utc).timestamp() * 1000
        end_time = int(now)
        # print(end_time)
        limit = 1500
        while True:
            url = f"https://api.binance.com/api/v3/klines?symbol={symbol}"+\
            f"&interval={interval}&endTime={end_time}&limit={limit}"
            print(url)
            # Send the request

            response = requests.get(url)
            # print(response)
            # import pdb; pdb.set_trace()
            if response.status_code == 200:
                data = response.json()
                # if len(df)>0:
                    # if(end_time < df["open_time"].values[-1]):
                    #     break
                if(end_time<1609430400000): # 2021-01-01
                #if(end_time<1710975546000): #2024-03-21
                    break
                # Save the response
                klines = data + klines
                # if len(data) < limit:
                #     # If the number of klines returned is less than the limit, we got all the klines
                #     break
                # else:
                #     # If not, set the start time to the end time of the last kline received
                try:
                    end_time = data[0][0] - 1
                except:
                    break
                # Wait for a little while (1 req/s)
                #time.sleep(1)
            else:
                # If the API returns an error, print the response
                print(response.json())
                break
        return klines
    klines = get_klines(df)
    if(len(df)==0):
        df = pd.DataFrame(klines, columns=columns)
        df = df.drop_duplicates(keep='first')
        df.to_csv(os.path.join(f"C:/Trade/data/{symbol}_{interval}_spot.csv"), index=False)
    else:
        df_new = pd.DataFrame(klines, columns=columns)
        df_end_time = df['open_time'].values[-1]
        drop_list = []
        for idx, row in df_new.iterrows():
            if(row['open_time']<=df_end_time):
                # df_new = df_new.drop(idx)
                drop_list.append(idx)
        df_new = df_new.drop(drop_list)
        df_concat = pd.concat([df, df_new])
        df_concat.to_csv(os.path.join(f"C:/Trade/data/{symbol}_{interval}_spot.csv"), index=False)

# generate_spot_trading_data()

def generate_contract_trading_data(symbol= "BTCUSDT", interval= "1h"):
    #os.makedirs(f"./Binacne_Data/{symbol}", exist_ok=True)
    columns = ["open_time", "open_price", "high_price", "low_price", "close_price",
           "volume", "close_time", "turnover", "tickcount", "active_buying_volume",
           "active_buying_turnover", "Unknown"]
    file_path=os.path.join(f"D:/Trade/data/{symbol}_{interval}_contract.csv")
    if(os.path.exists(file_path)):
        #df = pd.read_csv(os.path.join(f"D:/Trade/data/{symbol}_{interval}_contract.csv"))
        os.remove(file_path)
        df = pd.DataFrame(columns=columns)
    else:
        df = pd.DataFrame(columns=columns)
    def get_klines(df=None):
        klines = []
        now = datetime.now(timezone.utc).timestamp() * 1000
        end_time = int(now)
        # print(end_time)
        limit = 1500
        pair = symbol
        contractType = "PERPETUAL"
        while True:
            url = f"https://fapi.binance.com/fapi/v1/continuousKlines?pair={pair}"+\
            f"&contractType={contractType}&interval={interval}&endTime={end_time}&limit={limit}"
            print(url)
            # Send the request

            response = requests.get(url)
            # print(response)
            # import pdb; pdb.set_trace()
            if response.status_code == 200:
                data = response.json()
                # if len(df)>0:
                    # if(end_time < df["open_time"].values[-1]):
                    #     break
                #if(end_time<1609430400000): # 2021-01-01
                if(end_time<1710975546000): #2024-03-21
                    break
                # Save the response
                klines = data + klines
                # if len(data) < limit:
                #     # If the number of klines returned is less than the limit, we got all the klines
                #     break
                # else:
                #     # If not, set the start time to the end time of the last kline received
                try:
                    end_time = data[0][0] - 1
                except:
                    break
                # Wait for a little while (1 req/s)
                #time.sleep(1)
            else:
                # If the API returns an error, print the response
                print(response.json())
                break
        return klines
    klines = get_klines(df)
    if(len(df)==0):
        df = pd.DataFrame(klines, columns=columns)
        df = df.drop_duplicates(keep='first')
        df.to_csv(file_path, index=False)
    else:
        df_new = pd.DataFrame(klines, columns=columns)
        df_end_time = df['open_time'].values[-1]
        drop_list = []
        for idx, row in df_new.iterrows():
            if(row['open_time']<=df_end_time):
                # df_new = df_new.drop(idx)
                drop_list.append(idx)
        df_new = df_new.drop(drop_list)
        df_concat = pd.concat([df, df_new])
        df_concat.to_csv(file_path, index=False)

def generate_contract_trading_data2(symbol= "BTCUSDT", interval= "1h"):
    os.makedirs(f"./Binacne_Data/{symbol}", exist_ok=True)
    columns = ["open_time", "open_price", "high_price", "low_price", "close_price",
           "volume", "close_time", "turnover", "tickcount", "active_buying_volume",
           "active_buying_turnover", "Unknown"]
    if(os.path.exists(os.path.join(f"D:/Trade/Lorentzian/data/{symbol}_{interval}_contract.csv"))):
        df = pd.read_csv(os.path.join(f"D:/Trade/Lorentzian/data/{symbol}_{interval}_contract.csv"))
    else:
        df = pd.DataFrame(columns=columns)
    def get_klines(df=None):
        klines = []
        now = datetime.now(timezone.utc).timestamp() * 1000
        end_time = int(now)
        pair = symbol
        contractType = "PERPETUAL"
        limit = 1500
        while True:
            url = f"https://fapi.binance.com/fapi/v1/continuousKlines?pair={pair}"+\
            f"&contractType={contractType}&interval={interval}&endTime={end_time}&limit={limit}"
            print(url)
            # Send the request
            response = requests.get(url)
            # print(response)
            # import pdb; pdb.set_trace()
            if response.status_code == 200:
                data = response.json()
                if len(df)>0:
                    if(end_time < df["open_time"].values[-1]):
                        break
                # Save the response
                klines = data + klines
                # if len(data) < limit:
                #     # If the number of klines returned is less than the limit, we got all the klines
                #     break
                # else:
                    # If not, set the start time to the end time of the last kline received
                try:
                    end_time = data[0][0] - 1
                except:
                    break
                # Wait for a little while (1 req/s)
                time.sleep(1)
            else:
                # If the API returns an error, print the response
                print(response.json())
                break
        return klines
    klines = get_klines(df)
    if(len(df)==0):
        df = pd.DataFrame(klines, columns=columns)
        df = df.drop_duplicates(keep='first')
        df.to_csv(os.path.join(f"D:/Trade/Lorentzian/data/{symbol}/{symbol}_{interval}_contract.csv"), index=False)
    else:
        df_new = pd.DataFrame(klines, columns=columns)
        df_end_time = df['open_time'].values[-1]
        drop_list = []
        for idx, row in df_new.iterrows():
            if(row['open_time']<=df_end_time):
                # df_new = df_new.drop(idx)
                drop_list.append(idx)
        df_new = df_new.drop(drop_list)
        df_concat = pd.concat([df, df_new])
        df_concat.to_csv(os.path.join(f"D:/Trade/Lorentzian/data/{symbol}/{symbol}_{interval}_contract.csv"), index=False)

# generate_contract_trading_data()

def generate_markPrice_data(symbol = "BTCUSDT", interval= "1h"):
    os.makedirs(f"./Binacne_Data/{symbol}", exist_ok=True)
    columns = ["open_time", "open_price", "high_price", "low_price", "close_price",
           "volume", "close_time", "turnover", "tickcount", "active_buying_volume",
           "active_buying_turnover", "Unknown"]
    if(os.path.exists(os.path.join(f"./Binacne_Data/{symbol}/{symbol}_{interval}_markPrice.csv"))):
        df = pd.read_csv(os.path.join(f"./Binacne_Data/{symbol}/{symbol}_{interval}_markPrice.csv"))
    else:
        df = pd.DataFrame(columns=columns)
    def get_klines(df=None):
        klines = []
        now = datetime.now(timezone.utc).timestamp() * 1000
        end_time = int(now)
        pair = symbol
        limit = 1500
        while True:
            url = f"https://fapi.binance.com/fapi/v1/markPriceKlines?symbol={pair}"+\
            f"&interval={interval}&endTime={end_time}&limit={limit}"
            print(url)
            # Send the request
            response = requests.get(url)
            # print(response)
            # import pdb; pdb.set_trace()
            if response.status_code == 200:
                data = response.json()
                if len(df)>0:
                    if(end_time < df["open_time"].values[-1]):
                        break
                # Save the response
                klines = data + klines
                # if len(data) < limit:
                #     # If the number of klines returned is less than the limit, we got all the klines
                #     break
                # else:
                    # If not, set the start time to the end time of the last kline received
                try:
                    end_time = data[0][0] - 1
                except:
                    break
                # Wait for a little while (1 req/s)
                time.sleep(1)
            else:
                # If the API returns an error, print the response
                print(response.json())
                break
        return klines
    klines = get_klines(df)
    if(len(df)==0):
        df = pd.DataFrame(klines, columns=columns)
        df = df.drop_duplicates(keep='first')
        df.to_csv(os.path.join(f"./Binacne_Data/{symbol}/{symbol}_{interval}_markPrice.csv"), index=False)
    else:
        df_new = pd.DataFrame(klines, columns=columns)
        df_end_time = df['open_time'].values[-1]
        drop_list = []
        for idx, row in df_new.iterrows():
            if(row['open_time']<=df_end_time):
                # df_new = df_new.drop(idx)
                drop_list.append(idx)
        df_new = df_new.drop(drop_list)
        df_concat = pd.concat([df, df_new])
        df_concat.to_csv(os.path.join(f"./Binacne_Data/{symbol}/{symbol}_{interval}_markPrice.csv"), index=False)

def generate_premiumIndex_data(symbol = "BTCUSDT", interval= "1h"):
    os.makedirs(f"./Binacne_Data/{symbol}", exist_ok=True)
    columns = ["open_time", "open_price", "high_price", "low_price", "close_price",
           "volume", "close_time", "turnover", "tickcount", "active_buying_volume",
           "active_buying_turnover", "Unknown"]
    if(os.path.exists(os.path.join(f"./Binacne_Data/{symbol}/{symbol}_{interval}_premiumIndex.csv"))):
        df = pd.read_csv(os.path.join(f"./Binacne_Data/{symbol}/{symbol}_{interval}_premiumIndex.csv"))
    else:
        df = pd.DataFrame(columns=columns)
    def get_klines(df=None):
        klines = []
        now = datetime.now(timezone.utc).timestamp() * 1000
        end_time = int(now)
        pair = symbol
        limit = 1500
        while True:
            url = f"https://fapi.binance.com/fapi/v1/premiumIndexKlines?symbol={pair}"+\
            f"&interval={interval}&endTime={end_time}&limit={limit}"
            print(url)
            # Send the request
            response = requests.get(url)
            # print(response)
            # import pdb; pdb.set_trace()
            if response.status_code == 200:
                data = response.json()
                if len(df)>0:
                    if(end_time < df["open_time"].values[-1]):
                        break
                # Save the response
                klines = data + klines
                # if len(data) < limit:
                #     # If the number of klines returned is less than the limit, we got all the klines
                #     break
                # else:
                    # If not, set the start time to the end time of the last kline received
                try:
                    end_time = data[0][0] - 1
                except:
                    break
                # Wait for a little while (1 req/s)
                time.sleep(1)
            else:
                # If the API returns an error, print the response
                print(response.json())
                break
        return klines
    klines = get_klines(df)
    if(len(df)==0):
        df = pd.DataFrame(klines, columns=columns)
        df = df.drop_duplicates(keep='first')
        df.to_csv(os.path.join(f"./Binacne_Data/{symbol}/{symbol}_{interval}_premiumIndex.csv"), index=False)
    else:
        df_new = pd.DataFrame(klines, columns=columns)
        df_end_time = df['open_time'].values[-1]
        drop_list = []
        for idx, row in df_new.iterrows():
            if(row['open_time']<=df_end_time):
                # df_new = df_new.drop(idx)
                drop_list.append(idx)
        df_new = df_new.drop(drop_list)
        df_concat = pd.concat([df, df_new])
        df_concat.to_csv(os.path.join(f"./Binacne_Data/{symbol}/{symbol}_{interval}_premiumIndex.csv"), index=False)

def generate_fundingRate_data(symbol = "BTCUSDT"):
    os.makedirs(f"./Binacne_Data/{symbol}", exist_ok=True)
    columns = ["symbol", "fundingRate", "fundingTime"]
    if(os.path.exists(os.path.join(f"./Binacne_Data/{symbol}/{symbol}_fundingRate.csv"))):
        df = pd.read_csv(os.path.join(f"./Binacne_Data/{symbol}/{symbol}_fundingRate.csv"))
    else:
        df = pd.DataFrame(columns=columns)
    def get_klines(df=None):
        klines = []
        now = datetime.now(timezone.utc).timestamp() * 1000
        end_time = int(now)
        pair = symbol
        limit = 1000
        begin = False
        last_url = None
        while True:
            if(begin==False):
                url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={pair}"
                begin = True
            else:
                start_time = end_time-limit*28800000
                url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={pair}" +\
                f"&startTime={start_time}&limit={limit}"
            print(url)
            if(url==last_url):
                break
            # Send the request
            response = requests.get(url)
            # print(response)
            # import pdb; pdb.set_trace()
            if response.status_code == 200:
                data = response.json()
                if len(df)>0:
                    if(end_time < df["fundingTime"].values[-1]):
                        break
                # Save the response
                klines = data + klines
                # print(klines[0])
                last_url = url
                # if len(data) < limit:
                #     # If the number of klines returned is less than the limit, we got all the klines
                #     break
                # else:
                    # If not, set the start time to the end time of the last kline received
                try:
                    end_time = data[0]["fundingTime"] - 1
                    # print(data[0])
                except:
                    break
                # Wait for a little while (1 req/s)
                time.sleep(1)
            else:
                # If the API returns an error, print the response
                print(response.json())
                break
        return klines
    klines = get_klines(df)
    if(len(df)==0):
        df = pd.DataFrame(klines)
        df = df.drop_duplicates(keep='first')
        df.to_csv(os.path.join(f"./Binacne_Data/{symbol}/{symbol}_fundingRate.csv"), index=False)
    else:
        df_new = pd.DataFrame(klines)
        df_end_time = df["fundingTime"].values[-1]
        drop_list = []
        for idx, row in df_new.iterrows():
            if(row["fundingTime"]<=df_end_time):
                # df_new = df_new.drop(idx)
                drop_list.append(idx)
        df_new = df_new.drop(drop_list)
        df_concat = pd.concat([df, df_new])
        df_concat.to_csv(os.path.join(f"./Binacne_Data/{symbol}/{symbol}_fundingRate.csv"), index=False)

if __name__ == "__main__":
    import multiprocessing
    symbols = get_topN_trading_coin(N=150)
    print(symbols)
    #symbols = ['IMXUSDT','1000FLOKIUSDT']

    from strategies.coin_list import *
    symbols = coin_test2_list
    symbols = ['JASMYUSDT']
    pool = multiprocessing.Pool(processes=5)
    print(symbols)
    # generate_fundingRate_data(symbol = symbols[0])
    start_index = 0
    for idx in range(start_index, len(symbols)):
        symbol = symbols[idx]
        for internal in ['15m']:
        # try:
        #     pool.apply_async(generate_spot_trading_data, args=(symbol, "1w"))
        #     # generate_spot_trading_data(symbol= symbol, interval= "1h")
        # except:
        #     print(f"error {symbol} spot")
                #pool.apply_async(generate_spot_trading_data, args=(symbol, internal))
            #generate_spot_trading_data(symbol, internal)
            generate_contract_trading_data(symbol, internal)
            # try:
            #     pool.apply_async(generate_spot_trading_data, args=(symbol, internal))
            #     # generate_spot_trading_data(symbol= symbol, interval= "1h")
            # except:
            #     print(f"error {symbol} spot")
        # try:
        #     pool.apply_async(generate_spot_trading_data, args=(symbol, "4h"))
        #     # generate_spot_trading_data(symbol= symbol, interval= "1h")
        # except:
        #     print(f"error {symbol} spot")
        # try:
        #     pool.apply_async(generate_spot_trading_data, args=(symbol, "1h"))
        #     # generate_spot_trading_data(symbol= symbol, interval= "1h")
        # except:
        #     print(f"error {symbol} spot")
        # try:
        #     pool.apply_async(generate_spot_trading_data, args=(symbol, "1d"))
        #     generate_spot_trading_data(symbol= symbol, interval= "5m")
        #     pool.apply_async(generate_spot_trading_data, args=(symbol, "5m"))
        #     generate_spot_trading_data(symbol= symbol, interval= "1h")
        # except:
        #     print(f"error {symbol} spot")
        # try:
        #     pool.apply_async(generate_contract_trading_data, args=(symbol, "1h"))
        #     # generate_contract_trading_data(symbol= symbol, interval= "1h")
        # except:
        #     print(f"error {symbol} contract")
        # try:
        #     pool.apply_async(generate_contract_trading_data, args=(symbol, "1d"))
        #     # generate_contract_trading_data(symbol= symbol, interval= "1h")
        # except:
        #     print(f"error {symbol} contract")
        # try:
        #     pool.apply_async(generate_contract_trading_data, args=(symbol, "1M"))
        #     # generate_contract_trading_data(symbol= symbol, interval= "1h")
        # except:
        #     print(f"error {symbol} contract")
        # try:
        #     pool.apply_async(generate_contract_trading_data, args=(symbol, "5m"))
        #     # pool.apply_async(generate_contract_trading_data, args=(symbol, "5m"))
        #     # generate_contract_trading_data(symbol= symbol, interval= "5m")
        # except:
        #     print(f"error {symbol} contract")
        # try:
        #     pool.apply_async(generate_markPrice_data, args=(symbol, "1h"))
        #     # generate_markPrice_data(symbol =symbol, interval= "1h")
        # except:
        #     print(f"error {symbol} markprice")
        # try:
        #     pool.apply_async(generate_premiumIndex_data, args=(symbol, "1h"))
        #     # generate_premiumIndex_data(symbol = symbol, interval= "1h")
        # except:
        #     print(print(f"error {symbol} Index"))
        # try:
        #     pool.apply_async(generate_premiumIndex_data, args=(symbol, "8h"))
        #     # generate_premiumIndex_data(symbol = symbol, interval= "8h")
        # except:
        #     print(print(f"error {symbol} Index"))
        # try:
        #     # generate_premiumIndex_data(symbol = symbol, interval= "1m")
        #     pool.apply_async(generate_premiumIndex_data, args=(symbol, "1m"))
        # except:
        #     print(print(f"error {symbol} Index"))
        # try:
        #     # pool.apply_async(generate_fundingRate_data, args=(symbol))
        #     generate_fundingRate_data(symbol = symbol)
        # except:
        #     print(f"error {symbol} fundingrate")
    # pool.close()
    # pool.join()