import pandas as pd
from api import get_binance_data,get_okx_data

class Trader:
    def __init__(self, exchange='binance', initial_capital=10000.0, symbol="BTCUSDT", interval="1m",
                 start_time=None, end_time=None):
        self.capital = initial_capital    # 初始余额默认为10000
        self.position = 0.0               # 持仓数量，默认为空仓
        self.entry_price = 0.0            # 建仓时价格
        self.symbol = symbol
        self.exchange = exchange          # 交易所
        self.interval = interval          # klines 的时间间隔
        self.start_time = start_time
        self.end_time = end_time

        if exchange == 'binance':
            self.df = get_binance_data(start_time, end_time, interval, "BTCUSDT")
        elif exchange == 'okx':
            self.df = get_okx_data(start_time, end_time, interval,"BTC-USDT")
        else:
            raise ValueError("Unsupported exchange")

    # short/long_window 代表最近n个收盘价
    def ma_cross_strategy(self, short_window=5, long_window=20):
        df = self.df.copy()
        # 最近n个收盘价的平均值，并命名为 "ma_shout" 和 "ma_long" 储存在df里（没有改变原来的df）
        df["ma_short"] = df["close"].rolling(short_window).mean()
        df["ma_long"] = df["close"].rolling(long_window).mean()
        return df


    async def simulate_trades(self, notify, short_window=5, long_window=20):
        # 获取 ma_short 和 ma_long
        df = self.ma_cross_strategy(short_window, long_window)

        # 对于每一行数据
        for i in range(len(df)):
            price = df["close"].iloc[i]
            time = df["time"].iloc[i]
            ma_short = df["ma_short"].iloc[i]
            ma_long = df["ma_long"].iloc[i]

            # 买入条件
            if ma_short > ma_long and self.position == 0:
                self.position = self.capital / price  # 花光资金买入
                self.entry_price = price              # 记录入场的价位
                self.capital = 0
                await notify(f"💰 BUY at {price:.2f} on {time}", price, self.position, self.capital, 0)

            # 卖出条件
            elif ma_short < ma_long and self.position > 0:
                self.capital = self.position * price
                profit = self.capital - (self.entry_price * self.position)
                profit_percent = (profit / (self.entry_price * self.position)) * 100
                await notify(
                    f"💸 SELL at {price:.2f} on {time}\nProfit: ${profit:.2f} ({profit_percent:.2f}%)",
                    price, 0, self.capital, profit
                )
                self.position = 0

        # 最后强制结算如果还持仓
        if self.position > 0:
            final_price = df["close"].iloc[-1]
            self.capital = self.position * final_price
            profit = self.capital - (self.entry_price * self.position)
            profit_percent = (profit / (self.entry_price * self.position)) * 100
            await notify(
                f"🏁 CLOSE at {final_price:.2f} (forced)\nProfit: ${profit:.2f} ({profit_percent:.2f}%)",
                final_price, 0, self.capital, profit
            )
            self.position = 0
