# For discord, 

import discord
import asyncio
from trade_simulation import Trader
from discord.ui import Select, View, TextInput, Modal, Button
from discord import ui
from api import get_binance_data,get_okx_data, get_dex_data

#登录开发者平台获取
TOKEN = "MTM5MjQxOTM2MjQxMjk1MzYwMA.GXYjRE.HscgvEQSZKGz_JDXQChen0jjf1hy3kOQN7kG5k"
# 在dc右键group title获取
CHANNEL_ID = 1392422072143183883  

intents = discord.Intents.default()
# 读取消息权限
intents.message_content = True
dc_client = discord.Client(intents=intents)

#创建一个表格让用户填写，并根据数据设置alert
class Questionnaire(ui.Modal, title='Alert'):
    # 创建文本输入框
    chain = ui.TextInput(label='Select a Chain', placeholder='e.g., Ethereum')
    coin = ui.TextInput(label='Select a Coin', placeholder='e.g., BTC')

    async def on_submit(self, interaction: discord.Interaction):
        # 获取用户输入的表单数据
        selected_chain = self.chain.value
        selected_coin = self.coin.value
        
        # 向用户发送感谢消息，并显示填写的内容
        await interaction.response.send_message(
            f'Thanks for your response! You selected:\nChain: {selected_chain}\nCoin: {selected_coin}',
            ephemeral=True
        )

        # 在这里根据获取的信息设置alert






# 阅读用户消息并做出回应
@dc_client.event
async def on_message(message):
    channel = dc_client.get_channel(CHANNEL_ID)

    if message.author == dc_client.user:
        return
     # type simulation 开始使用历史数据模拟交易（过去30天）， data from okx
    if message.content.lower() == "simulation":

        async def notify(message, price, position, capital, profit):
            await channel.send(
            f"{message}\n📌 当前仓位: {position:.6f} BTC\n💼 剩余资金: ${capital:.2f}\n📈 当前价格: ${price:.2f}"
        )
            
        trader = Trader(exchange='okx', initial_capital=10000, symbol="BTC-USDT")
        await trader.simulate_trades(notify)
        await channel.send("✅ 模拟交易完成。")
        
# 修改这里----------------------------------------------------------------------------------------------------------------------------
    #type alert 设置一个警报，从dex获取实时数据
    elif message.content.lower() == "alert":
        button = Button(label='Start Questionnaire', style=discord.ButtonStyle.primary)
        async def button_callback(interaction: discord.Interaction):
                modal = Questionnaire()
                await interaction.response.send_modal(modal)  # 通过interaction发送表单
            
        # 将按钮与回调函数绑定
        button.callback = button_callback

        # 创建 View 并将按钮添加进去
        view = View()
        view.add_item(button)

        # 发送带有按钮的消息
        await message.author.send("Click the button to fill the questionnaire:", view=view)
#----------------------------------------------------------------------------------------------------------------------------------------
   
    elif message.content.lower() == "quit":
        await channel.send("quit the bot now.")
        await dc_client.close()

@dc_client.event
async def on_ready():
    print(f"Logged in as {dc_client.user}")
    # 让用户可以开始交互
    await dc_client.get_channel(CHANNEL_ID).send("Type '模拟交易' to start simulation, or '设置警报' to set price alert.") 

dc_client.run(TOKEN)

