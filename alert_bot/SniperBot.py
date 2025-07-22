from api import get_coin_price, get_coin_symbol_time, get_coin_liquidity,get_latest_coin_info
from database import *
import time

""" 1.从get_latest_coin_info()获取币种信息
    2. 加入TABLE PROGRESS,获取liquidity信息,判断新币状态（上没上市）
    3. 声明初始资金，设置买卖条件，执行交易（利润）
    4. 检查progress里每条数据的发币时间,超过一天直接删除
    5. 加入TABLE ALERT,记录交易信息，发送通知
    6. 可选择状态：只在货币上市后开始买卖
    7. 要不断刷新liquidity信息
    8. 不断刷新新币的信息,监测progress表里的liquidity变化,判断是否有交易机会
    9. 买入条件: liquidity > 20000且发行时间不到10分钟。
    10. 卖出条件: liquidity < 20000, 或者利润超过10%。
    11. 交易逻辑：先卖出，再买入。
    12. 记录交易信息，发送通知。
    13. 定时任务:每隔1分钟刷新一次信息,检查是否有交易机会。
"""
class SniperBot:
    def __init__(self, initial_capital, token_status = "listed", profit=0.10, liquidity=20000):
        self.capital = initial_capital
        self.token_status = token_status #listed or unlisted
        self.profit = None
        self.liquidity = liquidity

    #get information of new coin
    def get_new_coin_info(self):
        global new_coin 
        global new_coin_chain_id
        global new_coin_address
        global new_coin_symbol
        global new_coin_time
        global new_coin_price
        global new_coin_liquidity
        global new_coin_status
        new_coin =  get_latest_coin_info() #chain_id,address,symbol,time
        new_coin_chain_id=new_coin[0]
        new_coin_address=new_coin[1]
        new_coin_symbol=new_coin[2]
        new_coin_time=new_coin[3]
        new_coin_status = get_coin_liquidity(new_coin_chain_id,new_coin_address)[1]
        new_coin_price=get_coin_price(new_coin_chain_id,new_coin_address)
        new_coin_liquidity=get_coin_liquidity(new_coin_chain_id,new_coin_address)[0]
        data_set=[new_coin_symbol,new_coin_address,new_coin_chain_id,new_coin_time,new_coin_liquidity,new_coin_status,new_coin_price]
        return data_set
    
    def insert_new_coin_info(self,data_set):
        coin_id=data_set[0]
        address=data_set[1]
        chain_id=data_set[2]
        time=data_set[3]
        liquidity=data_set[4]
        status=data_set[5]
        price=data_set[6]
        add_data_to_progress(coin_id, address, chain_id, time,liquidity,status,price)


    # bot main function
    def run(self):
        while True:
            # get new coin information
            data_set=self.get_new_coin_info()
            # insert new coin information into database
            self.insert_new_coin_info(data_set)
            # update table
            update_table("COIN")
            update_table("PROGRESS")
            # check if new coin is listed
            if new_coin_status == "listed":
                # set buy condition
                if new_coin_price < 10000:
                    self.set_buy_condition(new_coin_symbol, new_coin_chain_id, "1m", 10000, 100, "price_below_10000")
                # set sell condition
                if new_coin_price > 15000:
                    self.set_sell_condition(new_coin_symbol, new_coin_chain_id, "1m", 15000, 100, "price_above_15000")
                # execute trade
                if self.capital > 0 and self.liquidity > 0:
                    self.execute_trade(new_coin_symbol, new_coin_chain_id, "1m", 10000, 100, "buy", "price_below_10000")
                    self.execute_trade(new_coin_symbol, new_coin_chain_id, "1m", 15000, 100, "sell", "price_above_15000")
            # check if new coin is unlisted
            else:
                # delete progress data
                delete_data_from_progress(new_coin_symbol, new_coin_chain_id)
            # delete progress data if it is over 1 day
            delete_data_from_progress(new_coin_symbol, new_coin_chain_id, 1)
            # refresh liquidity information
            self.liquidity = get_coin_liquidity(new_coin_chain_id,new_coin_address)[0]
            # refresh capital information
            self.capital = 10000
            # refresh profit information
            self.profit = 0.10
            # refresh token status information
            self.token_status = "listed"
            # refresh new coin information
            data_set=self.get_new_coin_info()
            # refresh new coin information into database
            self.insert_new_coin_info(data_set)
            # update table
            update_table("COIN")
            update_table("PROGRESS")
            # wait for 1 minute
            time.sleep(60)

    # 计算利润
    def calculate_profit(self, price, quantity):
        profit = (price - self.capital) * quantity
        return profit
    
    # set buy condition
    #买入条件: liquidity > 20000且发行时间与目前相比不到10分钟, return bool
    def set_buy_condition(self, time, status,liquidity):
        if liquidity > 20000 and (datetime.now() - datetime.strptime(time, '%Y-%m-%d %H:%M:%S')).total_seconds() < 600:
            return True
        else:
            return False
    #卖出条件: liquidity < 20000, 或者利润超过10%, return bool
    def set_sell_condition(self, profit, status,liquidity):
        if liquidity < 20000 or profit > 0.10:
            return True
        else:
            return False
    #执行交易, return bool
    def execute_trade(self, symbol, exchange, timeframe, limit, quantity, side, condition):
        if self.set_buy_condition(new_coin_time, new_coin_status, new_coin_liquidity) and self.capital > 0:
            if side == "buy":
                if self.capital > 0 and self.liquidity > 0:
                    if condition == "price_below_10000":    
                        # buy coin
                        self.capital -= limit * quantity
                        self.liquidity -= quantity
                        print(f"Bought {quantity} {symbol} at {limit} {exchange} {timeframe} with {self.capital} capital and {self.liquidity} liquidity")
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                if self.capital > 0 and self.liquidity > 0:
                    if condition == "price_above_15000":
                        # sell coin
                        self.capital += limit * quantity
                        self.liquidity += quantity
                        print(f"Sold {quantity} {symbol} at {limit} {exchange} {timeframe} with {self.capital} capital and {self.liquidity} liquidity")
                        
                        return True
                    else:
                        return False
                else:
                    return False
        else:
            return False

    