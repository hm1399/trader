import discord
import asyncio
from trade_simulation import Trader
from discord.ui import Select, View, TextInput
from api import get_binance_data,get_okx_data, get_dex_data

TOKEN = "MTM5MjQxOTM2MjQxMjk1MzYwMA.Ge65_e.HvnoUdPzGrFA1nUHqvlkSdKjqFli9LL-9lnouk"
CHANNEL_ID = 1392422072143183883  # 整数形式

intents = discord.Intents.default()
# 读取消息权限
intents.message_content = True
dc_client = discord.Client(intents=intents)

# Select a chain
class ChainSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Solana", value="solana"),
            discord.SelectOption(label="Ethereum", value="ethereum"),
            discord.SelectOption(label="Base", value="base")
        ]
        super().__init__(placeholder="Select chain", options=options)

    async def callback(self, interaction: discord.Interaction):
        chain_id = self.values[0]
        await interaction.response.send_message(f"Selected Chain: {chain_id}. Now choose the token...")
        token_select = TokenSelect(chain_id)
        view = TokenSelectView(token_select)
        await interaction.channel.send("Please choose a token:", view=view)

# Select a token
class TokenSelect(Select):
    def __init__(self, chain_id):
        self.chain_id = chain_id
        if chain_id == "solana":
            options = [
            discord.SelectOption(label="PEPE", value="Ey2zpSAJ5gVLfYDD5WjccbksJD3E9jPFMPaJ8wxvpump"),
            discord.SelectOption(label="PENGU", value="2zMMhcVQEXDtdE6vsFS7S7D5oUodfJHE8vd1gnBouauv"),
            discord.SelectOption(label="Bog", value="GnU9vh8c1MtMFS9DV1HLbXDe2Ug8EM5n54djT4Nnbonk")
            ]
        
        elif chain_id == "ethereum" :
            options = [
            discord.SelectOption(label="KIKO", value="0xD50AD7C05D090EBe07827e7854141cFF48C27b44"),
            discord.SelectOption(label="XING", value="0x71823B57de5898957d763D2A92A1571fCb0d6B44"),
            discord.SelectOption(label="AP", value="0xe60e9BD04ccc0a394f1fDf29874e35a773cb07f4")
            ]

        elif chain_id == "base": 
            options = [
            discord.SelectOption(label="SHIB", value="0xFCa95aeb5bF44aE355806A5ad14659c940dC6BF7"),
            discord.SelectOption(label="SKI", value="0x768BE13e1680b5ebE0024C42c896E3dB59ec0149L"),
            discord.SelectOption(label="KTA", value="0xc0634090F2Fe6c6d75e61Be2b949464aBB498973")
            ]

        super().__init__(placeholder="Select token", options=options)

    async def callback(self, interaction: discord.Interaction):
        token_address = self.values[0]
        await interaction.response.send_message(f"Selected Token: {token_address}. Now set your price alert...")
        price = PriceInput(self.chain_id, token_address)
        await interaction.channel.send("Please set the price alert (e.g. 100.00):", view=price)


class PriceInput(View):
    def __init__(self, chain_id, token_address):
        super().__init__()
        self.chain_id = chain_id
        self.token_address = token_address

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("请在聊天中输入价格(例如:100.00):", ephemeral=True)

        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel

        try:
            # 等待用户输入
            price_message = await dc_client.wait_for("message", check=check)
            price = float(price_message.content)

            if price < 0:
                await interaction.followup.send("无效价格！请输入正数。", ephemeral=True)
                return

            await interaction.followup.send(f"价格警报已设置为 {price}。当价格达到此阈值时，我会通知你。")
            await self.monitor_price(price, interaction)
        except ValueError:
            await interaction.followup.send("无效输入！请输入一个有效的数字。", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"发生错误：{str(e)}", ephemeral=True)

    async def monitor_price(self, alert_price, interaction):
        while True:
            current_price = get_dex_data(self.chain_id, self.token_address)  
            if current_price is not None:
                if current_price >= alert_price:
                    await interaction.followup.send(f"🔔 价格警报！当前价格为 {current_price}，超出你的阈值 {alert_price}。")
                    break
            await asyncio.sleep(60)
        

    async def monitor_price(self, alert_price, interaction):
        while True:
            current_price = get_dex_data(interaction.guild.id, TOKEN)  
            if current_price is not None:
                if current_price >= alert_price:
                    await interaction.followup.send(f"🔔 价格警报！当前价格为 {current_price}，超出你的阈值 {alert_price}。")
                    break
            await asyncio.sleep(60)  

# 创建 TokenSelectView，确保 Select 被包含在 View 中
class TokenSelectView(View):
    def __init__(self, token_select: discord.ui.Select):
        super().__init__()
        self.add_item(token_select)

# 阅读用户消息并做出回应
@dc_client.event
async def on_message(message):
    channel = dc_client.get_channel(CHANNEL_ID)

    if message.author == dc_client.user:
        return

    if message.content.lower() == "simulation":

        async def notify(message, price, position, capital, profit):
            await channel.send(
            f"{message}\n📌 当前仓位: {position:.6f} BTC\n💼 剩余资金: ${capital:.2f}\n📈 当前价格: ${price:.2f}"
        )
            
        trader = Trader(exchange='okx', initial_capital=10000, symbol="BTC-USDT")
        await trader.simulate_trades(notify)
        await channel.send("✅ 模拟交易完成。")
        

    elif message.content.lower() == "alert":
        # 当用户输入 "设置警报" 时，展示选择链的界面
        select = ChainSelect()
        view = View()
        view.add_item(select)
        await message.channel.send("Please select the chain:", view=view)

    elif message.content.lower() == "quit":
        await channel.send("quit the bot now.")
        await dc_client.close()

@dc_client.event
async def on_ready():
    print(f"Logged in as {dc_client.user}")
    # 让用户可以开始交互
    await dc_client.get_channel(CHANNEL_ID).send("Type '模拟交易' to start simulation, or '设置警报' to set price alert.") 

dc_client.run(TOKEN)

