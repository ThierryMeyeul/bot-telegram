from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db import Session
from models import Event, User, RecurrenceEnum


async def delete_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = Session()
    try:
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
        if not user:
            await update.message.reply_text(
                "🙁 *Tu n’as encore aucun rappel enregistré.*\n\n"
                "👉 Utilise `/reminder` pour en créer un.",
                parse_mode="Markdown"
            )
            return

        events = session.query(Event).filter_by(user_id=user.id).all()
        if not events:
            await update.message.reply_text(
                "📭 *Aucun rappel trouvé.*",
                parse_mode="Markdown"
            )
            return

        # Création des boutons avec infos lisibles
        buttons = []
        for e in events:
            buttons.append([
                InlineKeyboardButton(
                    f"🗑️ {e.title} | {RecurrenceEnum(e.recurrence).value} | {e.event_datetime.strftime('%Y-%m-%d %H:%M')}",
                    callback_data=f'delete_event_{e.id}'
                )
            ])

        await update.message.reply_text(
            "👉 *Sélectionne l’événement que tu veux supprimer :*",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown"
        )

    finally:
        session.close()


async def button_click_delete_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith('delete_event_'):
        event_id = query.data.split('_')[2]
        session = Session()
        try:
            event = session.query(Event).filter_by(id=event_id).first()
            if not event:
                await query.edit_message_text(
                    "⚠️ *Cet événement n’existe plus ou a déjà été supprimé.*",
                    parse_mode="Markdown"
                )
                return

            session.delete(event)
            session.commit()

            await query.edit_message_text(
                f"✅ *Événement supprimé avec succès !*\n\n"
                f"📝 {event.title}\n"
                f"⏰ {event.event_datetime.strftime('%Y-%m-%d %H:%M')}",
                parse_mode="Markdown"
            )
        finally:
            session.close()
