import asyncio
from telegram import Bot
from trade_simulation import Trader
from telegram.error import RetryAfter

# Token
TOKEN = "8175853447:AAHVazK6-YiJ7et_les7zh4v9HkPZbkr9mk"
# chat_id
CHAT_ID = -4897853939

bot = Bot(token=TOKEN)

async def notify(message: str, price: float, position: float, capital: float, profit: float):
    text = (
        f"{message}\n"
        f"📌 当前仓位: {position:.6f}\n"
        f"💼 剩余资金: ${capital:.2f}\n"
        f"📈 当前价格: ${price:.2f}\n"
        f"💰 本次收益: ${profit:.2f}"
    )
    try:
        await bot.send_message(chat_id=CHAT_ID, text=text)
    except RetryAfter as e:
        # 被防止刷屏了，等 e.retry_after 秒后再发
        await asyncio.sleep(e.retry_after)
        await bot.send_message(chat_id=CHAT_ID, text=text)

async def main():
    trader = Trader(
        exchange='okx',
        initial_capital=10000.0,
        symbol='BTC-USDT',
        interval='1m'
        # start_time, end_time 可选
    )
    # 异步执行交易模拟，并在每次交易时调用 notify
    await trader.simulate_trades(notify)

if __name__ == '__main__':
    asyncio.run(main())
