from telegram import Update
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! Use /addevent <minutes> <title> <recurrence> <reminder_minutes> to add events.\n"
        "Recurrence: once, daily, weekly, monthly\n"
        "Example: /addevent 10 Meeting once 5"
    )