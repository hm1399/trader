# dc_bot.py
import discord
import asyncio
from trade_simulation import Trader

TOKEN = "MTM5MjQxOTM2MjQxMjk1MzYwMA.Gkr_oC.ZpyECLzvoOno5abJeVskYIDn90KU3nRFUsJV-U"
CHANNEL_ID = 1392422072143183883  # 整数形式

intents = discord.Intents.default()
# 读取消息权限
intents.message_content = True
dc_client = discord.Client(intents=intents)

@dc_client.event
async def on_ready():
    print(f"🤖 Bot 已上线：{dc_client.user}")
    channel = dc_client.get_channel(CHANNEL_ID)

    async def notify(message, price, position, capital, profit):
        await channel.send(
            f"{message}\n📌 当前仓位: {position:.6f} BTC\n💼 剩余资金: ${capital:.2f}\n📈 当前价格: ${price:.2f}"
        )

    trader = Trader(exchange='okx', initial_capital=10000, symbol="BTC-USDT")
    await trader.simulate_trades(notify)

    await channel.send("✅ 模拟交易完成。")
    await dc_client.close()

dc_client.run(TOKEN)