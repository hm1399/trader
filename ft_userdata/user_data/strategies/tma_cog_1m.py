from freqtrade.strategy import IStrategy
import pandas as pd
import numpy as np
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TMACOGStrategy(IStrategy):
    # Strategy parameters
    INTERFACE_VERSION = 2
    timeframe = "1m"  # From config
    minimal_roi = {"0": 0.02}  # From take_profit_percent
    stoploss = -0.01  # From stop_loss_percent
    trailing_stop = False
    can_short = False #True  # Enable shorting  #Not available

    # Custom parameters from config.json
    window = 56
    bands_deviations = 1.2
    ma_period = 14
    ma_method = "SMA"
    use_tma = True
    use_ma_filter = True
    stop_loss_percent = 0.01
    take_profit_percent = 0.02
    risk_per_trade = 0.01
    close_on_opposite = True
    join_ongoing_trends = True

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        # Calculate TMA
        tma_len = int(round(self.window / 2)) + 1
        sma1 = dataframe['close'].rolling(window=tma_len, min_periods=1).mean()
        dataframe['tma'] = sma1.rolling(window=tma_len, min_periods=1).mean()

        # Calculate COG
        cog_series = pd.Series([np.nan] * len(dataframe))
        for i in range(self.window - 1, len(dataframe)):
            src = dataframe['close'].iloc[i - self.window + 1:i + 1]
            num = sum((1 + j) * src.iloc[-1 - j] for j in range(self.window))
            den = sum(src)
            cog_series.iloc[i] = -num / den + (self.window + 1) / 2.0 if den != 0 else np.nan
        dataframe['cog'] = cog_series

        # TMA on COG
        dataframe['tma_cog'] = self.calculate_tma(dataframe['cog'], self.window)

        # MA filter
        dataframe['ma'] = self.calculate_ma(dataframe['close'], self.ma_period, self.ma_method)

        # TMA bands and histogram
        std = dataframe['close'].rolling(window=self.window).std()
        dataframe['upper_band'] = dataframe['tma'] + self.bands_deviations * std
        dataframe['lower_band'] = dataframe['tma'] - self.bands_deviations * std
        dataframe['histo'] = np.where(dataframe['close'] > dataframe['upper_band'], 1,
                                      np.where(dataframe['close'] < dataframe['lower_band'], -1, 0))

        return dataframe

    def calculate_tma(self, series: pd.Series, window: int) -> pd.Series:
        tma_len = int(round(window / 2)) + 1
        sma1 = series.rolling(window=tma_len, min_periods=1).mean()
        return sma1.rolling(window=tma_len, min_periods=1).mean()

    def calculate_ma(self, series: pd.Series, period: int, method: str) -> pd.Series:
        if method == 'SMA':
            return series.rolling(window=period, min_periods=1).mean()
        elif method == 'EMA':
            return series.ewm(span=period, adjust=False, min_periods=1).mean()
        elif method == 'WMA':
            def wma_func(x):
                if len(x) == 0:
                    return np.nan
                weights = np.arange(1, len(x) + 1)
                return np.dot(x, weights) / weights.sum()
            return series.rolling(window=period, min_periods=1).apply(wma_func, raw=True)
        else:
            raise ValueError(f"Invalid MA method: {method}")

    def crossover(self, series1: pd.Series, series2: pd.Series) -> pd.Series:
        return (series1.shift(1) <= series2.shift(1)) & (series1 > series2)

    def crossunder(self, series1: pd.Series, series2: pd.Series) -> pd.Series:
        return (series1.shift(1) >= series2.shift(1)) & (series1 < series2)

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe['enter_long'] = 0
        dataframe['enter_short'] = 0

        # Buy (Long) signal
        buy_condition = self.crossover(dataframe['cog'], dataframe['tma_cog']) & \
                        ((~self.use_tma) | (dataframe['histo'] != 0)) & \
                        ((~self.use_ma_filter) | (dataframe['close'] > dataframe['ma']))
        ongoing_buy = self.join_ongoing_trends & (dataframe['cog'] > dataframe['tma_cog']) & \
                      ((~self.use_tma) | (dataframe['histo'] == 1)) & \
                      ((~self.use_ma_filter) | (dataframe['close'] > dataframe['ma']))
        dataframe.loc[buy_condition | ongoing_buy, 'enter_long'] = 1

        # Sell (Short) signal
        sell_condition = self.crossunder(dataframe['cog'], dataframe['tma_cog']) & \
                         ((~self.use_tma) | (dataframe['histo'] != 0)) & \
                         ((~self.use_ma_filter) | (dataframe['close'] < dataframe['ma']))
        ongoing_sell = self.join_ongoing_trends & (dataframe['cog'] < dataframe['tma_cog']) & \
                       ((~self.use_tma) | (dataframe['histo'] == -1)) & \
                       ((~self.use_ma_filter) | (dataframe['close'] < dataframe['ma']))
        dataframe.loc[sell_condition | ongoing_sell, 'enter_short'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe['exit_long'] = 0
        dataframe['exit_short'] = 0

        if self.close_on_opposite:
            # Exit long on short signal
            sell_condition = self.crossunder(dataframe['cog'], dataframe['tma_cog']) & \
                             ((~self.use_tma) | (dataframe['histo'] != 0)) & \
                             ((~self.use_ma_filter) | (dataframe['close'] < dataframe['ma']))
            ongoing_sell = self.join_ongoing_trends & (dataframe['cog'] < dataframe['tma_cog']) & \
                           ((~self.use_tma) | (dataframe['histo'] == -1)) & \
                           ((~self.use_ma_filter) | (dataframe['close'] < dataframe['ma']))
            dataframe.loc[sell_condition | ongoing_sell, 'exit_long'] = 1

            # Exit short on buy signal
            buy_condition = self.crossover(dataframe['cog'], dataframe['tma_cog']) & \
                            ((~self.use_tma) | (dataframe['histo'] != 0)) & \
                            ((~self.use_ma_filter) | (dataframe['close'] > dataframe['ma']))
            ongoing_buy = self.join_ongoing_trends & (dataframe['cog'] > dataframe['tma_cog']) & \
                          ((~self.use_tma) | (dataframe['histo'] == 1)) & \
                          ((~self.use_ma_filter) | (dataframe['close'] > dataframe['ma']))
            dataframe.loc[buy_condition | ongoing_buy, 'exit_short'] = 1

        return dataframe

    def custom_stoploss(self, pair: str, trade: 'Trade', current_time: datetime,
                        current_rate: float, current_profit: float, **kwargs) -> float:
        # Implement fixed stop-loss percent
        return self.stop_loss_percent

    def leverage(self, pair: str, current_time: datetime, current_rate: float,
                 proposed_leverage: float, max_leverage: float, side: str, **kwargs) -> float:
        return 1.0  # Adjust if leverage is needed