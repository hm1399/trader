import sqlite3
import os




# 连接到数据库文件
conn = sqlite3.connect(r"C:\internship\AITO\python_project\trader\db\chain.db")


cursor = conn.cursor()

# 执行查询语句
cursor.execute("SELECT * FROM COIN")

# 获取所有数据
rows = cursor.fetchall()

# 遍历并输出
for row in rows:
    print(row)

# 关闭连接
conn.close()
