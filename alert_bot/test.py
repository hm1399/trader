# Select a chain
import discord
import asyncio
from trade_simulation import Trader
from discord.ui import Select, View, TextInput, Modal, Button
from discord import ui
from api import get_binance_data,get_okx_data, get_dex_data

chain_id = "solana"
token_address = "9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump"
data=get_dex_data(chain_id,token_address)
print(data)