import requests
import pandas as pd
from datetime import datetime, timedelta
import json
from discord.ui import Select, View
import discord
import asyncio
import websockets

# date to ms
def datetime_to_millis(dt_str):
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    return int(dt.timestamp() * 1000)

def millis_to_datetime(ms): 
    dt = datetime.fromtimestamp(ms/1000)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# 返回特定时间段Binance的交易历史数据，klines
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
# 返回特定时间段OKX的历史交易数据，klines

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
#DEXscreener API
#返回价格
def get_coin_price(chain_id,token_address):
    # 构建查询的URL，平台和代币名称组合在一起
    chain_id = chain_id.lower()  # 转换为小写
    url = f"https://api.dexscreener.com/tokens/v1/{chain_id}/{token_address}"
    try:
        # 发送请求并获取响应
        response = requests.get(url)
        
        # 如果响应成功
        if response.status_code == 200:
            data = response.json()  # 将响应内容转换为JSON格式
            
            # 提取价格信息 (priceUsd)
            if data and isinstance(data, list):  # 如果数据是一个非空列表
                price_usd = data[0].get('priceUsd', 'N/A')  # 获取第一个对象中的 priceUsd
                return float(price_usd)
            else:
                print("No data found.")
        else:
            print(f"Error: Unable to fetch data (status code: {response.status_code})")
    
    except Exception as e:
        print(f"Error occurred: {e}")

# get the symbol and the create time of the coin
# result[0]=symbol, result[1]=create time
def get_coin_symbol_time(chain_id,token_address):
    chain_id = chain_id.lower()  # 转换为小写
    url=f"https://api.dexscreener.com/token-pairs/v1/{chain_id}/{token_address}"
    try:
        # 发送请求并获取响应
        response = requests.get(url)
        
        # 如果响应成功
        if response.status_code == 200:
            data = response.json()  # 将响应内容转换为JSON格式

            label = data[0].get('baseToken', 'N/A')  # 获取第一个对象中的 symbol
            symbol = label.get('symbol', 'N/A') # 获取第一个对象中的 symbol
            time = data[0].get('pairCreatedAt', 'N/A')
            time = millis_to_datetime(time)
            return symbol,time
        else:
            print(f"Error: Unable to fetch data (status code: {response.status_code})")
    
    except Exception as e:
        print(f"Error occurred: {e}")


# get the information of the latest coin
def get_latest_coin_info():
    url = "https://api.dexscreener.com/token-profiles/latest/v1"
    try:
        # 发送请求并获取响应
        response = requests.get(url)
        
        # 如果响应成功
        if response.status_code == 200:
            data = response.json()  # 将响应内容转换为JSON格式  
            latest_chain_id = None
            latest_address = None
            latest_symbol = None
            latest_time = None

            for item in data:
                chain_id=item.get('chainId', 'N/A')
                address = item.get('tokenAddress', 'N/A')
                time = get_coin_symbol_time(chain_id,address)[1]
                if  latest_time == None:
                    latest_time = time
                    latest_chain_id = chain_id
                    latest_address = address
                elif time > latest_time :
                    latest_time = time
                    latest_chain_id = chain_id
                    latest_address = address
                else:
                    continue
            
            latest_symbol = get_coin_symbol_time(latest_chain_id,latest_address)[0]
            data_set=[latest_chain_id, latest_address, latest_symbol, latest_time]
            return data_set
        else:
            print(f"Error: Unable to fetch data (status code: {response.status_code})")
    
    except Exception as e:
        print(f"Error occurred: {e}")

# reurn the liquidity and status of the coin
def get_coin_liquidity(chain_id,token_address):
    chain_id = chain_id.lower()  # 转换为小写
    url = f"https://api.dexscreener.com/tokens/v1/{chain_id}/{token_address}"
    try:
        # 发送请求并获取响应
        response = requests.get(url)
        
        # 如果响应成功
        if response.status_code == 200:
            data = response.json()  # 将响应内容转换为JSON格式
            
            # 提取价格信息 (priceUsd)
            if data and isinstance(data, list):  # 如果数据是一个非空列表
                liquidity = data[0].get('liquidity', 'N/A')  # 获取第一个对象中的 priceUsd
                liquidity= liquidity.get('usd','N/A')
                if liquidity != 'N/A':
                    liquidity=float(liquidity)
                    status = "listed"
                else:
                    status = "unlisted"
            data_set=[liquidity,status]
            return data_set
        else:
            print(f"Error: Unable to fetch data (status code: {response.status_code})")
    
    except Exception as e:
        print(f"Error occurred: {e}")




            
#-----------------------------------------------------------------------------------------------------------------------------
# pump.fun API,抄的，还没调试
async def subscribe():
  uri = "wss://pumpportal.fun/api/data"
  async with websockets.connect(uri) as websocket:
      
      # Subscribing to token creation events
      payload = {
          "method": "subscribeNewToken",
      }
      await websocket.send(json.dumps(payload))

      # Subscribing to migration events
      payload = {
          "method": "subscribeMigration",
      }
      await websocket.send(json.dumps(payload))

      # Subscribing to trades made by accounts
      payload = {
          "method": "subscribeAccountTrade",
          "keys": ["AArPXm8JatJiuyEffuC1un2Sc835SULa4uQqDcaGpAjV"]  # array of accounts to watch
      }
      await websocket.send(json.dumps(payload))

      # Subscribing to trades on tokens
      payload = {
          "method": "subscribeTokenTrade",
          "keys": ["91WNez8D22NwBssQbkzjy4s2ipFrzpmn5hfvWVe2aY5p"]  # array of token CAs to watch
      }
      await websocket.send(json.dumps(payload))
      
      async for message in websocket:
          print(json.loads(message))

# Run the subscribe function
#asyncio.get_event_loop().run_until_complete(subscribe())


