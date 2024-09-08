import requests
proxy_ip="http://127.0.0.1:7777"
proxies={"http":proxy_ip}
url='https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&endTime=1710975546000&limit=1500'
response = requests.get(url,proxies=proxies)
print(response)