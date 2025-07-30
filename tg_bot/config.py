from telegram import Update
from telegram.ext import (
    CallbackContext,
    ConversationHandler,
)
import sys_config
import os,json

##############Utils###########
def load_config():
    if not os.path.exists(sys_config.CONFIG_FILE):
        #rasing error if config file not found
        print("Config file not found, ERROR")
        raise FileNotFoundError

    with open(sys_config.CONFIG_FILE, "r") as f:
        data = json.load(f)
        return data

    

def save_config(config):
    with open(sys_config.CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

#########End of Utils###########



def set_dry_run() -> int:
    config = load_config()
    config["mode"] = "DryRun"
    save_config(config)
    return ConversationHandler.END

def set_real_run() -> int:
    config = load_config()
    config["mode"] = "RealRun"
    save_config(config)
    return ConversationHandler.END

async def handle_set_sl(update: Update, context: CallbackContext) -> int:
    try:
        sl = float(update.message.text.strip())
        config = load_config()
        config["sl"] = sl
        save_config(config)
        await update.message.reply_text(f"止损已设置为：{sl}")
    except ValueError:
        await update.message.reply_text("请输入有效数字（如 0.05）。")
        return sys_config.SET_SL
    return ConversationHandler.END

async def handle_set_tp(update: Update, context: CallbackContext) -> int:
    try:
        tp = float(update.message.text.strip())
        config = load_config()
        config["tp"] = tp
        save_config(config)
        await update.message.reply_text(f"止盈已设置为：{tp}")
    except ValueError:
        await update.message.reply_text("请输入有效数字（如 0.1)")
        return sys_config.SET_TP
    return ConversationHandler.END