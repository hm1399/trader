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
"""


# return chain_id,address,coin_id,time,liquidity,status,price
def get_new_coin_info():
    data_set = get_latest_coin_info() #chain_id,address,symbol,time
    print(f"new coin data is {data_set}")
    coin_id = data_set[2]
    address = data_set[1]
    chain_id = data_set[0]
    time = data_set[3]
    #liquidity = get_coin_liquidity(chain_id,address)[0]
    #status = get_coin_liquidity(chain_id,address)[1]
    price = get_coin_price(chain_id,address)
    data=[chain_id,address,coin_id,time,0,0,price]
    return data

# return 剩余资金和买入数量
# data=[chain_id,address,coin_id,time,liquidity,status,price]
def buy_coin(data, remainder, quantity): 
    chain_id = data[0]
    address = data[1]
    coin_id = data[2]
    time = data[3]
    #liquidity = data[4]
    #status = data[5]
    price = data[6]

    # 小于20000 all in
    if remainder > price and remainder <= 20000:
        quantity = int(remainder/price)
        remainder -= price*quantity
        print(f"Bought {quantity} {coin_id} at {price} with ${price*quantity} , and remainder is ${remainder}")
        return [remainder, quantity]
    
    elif remainder > price and remainder > 20000:
        quantity = int(20000/price)
        remainder -= price*quantity
        print(f"Bought {quantity} {coin_id} at {price} with ${price*quantity} , and remainder is ${remainder}")
        return [remainder, quantity]
    else:
        print(f"Not enough money to buy {coin_id} at {price}")
        return None       

    
# coin data,  余额， 买入数量
def sell_coin(data, remainder, quantity):
    chain_id = data[0]
    address = data[1]
    coin_id = data[2]
    list_time = data[3]
    # 持续更新流动性,新币没有流动性
    #liquidity = get_coin_liquidity(chain_id,address)[0]
    #status = get_coin_liquidity(chain_id,address)[1]
    #原价
    start_price = data[6]
    last_profit = 0 # 上一次利润
    current_profit = 0 # 当前利润
    biggest_profit = 0 # 最大利润
    new_price = get_coin_price(chain_id,address)
    # 获取当前利润
    current_profit= (new_price - start_price) / start_price * 100 #0
    last_profit = current_profit #0
    biggest_profit = current_profit #0
    print(f"current profit is {current_profit}%")

    #建立一个数组，记录利润和开始时间，如果同一个利润范围（+-1%）超过1分钟，则卖出
    Loss_time=0 # 持续亏损的次数,连续20次都是负利润，则卖出
    profit_list = [current_profit,datetime.now(), Loss_time]
    
    # 持续获取价格
    while True:
        new_price = get_coin_price(chain_id,address)
        # 获取当前利润
        current_profit= (new_price - start_price) / start_price * 100
        #检查利润是否有变化
        #如果利润没有变化超过1分钟，卖出
        if profit_list[0]-0.5<= current_profit<=  profit_list[0]+0.5:
            if (datetime.now() - profit_list[1]).total_seconds() > 60:
                earn_money = new_price*quantity
                remainder += earn_money
                print("the price is not change for 1 minutes, sell the coin")
                print(f"Sold {quantity} {coin_id} at {new_price} with ${earn_money} , and remainer is ${remainder}")
                quantity = 0
                #返回余额
                return remainder
        #利润变化了
        else:
            profit_list[0]=current_profit
            profit_list[1]=datetime.now()

        if current_profit < 0:
            profit_list[2]+=1
            # 超过20次亏损
            if Loss_time >= 20:
                earn_money = new_price*quantity
                remainder += earn_money
                print(f"Sold {quantity} {coin_id} at {new_price} with ${earn_money} , and remainer is ${remainder}")
                quantity = 0
                #返回余额
                return remainder
        # 中断连续亏损
        else:
            profit_list[2]=0

        if current_profit > last_profit:
            print(f"Current profit is increasing, current profit is {current_profit}%")
            # 大于20%时卖出
            if current_profit >= 20.0 or ( -5<=current_profit < 0.0):
                earn_money = new_price*quantity
                remainder += earn_money
                print(f"Sold {quantity} {coin_id} at {new_price} with ${earn_money} , and remainer is ${remainder}")
                quantity = 0
                #返回余额
                return remainder
            elif current_profit <-5.0 :
                last_profit = current_profit
                biggest_profit = current_profit
                time.sleep(0.2)
                continue
            else:
                last_profit = current_profit
                biggest_profit = current_profit
                time.sleep(0.2)
                continue
        
        elif current_profit < last_profit:
            print(f"Current profit is decreasing, current profit is {current_profit}%")
            # 到最大利润的9成 或者 亏损过大, 等待回升
            if biggest_profit *0.9 <= current_profit or current_profit < -5.0:
                last_profit = current_profit
                time.sleep(0.2)
                continue
            # 当前利润低于最大利润的9成且亏损在5%以下，卖出
            elif biggest_profit *0.9 > current_profit  and  current_profit > -5:
                earn_money = new_price*quantity
                remainder += earn_money
                print(f"Sold {quantity} {coin_id} at {new_price} with ${earn_money} , and remainer is ${remainder}")
                quantity = 0
                #返回余额
                return remainder

        else:
            time.sleep(0.2)
            continue

        """
        # 流动性小于20000时全部卖出
        if liquidity < 20000:
            earn_money = new_price*quantity
            remainder += earn_money
            print(f"Sold {quantity} {coin_id} at {new_price} with ${earn_money} , and remainer is ${remainder}")
            quantity = 0
            #返回余额
            return remainder
        """   


capital = 10000 # 初始资金
round_id = 1
last_round_money = capital
quantity = 0
remainder = capital
print(f"----------------------------------{round_id} round------------------------------------------------")
while True:


    # 获取数据

    new_coin_data= get_new_coin_info()
    print(f"new coin data is {new_coin_data}")
    #买入
    buy = buy_coin(new_coin_data, remainder, quantity)# return remainder, quantity

    if buy != None: # 成功买入
    # 余额
        remainder = buy[0]
    # 买入数量
        quantity = buy[1]
    #卖出
        remainder = sell_coin(new_coin_data,remainder,quantity)
        # 计算本回合利润
        
        profit = (remainder - last_round_money) / last_round_money * 100
        last_round_money = remainder
        print(f"{round_id} round, profit is {profit}%, the remainder is {remainder}")
    
        round_id += 1

    else:
        print("not buy")
        continue

    #计算总利润
    
    total_profit = (remainder - capital) / capital * 100
    print(f"total profit is {total_profit}%, the capital is {capital},the remainder is {remainder}")
    

    print(f"----------------------------------{round_id} round------------------------------------------------")
    # 休眠10秒
    time.sleep(5)



    ## stop loss 
    ## 不断更新当前利润，如果比上一次的利润少3%，则卖出
    ## check 时间，只有刚刚上市5分钟的才买入
    # 查看 pump.fun的api能获取哪些数据
    # 完善stoploss