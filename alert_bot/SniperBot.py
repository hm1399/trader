from api import get_coin_price, get_coin_symbol_time, get_coin_liquidity,get_latest_coin_info


""" 1.从get_latest_coin_info()获取币种信息
    2. 加入TABLE PROGRESS,获取liquidity信息,判断新币状态（上没上市）
    3. 声明初始资金，设置买卖条件，执行交易（利润）
    4. 检查progress里每条数据的发币时间,超过一天直接删除
    5. 加入TABLE ALERT,记录交易信息，发送通知
    6. 可选择状态：只在货币上市后开始买卖
"""
class SniperBot:
    def __init__(self, initial_capital, token_status, profit, liquidity):
        self.capital = initial_capital
        self.token_status = token_status
        self.profit = None
        self.liquidity = liquidity

    #get information of new coin
    def update_new_coin_info(self):
        global new_coin 
        global new_coin_chain_id
        global new_coin_address
        global new_coin_symbol
        global new_coin_time
        global new_coin_price
        global new_coin_liquidity
        new_coin =  get_latest_coin_info() #chain_id,address,symbol,time
        new_coin_chain_id=new_coin[0]
        new_coin_address=new_coin[1]
        new_coin_symbol=new_coin[2]
        new_coin_time=new_coin[3]
        new_coin_price=get_coin_price(new_coin_chain_id,new_coin_address)
        new_coin_liquidity=get_coin_liquidity(new_coin_chain_id,new_coin_address)






#def buy_token(symbol, exchange, timeframe, limit, quantity):
    #pass

#def sell_token(symbol, exchange, timeframe, limit, quantity):
    #pass

#def set_sell_condition(symbol, exchange, timeframe, limit, quantity, condition):
    #pass

#def set_buy_condition(symbol, exchange, timeframe, limit, quantity, condition):
    #pass

#def execute_trade(symbol, exchange, timeframe, limit, quantity, side, condition):
    #pass
