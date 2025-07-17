import requests
import pandas as pd
from datetime import datetime, timedelta
import json
from discord.ui import Select, View
import discord

# date to ms
def datetime_to_millis(dt_str):
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    return int(dt.timestamp() * 1000)

# 返回特定时间段Binance的交易数据，klines
def get_binance_data(start_time=None, end_time=None, interval="1m", symbol="BTCUSDT"):
    # 默认时间段为最新的30天
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(days=30)

    # API for binance
    url = "https://api.binance.com/api/v3/klines"

    # 请求数据的参数
    params = {
        "symbol": symbol, # 交易对符号
        "interval": interval, # 时间间隔：多长时间的k线
        "startTime": int(start_time.timestamp() * 1000), #毫秒时间戳
        "endTime": int(end_time.timestamp() * 1000)
    }

    # 把请求回来的数据当作 JSON 格式解析，转为 Python 数据结构，并存在data里
    res = requests.get(url, params=params)
    data = res.json()

    # 把data里的数据转换成结构化 pandas Data Frame
    ''' time, close_time: 开盘时间， 收盘时间
        open, high, low, close : 开、高、低、收盘价(string)
        volume: 成交量
        volume_currency: 成交额
        trade_count: 交易笔数
        taker_buy_base: 主动买入的成交量
        taker_buy_quote: 主动买入的成交额
        ignore: 忽略字段
    '''
    df = pd.DataFrame(data, columns=[
        "time", "open", "high", "low", "close", "volume",
        "close_time", "volume_currency", "trade_count",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])


    df["close"] = df["close"].astype(float)
    # 将毫秒的开盘时间转为标准的日期时间格式
    df["time"] = pd.to_datetime(df["time"], unit="ms")

    return df

#--------------------------------------------------------------------------------------------------------------
# 返回特定时间段OKX的交易数据，klines

def get_okx_data(start_time=None, end_time=None, interval="1m", symbol="BTC-USD"):

    if end_time is None:
        end_time= datetime.utcnow()
        print(end_time)
        
    if start_time is None:
        start_time =  end_time - timedelta(days=30)
        print(start_time)

    # 换成毫秒再转成string
    int_start_time = int(start_time.timestamp() * 1000)
    int_end_time = int(end_time.timestamp() * 1000)
    start_time = str(int_start_time)
    end_time = str(int_end_time)

    # 请求参数
    url = "https://www.okx.com/api/v5/market/history-index-candles"
    params = {
        "instId": symbol,
        "after": end_time,
        "before": start_time,
        "bar": interval,
        "limit": "100"
    }

    res = requests.get(url, params=params, timeout=10)

    data_json = res.json()
    data = data_json["data"][::-1]  # 翻转为时间正序
    df = pd.DataFrame(data, columns=[
        "time", "open", "high", "low", "close", "confirm"
    ])
    df["close"] = df["close"].astype(float)
    df["time"] = pd.to_datetime(df["time"], unit="ms")

    return df


#-----------------------------------------------------------------------------------------------------------------------------

""""
def get_dex_data(chain_id, token_address):

    url = f"https://api.dexscreener.com/token-pairs/v1/{chain_id}/{token_address}"
    try:
        response = requests.get(url)
        data = response.json()
        if response.status_code == 200 and "data" in data:
            price_data = data["data"]
            if price_data:
                return float(price_data[0]['price'])
            else:
                return None
        else:
            return None
    except Exception as e:
        return None

"""

