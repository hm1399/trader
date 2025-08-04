# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these imports ---
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from pandas import DataFrame
from typing import Optional, Union

from freqtrade.strategy import (
    IStrategy,
    Trade,
    Order,
    PairLocks,
    informative,  # @informative decorator
    # Hyperopt Parameters
    BooleanParameter,
    CategoricalParameter,
    DecimalParameter,
    IntParameter,
    RealParameter,
    # timeframe helpers
    timeframe_to_minutes,
    timeframe_to_next_date,
    timeframe_to_prev_date,
    # Strategy helper functions
    merge_informative_pair,
    stoploss_from_absolute,
    stoploss_from_open,
)

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
from technical import qtpylib


# This class is a sample. Feel free to customize it.
class SuperTrendStrategy(IStrategy):

    # Strategy interface version - allow new iterations of the strategy interface.
    # Check the documentation or the Sample strategy to get the latest version.
    INTERFACE_VERSION = 3

    # Can this strategy go short?
    can_short: bool = False 

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi".
    minimal_roi = {
        "0":100
    }

    # Optimal stoploss designed for the strategy.
    # This attribute will be overridden if the config file contains "stoploss".
    stoploss = -0.5 #disable

    # Trailing stoploss
    trailing_stop = False
    trailing_only_offset_is_reached = True
    trailing_stop_positive = 0.3
    trailing_stop_positive_offset = 0.4

    # Optimal timeframe for the strategy.
    timeframe = "15m"

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = True

    # These values can be overridden in the config.
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # parameters
    Periods = 100
    src = 'hl2' #from Pine script (high+low)/2
    Multiplier = 3.0
    changeATR = True
    showsignals = True
    highlighting = True
    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 200

    # Optional order type mapping.
    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    # Optional order time in force.
    order_time_in_force = {"entry": "GTC", "exit": "GTC"}


    def informative_pairs(self):
        """
        輔助交易對
        Define additional, informative pair/interval combinations to be cached from the exchange.
        These pair/interval combinations are non-tradeable, unless they are part
        of the whitelist as well.
        For more information, please consult the documentation
        :return: List of tuples in the format (pair, interval)
            Sample: return [("ETH/USDT", "5m"),
                            ("BTC/USDT", "15m"),
                            ]
        """
        return []


    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # --- 1. 计算 ATR
        if self.changeATR:
            atr = ta.ATR(dataframe['high'], dataframe['low'], dataframe['close'],
                        timeperiod=self.Periods)
        else:
            atr = ta.SMA(dataframe['tr'], timeperiod=self.Periods)

        # --- 2. 计算 raw_up/raw_dn
        if self.src == 'hl2':
            src = (dataframe['high'] + dataframe['low']) / 2
        else:
            src = dataframe[self.src]

        raw_up = src - self.Multiplier * atr
        raw_dn = src + self.Multiplier * atr

        # --- 3. 准备容器
        n = len(dataframe)
        final_up    = np.zeros(n)
        final_dn    = np.zeros(n)
        trend       = np.ones(n, dtype=int)

        closes = dataframe['close'].values

        # --- 4. 逐根迭代
        final_up[0] = raw_up.iloc[0]
        final_dn[0] = raw_dn.iloc[0]
        trend[0]    = 1

        for i in range(1, n):
            # 4.1 根据前一根的边界和 raw 计算 up/dn
            if closes[i-1] > final_up[i-1]:
                final_up[i] = max(raw_up.iloc[i], final_up[i-1])
            else:
                final_up[i] = raw_up.iloc[i]

            if closes[i-1] < final_dn[i-1]:
                final_dn[i] = min(raw_dn.iloc[i], final_dn[i-1])
            else:
                final_dn[i] = raw_dn.iloc[i]

            # 4.2 根据前一根 trend 和 当前 close 决定新 trend
            if trend[i-1] == -1 and closes[i] > final_dn[i-1]:
                trend[i] = 1
            elif trend[i-1] ==  1 and closes[i] < final_up[i-1]:
                trend[i] = -1
            else:
                trend[i] = trend[i-1]

        # --- 5. 写回 DataFrame
        dataframe['up']    = final_up
        dataframe['dn']    = final_dn
        dataframe['trend'] = trend

        # --- 6. 生成信号
        dataframe['buySignal']  = (dataframe['trend'] == 1) & (dataframe['trend'].shift(1) == -1)
        dataframe['sellSignal'] = (dataframe['trend'] == -1) & (dataframe['trend'].shift(1) ==  1)

        return dataframe


    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the entry signal for the given dataframe
        :param dataframe: DataFrame
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with entry columns populated
        """
        dataframe.loc[
            (
                dataframe['buySignal'] == True
            ),
            "enter_long",
        ] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the exit signal for the given dataframe
        :param dataframe: DataFrame
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with exit columns populated
        """
        dataframe.loc[
            (
                dataframe['sellSignal'] == True
            ),
            "exit_long",
        ] = 1

        return dataframe
