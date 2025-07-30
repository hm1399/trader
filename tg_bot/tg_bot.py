from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup,error
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import sys_config
import config
import jupiter_api.api as japi

############End of Utils###############

############Menu#################
async def menu(update: Update, context: CallbackContext) -> int:
    keyboard = [
        [
            InlineKeyboardButton("Config", callback_data="config"),
            InlineKeyboardButton("Show Details", callback_data="show_details"),
            InlineKeyboardButton("Show Balances", callback_data="show_balances"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Bot Menu", reply_markup=reply_markup)
    return sys_config.MENU

# 按钮点击的回调处理
async def button_click(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "config":
        keyboard = [
            [InlineKeyboardButton("Set Run Mode", callback_data="set_mode")],
            [InlineKeyboardButton("Set SL (止损)", callback_data="set_sl")],
            [InlineKeyboardButton("Set TP (止盈)", callback_data="set_tp")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Config 设置菜单：", reply_markup=reply_markup)
        return sys_config.CONFIG
    elif query.data == "show_details":
        await query.edit_message_text(text="You selected Option 2.")
        return sys_config.SHOW_DETAILS
    elif query.data == "show_balances":
        await query.edit_message_text(text="Tracking balances at")
        data = japi.get_balance(config.load_config()["TRACK_WALLET"])
        await context.bot.send_message(chat_id=query.message.chat_id, text="Holdings:\n")
        try:
            tokens = ""
            for k in data:
                tokens += k + ","
            tokens = tokens[:-1]
            #print(tokens)
            token_data = japi.get_token_data_by_token_address(tokens)
            if len(token_data) > 100:
                await context.bot.send_message(chat_id=query.message.chat_id, text="数量大于100，请联系开发者"+str(len(token_data)))
                return ConversationHandler.END
            #match the data in tokens     
            for k in token_data:
                for token in token_data:
                    if token['id'] == k:
                        token_data[k]['uiAmount'] = token['uiAmount']
            #print(token_data)
        
            for k in token_data:
                text = f"{token_data[k]['name']}/{token_data[k]['symbol']}: {token_data[k]['uiAmount']}(${token_data[k]['uiAmount']*token_data[k]['usdPrice']}) \n"
                await context.bot.send_message(chat_id=query.message.chat_id, text=text)

        except error.RetryAfter as e:
            await context.bot.send_message(chat_id=query.message.chat_id, text=f"Too many requests, try again in {e.retry_after} seconds.")

        return ConversationHandler.END
    elif query.data == "set_mode":
        keyboard = [
            [InlineKeyboardButton("Dry Run", callback_data="dry_run")],
            [InlineKeyboardButton("Real Run", callback_data="real_run")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Choose a run mode:", reply_markup=reply_markup)
        return sys_config.SET_MODE
    elif query.data == "set_sl":
        await context.bot.send_message(chat_id=query.message.chat_id, text="Input a value for SL (Stop Loss) (e.g. 0.1 for -10%):")
        return sys_config.SET_SL
    elif query.data == "set_tp":
        await context.bot.send_message(chat_id=query.message.chat_id, text="Input a value for TP (Take Profit) (e.g. 0.1 for 10%):")
        return sys_config.SET_TP
    elif query.data == "dry_run":
        config.set_dry_run()
        await query.edit_message_text(text="You selected Dry Run.")
        return ConversationHandler.END
    elif query.data == "real_run":
        config.set_real_run()
        await query.edit_message_text(text="You selected Real Run.")
        return ConversationHandler.END
    else:
        await query.edit_message_text(text="Unknown option selected.")
        return sys_config.MENU

async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END


##########END of Menu#################

####################Commands#####################

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Use /Menu ,open menu")

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello I am a bot")
####################END of Commands#####################

def main():
    app = ApplicationBuilder().token(sys_config.TOKEN).build()


    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("menu", menu)],
        states={
            sys_config.MENU:           [CallbackQueryHandler(button_click)],
            sys_config.CONFIG:         [CallbackQueryHandler(button_click)],
            sys_config.SET_MODE:       [CallbackQueryHandler(button_click)],
            sys_config.DRY_RUN:        [CallbackQueryHandler(button_click)],
            sys_config.REAL_RUN:       [CallbackQueryHandler(button_click)],
            
            sys_config.SHOW_DETAILS:   [MessageHandler(filters.TEXT & ~filters.COMMAND, cancel)],
            sys_config.SET_SL:         [MessageHandler(filters.TEXT & ~filters.COMMAND, config.handle_set_sl)],
            sys_config.SET_TP:         [MessageHandler(filters.TEXT & ~filters.COMMAND, config.handle_set_tp)],

            
        },
        fallbacks=[CommandHandler("menu", menu)],
    )

    app.add_handler(conv_handler)
    # 启动 bot
    app.run_polling()





if __name__ == '__main__':
    main()
