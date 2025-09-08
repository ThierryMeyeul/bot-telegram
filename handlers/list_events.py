from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from db import Session
from models import User, Event


async def list_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        send = query.edit_message_text
    else:
        send = update.message.reply_text
    session = Session()
    try:
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
        if not user:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text="🙁 *Tu n’as encore aucun rappel enregistré.*\n\n"
                "👉 Utilise `/reminder` pour en créer un nouveau.",
                parse_mode="Markdown"
            )
            return

        events = session.query(Event).filter_by(user_id=user.id).all()
        if not events:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text="📭 *Aucun rappel trouvé.*\n\n"
                "👉 Crée ton premier avec `/reminder`",
                parse_mode="Markdown"
            )
            return

        msg_lines = ["📅 *Voici tes rappels enregistrés :*\n"]
        for e in events:
            msg_lines.append(
                f"🆔 *ID* : `{e.id}`\n"
                f"📝 *Titre* : {e.title}\n"
                f"⏰ *Date/Heure* : `{e.event_datetime.strftime('%Y-%m-%d %H:%M')}`\n"
                f"🔁 *Récurrence* : {e.recurrence.value}\n"
                f"📌 *Statut* : {e.status.value}\n"
                "━━━━━━━━━━━━━━━"
            )

        # envoi avec markdown
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text="\n\n".join(msg_lines),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➕ Ajouter un rappel", callback_data="list_add_event")]])
        )

        # proposer des boutons pour gérer les events
        #buttons = [
        #   [InlineKeyboardButton("➕ Ajouter un rappel", callback_data="list_add_event")],
            #[InlineKeyboardButton("🗑️ Supprimer un rappel", callback_data="list_delete_event")]
        #]
        #await context.bot.send_message(
        #   chat_id=update.effective_user.id,
        #   text="👉 Que veux-tu faire ensuite ?",
        #   reply_markup=InlineKeyboardMarkup(buttons)
        #)

    finally:
        session.close()
