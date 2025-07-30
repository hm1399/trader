import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from discord.ui import Select, View
import discord
import asyncio
import websockets
import ccxt.pro as ccxtpro
import ccxt  
import time
import yfinance as yf
import re

# date to ms
def datetime_to_millis(dt_str):
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    return int(dt.timestamp() * 1000)

def millis_to_datetime(ms): 
    dt = datetime.fromtimestamp(ms/1000)
    return dt.strftime("%Y-%m-%d %H:%M:%S")
#---------------------------------------------------------------------------------------------------------------------------------------
# 返回特定时间段Binance的交易历史数据，klines
def get_binance_hist(start_time=None, end_time=None, interval="1m", symbol="BTCUSDT"):
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

#获得某个交易对的实时价格
def get_binance_real(symbol="BTCUSDT"):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    response = requests.get(url)
    data = response.json()
    return data


#获取交易额排名范围的交易对，24小时涨幅
#'quoteVolume'
def get_vol_rank(start:int=1, end:int=10, symbol:str=None):
    url = "https://api.binance.com/api/v3/ticker/24hr"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data)

    data_rank = []
    symbol_rank=[]
    rank=[]
    # 转换字段为 float 类型
    df['lastPrice'] = pd.to_numeric(df['lastPrice'], errors='coerce')
    df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
    df['quoteVolume'] = pd.to_numeric(df['quoteVolume'], errors='coerce')
    df['priceChangePercent'] = pd.to_numeric(df['priceChangePercent'], errors='coerce')

    # 过滤掉价格和成交额为 0 的数据
    df = df[(df['lastPrice'] > 0) & (df['quoteVolume'] > 0)]

    # 排序（按成交额从高到低）
    df_sorted = df.sort_values(by='quoteVolume', ascending=False).reset_index(drop=True)
    total = len(df_sorted)
    if symbol:
        matched_symbols = df_sorted[df_sorted['symbol'].str.contains(symbol, case=False, na=False)]

        if matched_symbols.empty:
            return f"No symbols found matching '{symbol}' in the market data."

        
        for i, row in matched_symbols.iterrows():
            rank = row.name + 1  # 获取排名，name对应的是行的索引
            print(f"The symbol '{row['symbol']}' is ranked #{rank} by 24h quote volume.")
            symbol_rank.append(rank)

         
    # 支持负数索引
    if start < 0 and end < 0:
        re_start = total + start
        re_end = total + end
        # 确保从较小索引切到较大索引
        re_start, re_end = sorted([re_start, re_end])
        subset = df_sorted.iloc[re_start:re_end][::-1]

    elif start >= 0 and end >= 0:
        re_start, re_end = sorted([start, end])
        subset = df_sorted.iloc[re_start:re_end]

    elif symbol:
        return [data_rank, symbol_rank]
    else:
        return "Invalid input: Please input either two positive integers or two negative integers."

    # 打印输出
    print(f"\nTrading pairs ranked from {start} to {end} by 24h Quote Volume:\n")
    for i, row in enumerate(subset.itertuples(index=False), 1):
        data_rank.append(row)
        print(f"{i}. {row.symbol}:")
        print(f"   - Last Price        : {row.lastPrice}")
        print(f"   - 24h Volume        : {row.volume}")
        print(f"   - 24h Quote Volume  : {row.quoteVolume}")
        print(f"   - Change Percent    : {row.priceChangePercent}%\n")

    return [data_rank, symbol_rank]


#'priceChangePercent'
# 返回以pricechange为排名的交易对信息，24小时涨幅
def get_change_rank(start:int=0, end:int=10):
    url = "https://api.binance.com/api/v3/ticker/24hr"
    response = requests.get(url)
    data = response.json()

    df = pd.DataFrame(data)

    # 转换字段为 float 类型
    df['lastPrice'] = pd.to_numeric(df['lastPrice'], errors='coerce')
    df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
    df['quoteVolume'] = pd.to_numeric(df['quoteVolume'], errors='coerce')
    df['priceChangePercent'] = pd.to_numeric(df['priceChangePercent'], errors='coerce')

    # 过滤掉价格和成交额为 0 的数据
    df = df[(df['lastPrice'] > 0) & (df['quoteVolume'] > 0)]

    # 排序（按成交额从高到低）
    df_sorted = df.sort_values(by='priceChangePercent', ascending=False).reset_index(drop=True)

    total = len(df_sorted)

    # 支持负数索引
    if start < 0 and end < 0:
        re_start = total + start
        re_end = total + end
        # 确保从较小索引切到较大索引
        re_start, re_end = sorted([re_start, re_end])
        subset = df_sorted.iloc[re_start:re_end][::-1]

    elif start >= 0 and end >= 0:
        re_start, re_end = sorted([start, end])
        subset = df_sorted.iloc[re_start:re_end]

    else:
        return "Invalid input: Please input either two positive integers or two negative integers."

    # 打印输出
    print(f"\nTrading pairs ranked from {start} to {end} by 24h Quote Volume:\n")
    for i, row in enumerate(subset.itertuples(index=False), 1):
        print(f"{i+1}. {row.symbol}:")
        print(f"   - Last Price        : {row.lastPrice}")
        print(f"   - 24h Volume        : {row.volume}")
        print(f"   - 24h Quote Volume  : {row.quoteVolume}")
        print(f"   - Change Percent    : {row.priceChangePercent}%\n")

    return subset






#-----------------------------------------------------------------------------------------------------------
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
    

# get the symbol and the create time of the coin
# result[0]=symbol, result[1]=create time
def get_coin_symbol_time(chain_id,token_address):
    chain_id = chain_id.lower()  # 转换为小写
    url=f"https://api.dexscreener.com/token-pairs/v1/{chain_id}/{token_address}"

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
    


# get the information of the latest coin
def get_latest_coin_info():
    url = "https://api.dexscreener.com/token-profiles/latest/v1"
    try:
        # 发送请求并获取响应
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()  # 将响应内容转换为JSON格式  
            df = []
            for item in data:
                try:
                    chain_id=item.get('chainId', 'N/A')
                    address = item.get('tokenAddress', 'N/A')
                    df.append(get_coin_symbol_time(chain_id,address)+(address,chain_id))
                    
                except Exception as e:
                    print(f"Error occurred: {e}")
                    continue
            
            df.sort(key=lambda x: x[1], reverse=True)
            latest_symbol = df[0][0]
            latest_time = df[0][1]
            latest_address = df[0][2]
            latest_chain_id = df[0][3]
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


#-----------------------------------------------------------------------------------------------------------------------------------------------
# ccxt data

# 根据交易所来寻找交易对
def get_pair_name(exchange_name: str) -> list:
    """
    返回指定交易所支持的所有交易对名称列表。
    :param exchange_name: ccxt.exchanges 中的交易所标识字符串，比如 "binance"、"okx"。
    :return: 交易对名称的 list,例如 ["BTC/USDT", "ETH/BTC", ...]；如果交易所不存在则返回空列表。
    """
    exchange_name = exchange_name.lower()  # 转换为小写
    all_exchanges = ccxt.exchanges
    # 检查交易所是否支持
    if exchange_name not in all_exchanges:
        print(f"Exchange '{exchange_name}' not found.\n please enter one of the following exchanges: {all_exchanges}")
        return []

    # 动态获取交易所类并实例化
    exchange_class = getattr(ccxt, exchange_name)
    this_exchange = exchange_class({
        'enableRateLimit': True,
    })

    # 同步加载市场（markets 是个 dict，键即是交易对名称）
    markets = this_exchange.load_markets()

    # 直接把 dict 的 key 转成 list 返回
    pair_list = list(markets.keys())
    return pair_list


def get_funding_rate(exchange_name: str, symbol: str):
    exchange_name = exchange_name.lower()  # 转换为小写
    symbol = symbol.upper()  # 转换为大写
    exchange_class = getattr(ccxt, exchange_name)
    this_exchange = exchange_class({
        'enableRateLimit': True,
    })

    this_exchange.options['defaultType'] = 'future'  # coinm contracts
    try:
        funding_rate = this_exchange.fetchFundingRate(symbol)
        return funding_rate['fundingRate']
    except ccxt.ExchangeError as e:
        print(f"获取资金费率失败: {e}")





# 获取时间段内某一个交易对的所有数据
# return [[time, open, high, low, close, volume],...]
# 例如拿close数据
# close_prices = [row[3] for row in data]
def get_ccxt_data(exchange: str, symbol: str, period: str, timeframe: str):
    exchange = exchange.lower()  # 转换为小写
    symbol = symbol.upper()  # 转换为大写
    pair_list=get_pair_name(exchange)
    if symbol == None:
        print("Symbol not found.")
        return None
    # 如果交易对不在ccxt交易所列表中，则返回None
    elif symbol not in pair_list:
        print(f"Symbol not found in {exchange}.")
        return None
    else:
        exchange_class = getattr(ccxt, exchange)
        this_exchange = exchange_class({
            'enableRateLimit': True,
        })
    minutes = parse_period_to_minutes(period)  # 例如 '1y' → 525600 分钟
    since = this_exchange.milliseconds() - minutes * 60 * 1000

    all_ohlcv = []
    while True:
        ohlcv = this_exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=1000)
        if not ohlcv:
            break
        all_ohlcv += ohlcv
        since = ohlcv[-1][0] + 1
        time.sleep(this_exchange.rateLimit / 1000)
        if len(ohlcv) < 1000:
            break

    return all_ohlcv

    

# 根据交易对名称获取相关实时数据，返回一条数据组
def get_latest_data(exchange:str,symbol: str):
    exchange = exchange.lower()  # 转换为小写
    symbol = symbol.upper()  # 转换为大写
    pair_list=get_pair_name(exchange)
    if symbol == None:
        print("Symbol not found.")
        return None
    # 如果交易对不在ccxt交易所列表中，则返回None
    elif symbol not in pair_list:
        print(f"Symbol not found in {exchange}.")
        return None
    else:
        exchange_class = getattr(ccxt, exchange)
        this_exchange = exchange_class({
            'enableRateLimit': True,
        })

    #print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    data = this_exchange.fetch_ticker(symbol)# 获取比特币/美元的数据
    high = data.get('high','N/A') #最近 24 小时内的最高价
    low = data.get('low','N/A') #最近 24 小时内的最低价
    open=data.get('open','N/A') #24 小时之前的开盘价
    close=data.get('close','N/A') #最新成交价,在某些交易所可能与 last 相同
    last=data.get('last','N/A') #最新成交价
    previousClose=data.get('previousClose','N/A') #上一交易日的收盘价
    average=data.get('average','N/A') # （open + close）/ 2 的简单平均价
    rate=get_funding_rate(exchange,symbol) # 资金费率
    data_set=[high,low,open,close,last,previousClose,average,rate]
    return data_set


# 1e 为1个月
def parse_period_to_minutes(period: str) -> int:
    match = re.match(r'(\d+)([mhdwey])', period.lower())
    if not match:
        raise ValueError("周期格式错误，应为如 '1m','1h','1d','1w', '1e', '1y'")
    value, unit = int(match.group(1)), match.group(2)
    if unit == 'm':
        return value
    elif unit == 'h':
        return value * 60
    elif unit == 'd':
        return value * 60 * 24
    elif unit == 'w':
        return value * 7 * 60 * 24
    elif unit == 'e':
        return value * 30 * 60 * 24
    elif unit == 'y':
        return value * 24* 30 * 60 * 24
    



    
#对数收益率波动率（百分比波动）, 利于不同币种之间做比较
def get_volatility(period: str, exchange: str, symbol: str):
    
    exchange = exchange.lower()  
    symbol = symbol.upper()  
    pair_list=get_pair_name(exchange)
    if symbol == None:
        print("Symbol not found.")
        return None
    # 如果交易对不在ccxt交易所列表中，则返回None
    elif symbol not in pair_list:
        print(f"Symbol not found in {exchange}.")
        return None
    else:
        exchange_class = getattr(ccxt, exchange)
        this_exchange = exchange_class({
            'enableRateLimit': True,
        })

    timeframe=None
    minutes = parse_period_to_minutes(period)
    since = this_exchange.milliseconds() - minutes * 60 * 1000

    # 自动选择 timeframe
    if minutes < 3: 
        print("The period is too short, please choose a period longer than 3 minutes.")
        return None
    elif minutes <= 60: # 1h
        timeframe = '1m'
        unit_minutes = 1
    elif minutes <= 24 * 60: # 1d
        timeframe = '1h'
        unit_minutes = 60
    elif minutes <= 7 * 24 * 60: # 7d
        timeframe = '6h'
        unit_minutes = 60*6
    elif minutes <= 365 * 24 * 60: # 1y
        timeframe = '1d'
        unit_minutes = 60*24
    else:
        timeframe = '1w'
        unit_minutes = 60*24*7

    ohlcv = this_exchange.fetch_ohlcv(symbol.upper(), timeframe=timeframe, since=since, limit=1000)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['log_return'] = np.log(df['close'] / df['close'].shift(1))
    df.dropna(inplace=True)

    std_log_return = df['log_return'].std()
    sample_minutes = len(df) * unit_minutes
    annual_minutes = 365 * 24 * 60
    scale = np.sqrt(annual_minutes / sample_minutes)
    print(f"Annualized volatility: {std_log_return * scale * 100:.2f}%")
    return std_log_return * scale * 100  

#-------------------------------------------------------------------------------------------------------------------------------------------------------
# jupyter API


#[symbol,dev（开发者钱包）,launchpad,firstPool_createdAt,topHoldersPercentage(以放大100),usdPrice,liquidity,priceChange_5m,priceChange_24h]
def get_jup_data(address:str):
    url = f"https://lite-api.jup.ag/ultra/v1/search?query={address}"

    headers = {
    'Accept': 'application/json'
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code == 200:
        data = response.json()  # 将响应内容转换为JSON格式
        
        if not isinstance(data, list):
            raise Exception("Unexpected data format from API")

        symbol= data[0].get("symbol")
        dev= data[0].get("dev")
        launchpad= data[0].get("launchpad")
        firstPool_createdAt= data[0].get("firstPool", {}).get("createdAt")
        topHoldersPercentage= data[0].get("audit", {}).get("topHoldersPercentage")
        usdPrice= data[0].get("usdPrice")
        liquidity= data[0].get("liquidity"),
        priceChange_5m= data[0].get("stats5m", {}).get("priceChange"),
        priceChange_24h= data[0].get("stats24h", {}).get("priceChange"),
        dataset = [symbol,dev,launchpad,firstPool_createdAt,topHoldersPercentage,usdPrice,liquidity[0],priceChange_5m[0],priceChange_24h[0]]
        print(f"symbol:{symbol},dev:{dev},launchpad:{launchpad},firstPool_createdAt:{firstPool_createdAt},topHoldersPercentage:{topHoldersPercentage},usdPrice:{usdPrice},liquidity:{liquidity},priceChange_5m:{priceChange_5m},priceChange_24h:{priceChange_24h}")
    else:
        print(f"Error: Unable to fetch data (status code: {response.status_code})")
    
    return dataset