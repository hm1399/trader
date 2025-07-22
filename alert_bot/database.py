import sqlite3
import os
from api import *
#所有数据库里的数据都是大写（出了coin_address）

# function of adding data to the table CHAIN
def add_data_to_chain(chain_id):
    if chain_id == None:
        print("Please enter the chain id")
        return
    chain_id = chain_id.upper()
    conn = sqlite3.connect(r"C:\internship\AITO\python_project\trader\db\dex_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO CHAIN (CHAIN_ID) VALUES (?)", (chain_id,))
    conn.commit()
    conn.close()
    print("Data added successfully")


# function of adding data to the table COIN
def add_data_to_coin(coin_id, address, chain_id, time, liquidity, status,price ):
    if coin_id == None or address == None or chain_id == None or time == None or liquidity == None or status == None:
        print("Please enter all the required fields")
    coin_id = coin_id.upper()
    chain_id = chain_id.upper()
    status = status.upper()
    if chain_id not in get_all_chains():
        print("Please enter a valid chain id")
        return
    
    conn = sqlite3.connect(r"C:\internship\AITO\python_project\trader\db\dex_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO COIN (COIN_ID, ADDRESS, CHAIN_ID, TIME, LIQUIDITY, STATUS) VALUES (?,?,?,?,?,?)", (coin_id,address, chain_id, time, liquidity, status,price))
    conn.commit()
    conn.close()
    print("Data added successfully")

# function of adding data to the table PROGRESS(for new coin)
def add_data_to_progress(coin_id, address, chain_id, time,liquidity,status,price):
    if coin_id == None or chain_id == None or address == None or time == None or status == None or price == None :
        print("Please enter all the required fields")
    coin_id = coin_id.upper()
    chain_id = chain_id.upper()
    status = status.upper()
    if chain_id not in get_all_chains():
        print("Please enter a valid chain id")
        return
    conn = sqlite3.connect(r"C:\internship\AITO\python_project\trader\db\dex_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO PROGRESS (P_COIN_ID, P_ADDRESS, P_CHAIN_ID, TIME, LIQUIDITY, STATUS,PRICE) VALUES (?,?,?,?,?,?,?)", (coin_id,address, chain_id, time, liquidity, status,price))
    conn.commit()
    conn.close()
    print("Data added successfully")


# function of getting all the chains from the table CHAIN
def get_all_chains():
    conn = sqlite3.connect(r"C:\internship\AITO\python_project\trader\db\dex_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM CHAIN")
    rows = cursor.fetchall()
    # delete ,
    data=[]
    for row in rows:
        row = list(row)
        data.append(row[0])
    conn.close()
    return data

# function of getting all the chain_id of coins from the table COIN base on the chain id
def get_all_coins(chain_id):
    conn = sqlite3.connect(r"C:\internship\AITO\python_project\trader\db\dex_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM COIN WHERE CHAIN_ID = ?", (chain_id,))
    rows = cursor.fetchall()
    # delete ,
    data=[]
    for row in rows:
        row = list(row)
        data.append(row[0])
    conn.close()
    return data

def get_coin_address(coin_id):
    conn = sqlite3.connect(r"C:\internship\AITO\python_project\trader\db\dex_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT ADDRESS FROM COIN WHERE COIN_ID = ?", (coin_id,))
    rows = cursor.fetchall()
    # delete ,
    data=[]
    for row in rows:
        row = list(row)
        data.append(row[0])
    conn.close()
    return data[0]


# 让database里的chain_id 都变成大写
def update_chain_id():
    conn = sqlite3.connect(r"C:\internship\AITO\python_project\trader\db\dex_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM CHAIN")
    rows = cursor.fetchall()
    for row in rows:
        row = list(row)
        chain_id = row[0]
        cursor.execute("UPDATE CHAIN SET CHAIN_ID = ? WHERE CHAIN_ID = ?", (chain_id.upper(), chain_id))
        conn.commit()
    conn.close()
    print("Data updated successfully")  

# 让database里的coin_id 和 chain_id 都变成大写
def update_coin_id():
    conn = sqlite3.connect(r"C:\internship\AITO\python_project\trader\db\dex_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM COIN")
    rows = cursor.fetchall()
    for row in rows:
        row = list(row)
        coin_id = row[0]
        chain_id = row[2]
        status = row[5]
        cursor.execute("UPDATE COIN SET COIN_ID = ? WHERE COIN_ID = ?", (coin_id.upper(), coin_id))
        cursor.execute("UPDATE COIN SET CHAIN_ID = ? WHERE CHAIN_ID = ?", (chain_id.upper(), chain_id))
        cursor.execute("UPDATE COIN SET STATUS = ? WHERE STATUS = ?", (status.upper(), status))
        conn.commit()
    conn.close()
    print("Data updated successfully")  



# 更新某个表里全部数据的的liquidity和status和price
def update_table(table_name):
    table_name = table_name.upper()
    if table_name not in ["COIN","PROGRESS"]:
        print("Please enter a valid table name")
        return
    chain_id=get_all_chains()
    # 对于每一条chain的每一个coin进行更新
    for chain_id in chain_id:
        coins=get_all_coins(chain_id)
        for coin in coins:
            address = get_coin_address(coin)
            liquidity = get_coin_liquidity(chain_id,address)[0]
            price=get_coin_price(chain_id,address)
            if liquidity == 'N/A':
                status = "unlisted"
            else:
                status = "listed"
            conn = sqlite3.connect(r"C:\internship\AITO\python_project\trader\db\dex_data.db")
            cursor = conn.cursor()

            # 如果是COIN表，且status为unlisted:liquidity没有了，则删除该条数据
            if table_name == "COIN" and status == "unlisted":
                cursor.execute("DELETE FROM "+table_name+" WHERE ADDRESS = ?", (address))
            # 如果是PROGRESS表，且status为listed:liquidity有了，上市了，且发行时间超过一天的，则插这条数据道COIN表里并且删除Progress表里的这条数据。
            elif table_name == "PROGRESS" and status == "listed" and (datetime.now()-datetime.strptime(get_coin_symbol_time(chain_id,address),"%Y-%m-%d %H:%M:%S")).days > 1:
                cursor.execute("INSERT INTO COIN (COIN_ID, ADDRESS, CHAIN_ID, TIME, LIQUIDITY, STATUS, PRICE) VALUES (?,?,?,?,?,?,?)", (coin,address, chain_id,get_coin_symbol_time(chain_id,address)[1],liquidity, status,price))
                cursor.execute("DELETE FROM PROGRESS WHERE ADDRESS = ?", (address))
            # 都不是的话只更新status和liquidity
            else:
                cursor.execute("UPDATE "+table_name+" SET LIQUIDITY = ? WHERE ADDRESS = ?", (liquidity,address))
                cursor.execute("UPDATE "+table_name+" SET STATUS = ? WHERE ADDRESS = ?", (status,address))
                cursor.execute("UPDATE "+table_name+" SET PRICE = ? WHERE ADDRESS = ?", (price,address))
            conn.commit()
            conn.close()
    print("status and liquidity updated successfully")  


