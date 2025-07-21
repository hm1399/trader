import sqlite3
import os
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
def add_data_to_coin(coin_id, address, chain_id ):
    if coin_id == None or address == None or chain_id == None:
        print("Please enter all the required fields")
    coin_id = coin_id.upper()
    chain_id = chain_id.upper()
    if chain_id not in get_all_chains():
        print("Please enter a valid chain id")
        return
    
    conn = sqlite3.connect(r"C:\internship\AITO\python_project\trader\db\dex_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO COIN (COIN_ID, ADDRESS, CHAIN_ID) VALUES (?,?,?)", (coin_id,address, chain_id))
    conn.commit()
    conn.close()
    print("Data added successfully")

# function of adding data to the table PROGRESS(for new coin)
def add_data_to_progress(coin_id, address, chain_id, time, status):
    if coin_id == None or chain_id == None or address == None or time == None or status == None:
        print("Please enter all the required fields")
    coin_id = coin_id.upper()
    chain_id = chain_id.upper()
    status = status.upper()
    if chain_id not in get_all_chains():
        print("Please enter a valid chain id")
        return
    add_data_to_coin(coin_id, address, chain_id)
    conn = sqlite3.connect(r"C:\internship\AITO\python_project\trader\db\dex_data.db")
    cursor.execute("INSERT INTO PROGRESS (COIN_ID, ADDRESS, CHAIN_ID, TIME, STATUS) VALUES (?,?,?,?,?)", (coin_id,address, chain_id, time, status))
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
def get_all_coins(chin_id):
    conn = sqlite3.connect(r"C:\internship\AITO\python_project\trader\db\dex_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM COIN WHERE CHAIN_ID = ?", (chin_id,))
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
        print(chain_id)
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
        cursor.execute("UPDATE COIN SET COIN_ID = ? WHERE COIN_ID = ?", (coin_id.upper(), coin_id))
        cursor.execute("UPDATE COIN SET CHAIN_ID = ? WHERE CHAIN_ID = ?", (chain_id.upper(), chain_id))
        conn.commit()
    conn.close()
    print("Data updated successfully")  





#add_data_to_coin("WETH","0x4200000000000000000000000000000000000006","BASE")
#print(get_coin_address("WETH"))

#给progress表格添加两列
conn = sqlite3.connect(r"C:\internship\AITO\python_project\trader\db\dex_data.db")
cursor = conn.cursor()
cursor.execute("ALTER TABLE PROGRESS ADD COLUMN TIME DATETIME NOT NULL")      
cursor.execute("ALTER TABLE PROGRESS ADD COLUMN STATUS STRING NOT NULL")      

conn.commit()
conn.close()
print("Data updated successfully")  

