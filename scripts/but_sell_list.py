import os

def get_symbol(print_str):
    position=print_str.find("USDT")
    return print_str[7:position+4] #返回对应symbol
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

trading_list = ['DYDXUSDT', 'SOLUSDT', 'BCHUSDT', 'UNIUSDT', 'ETCUSDT', 'AAVEUSDT', 'VETUSDT', 'ALGOUSDT', 'OPUSDT',
                'XTZUSDT', 'SANDUSDT', 'XECUSDT', 'CFXUSDT', 'STXUSDT', 'FILUSDT', 'APTUSDT', '1000FLOKIUSDT',
                '1000BONKUSDT', 'BSVUSDT', 'FLOWUSDT', 'NOTUSDT', 'EGLDUSDT', 'GALAUSDT', 'ARUSDT',
                'ILVUSDT', 'AIUSDT', 'IDUSDT', 'PORTALUSDT', 'NMRUSDT', 'PEOPLEUSDT', 'WAXUSDT', 'GMTUSDT', 'ZENUSDT',
                'BOMEUSDT', 'ARBUSDT', '1000SHIBUSDT', 'MKRUSDT', '1000XECUSDT', 'WAXPUSDT', 'WIFUSDT', 'ETHUSDT',
                'AVAXUSDT']
print_list=["Symbol:DOGEUSDT, now:2024-09-16 12:29:13 last_short:2024-09-16 11:59:59",
            "Symbol:BTCUSDT, now:2024-09-16 12:29:13 last_long:2024-09-16 11:59:59",
            "Symbol:XRPUSDT, now:2024-09-16 12:29:13 last_short:2024-09-16 11:59:59",
            "Symbol:ILVUSDT, now:2024-09-16 12:29:13 last_stop:2024-09-16 11:59:59",
            "Symbol:SANDUSDT, now:2024-09-16 12:29:13 last_stop:2024-09-16 11:59:59",]
trading_dict = {'buy': {}, 'sell': {}}
for idx, print_str in enumerate(print_list):
    if "long" in print_str:
        print(f"%d. {bcolors.OKGREEN}%s{bcolors.ENDC}" % (idx + 1, print_str))  # print with green
        trading_dict['buy'][idx+1] = get_symbol(print_str)
    elif "short" in print_str:
        print(f"%d. {bcolors.FAIL}%s{bcolors.ENDC}" % (idx + 1, print_str))  # print with red
        trading_dict['buy'][idx+1] = get_symbol(print_str)
    else:
        print(f"%d. {bcolors.OKBLUE}%s{bcolors.ENDC}" % (idx + 1, print_str))  # print with blue
        trading_dict['sell'][idx+1] = get_symbol(print_str)
print('testing')
buy_list_str = input("Input Buy List:")
buy_list = [int(num) for num in buy_list_str.split(' ')]
sell_list_str = input("Input Sell List:")
sell_list = [int(num) for num in sell_list_str.split(' ')]
print(buy_list_str)
print(sell_list_str)
for trading_id in buy_list:
    symbol=trading_dict['buy'][trading_id]
    trading_list.append(symbol)
for trading_id in sell_list:
    symbol=trading_dict['sell'][trading_id]
    trading_list.remove(symbol)
print('Trading List:')
print(trading_list)