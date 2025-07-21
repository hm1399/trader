# For discord, 

import discord
import asyncio
from trade_simulation import Trader
from discord.ui import Select, View, TextInput, Modal, Button
from discord import ui
from api import get_binance_data,get_okx_data, get_coin_price
from database import add_data_to_chain, add_data_to_coin, get_all_chains, get_all_coins, get_coin_address, update_chain_id, update_coin_id


#登录开发者平台获取
TOKEN = "MTM5MjQxOTM2MjQxMjk1MzYwMA.GTwFrx.D1SY0uECJkj8fsfIa0nuwrmjjQqaRQrlaXLuPs"
# 在dc右键group title获取
CHANNEL_ID = 1392422072143183883  
#创建机器人
intents = discord.Intents.default()
# 读取消息权限
intents.message_content = True
dc_client = discord.Client(intents=intents)

# 保存用户的警报设置（字典：用户ID -> 警报设置）
user_alerts = {}

#创建一个表格让用户填写，并根据数据设置alert
class Questionnaire(ui.Modal, title='Alert'):
    # 创建表格
    chain = ui.TextInput(label='Select a Chain', placeholder='e.g., Ethereum')
    coin = ui.TextInput(label='Select a Coin', placeholder='e.g., BTC')
    price = ui.TextInput(label='Set a price', placeholder='e.g., 100.00')

    async def on_submit(self, interaction: discord.Interaction):
        # 获取用户输入的表单数据
        selected_chain = self.chain.value
        selected_coin = self.coin.value
        select_price = float(self.price.value)

        # 向用户发送感谢消息，并显示填写的内容
        await interaction.response.send_message(
            f'Thanks for your response! You selected:\nChain: {selected_chain}\nCoin: {selected_coin}\nPrice: {select_price}',
            ephemeral=True
        )

        # 更新用户警报设置
        user_alerts[interaction.user.id] = {
            'chain': selected_chain,
            'coin': selected_coin,
            'price': select_price
        }

        # 启动检查价格的任务
        await self.check_price(selected_chain, selected_coin, select_price, interaction)

    async def check_price(self, selected_chain, selected_coin, select_price, interaction: discord.Interaction):
        # 根据链和代币地址获取实时价格
        # 检查用户选择的chain有没有被提供
        coin_address = None
        selected_chain = selected_chain.upper()
        selected_coin = selected_coin.upper()
        print(selected_chain)
        print(selected_coin)
        # check chain is supported or not
        if selected_chain not in get_all_chains():
            await interaction.followup.send(f"Chain {selected_chain} not supported", ephemeral=True)
            return
        # check coin is supported or not
        if selected_coin in get_all_coins(selected_chain):
            coin_address = get_coin_address(selected_coin)
            
        else:
            await interaction.followup.send(f"Coin {selected_coin} not found on {selected_chain}.", ephemeral=True)
            return
        
        if coin_address is None:
            await interaction.followup.send(f"Failed to fetch price for {selected_coin} on {selected_chain}.", ephemeral=True)
            return

        # 获取实时价格
        price = get_coin_price(selected_chain.lower(), coin_address)

        #获取不到价格
        if price is None:
            await interaction.followup.send(f"Failed to fetch price for {selected_coin} on {selected_chain}.", ephemeral=True)
            return
    
        
        # 检查价格是否超过设定阈值
        if price >= select_price:
            await interaction.user.send(f"Alert! The price of {selected_coin} on {selected_chain} has exceeded your set price of {select_price}. Current price is {price}.")
        else:
            await interaction.user.send(f"The current price of {selected_coin} on {selected_chain} is {price}, which is below your alert threshold of {select_price}.")
        
        # 设置定时任务以检查价格
        await asyncio.sleep(15)  # 每隔15秒检查一次价格
        await self.check_price(selected_chain, selected_coin, select_price, interaction)  # 递归调用




# 阅读用户消息并做出回应
@dc_client.event

async def on_ready():
    print(f"Logged in as {dc_client.user}")
    # 让用户可以开始交互
    await dc_client.get_channel(CHANNEL_ID).send("Type 'simulation' to start simulation, or 'alert' to set price alert.") 

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
        await message.author.send("Click the button to fill the alert setting", view=view)
#----------------------------------------------------------------------------------------------------------------------------------------
    




    elif message.content.lower() == "quit":
        await channel.send("quit the bot now.")
        await dc_client.close()



dc_client.run(TOKEN)

