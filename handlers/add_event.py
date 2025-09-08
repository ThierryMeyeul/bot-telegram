from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, \
    filters
from datetime import datetime, timedelta
from db import Session
from models import User, Event, RecurrenceEnum
from jobs.schedule import schedule_event


CHOOSING_RECURRENCE, TYPING_DATE, TYPING_TITLE, TYPING_HOUR = range(4)


async def add_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:  # si ça vient d'un bouton
        query = update.callback_query
        await query.answer()
        send = query.edit_message_text
    else:  # si ça vient d'une commande (/reminder)
        send = update.message.reply_text

    buttons = [
        [
            InlineKeyboardButton('📅 Une seule fois', callback_data='add_event_once'),
            InlineKeyboardButton('🔁 Chaque jour', callback_data='add_event_daily')
        ],
        [
            InlineKeyboardButton('📆 Chaque semaine', callback_data='add_event_weekly'),
            InlineKeyboardButton('🗓️ Chaque mois', callback_data='add_event_monthly')
        ]
    ]
    context.user_data['in_conversation'] = True
    await send(
        "📅 Choisis la récurrence de ton rappel :\n\n"
        "• une seule fois (ex: rendez-vous médecin)\n"
        "• chaque jour (ex: prendre un médicament)\n"
        "• chaque semaine (ex: réunion d’équipe)\n"
        "• chaque mois (ex: payer une facture)\n\n"
        "👉 Clique sur un bouton ci-dessous ⬇️",
        reply_markup=InlineKeyboardMarkup(buttons))
    return CHOOSING_RECURRENCE



async def button_click_select_recurrence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not query.data.startswith('add_event_'):
        await query.edit_message_text("Option invalide.")
        return ConversationHandler.END

    recurrence = query.data.split('_', 2)[2]  # once / daily / weekly / monthly
    context.user_data['recurrence'] = recurrence

    if recurrence == 'once':
        await query.edit_message_text(
            "🗓️ Entre la date *et l’heure* de ton rappel :\n\n"
            "Format attendu : `YYYY-MM-DD HH:MM`\n"
            "Exemple : `2025-09-08 14:45`\n\n"
            "⚠️ Tape `/cancel` à tout moment pour annuler.",
            parse_mode="Markdown"
        )

        return TYPING_DATE
    else:
        await query.edit_message_text(
            "⏰ Indique l’heure de ton rappel récurrent :\n\n"
            "Format attendu : `HH:MM`\n"
            "Exemple : `09:30` ou `18:00`\n\n"
            "⚠️ Tape `/cancel` à tout moment pour annuler.",
            parse_mode="Markdown"
        )

        return TYPING_HOUR



async def input_hour(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hour_text = update.message.text.strip()
    try:
        # On valide juste le format HH:MM, mais on garde la chaîne pour éviter le TypeError plus tard
        datetime.strptime(hour_text, '%H:%M')
        context.user_data['hour'] = hour_text
        await update.message.reply_text(
            "📝 Super ! Maintenant, donne un **titre** à ton rappel.\n\n"
            "Exemple : `Réunion projet`, `Aller à la salle de sport`, `Appeler maman`\n\n"
            "⚠️ Tape `/cancel` à tout moment pour annuler.",
            parse_mode='Markdown'
        )
        return TYPING_TITLE
    except ValueError:
        await update.message.reply_text(
            "❌ Format invalide !\n\n"
            "👉 Utilise : `YYYY-MM-DD HH:MM`\n"
            "Exemple : `2025-09-08 14:45`"
        )
        return TYPING_HOUR


async def input_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date_text = update.message.text.strip()
    try:
        # On parse en datetime directement et on stocke l'objet
        dt = datetime.strptime(date_text, "%Y-%m-%d %H:%M")
        context.user_data['date'] = dt
        await update.message.reply_text(
            "📝 Super ! Maintenant, donne un **titre** à ton rappel.\n\n"
            "Exemple : `Réunion projet`, `Aller à la salle de sport`, `Appeler maman`\n\n"
            "⚠️ Tape `/cancel` à tout moment pour annuler.",
            parse_mode='Markdown'
        )
        return TYPING_TITLE
    except ValueError:
        await update.message.reply_text(
            "❌ Format invalide !\n\n"
            "👉 Utilise : `HH:MM`\n"
            "Exemple : `08:00` ou `20:45`"
        )
        return TYPING_DATE


async def input_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = update.message.text.strip()
    recurrence = context.user_data.get('recurrence')
    if not recurrence:
        await update.message.reply_text("Récurrence introuvable. Reprenez la commande /reminder.")
        return ConversationHandler.END
    if recurrence != 'once':
        hour_str = context.user_data.get('hour')
        if not hour_str:
            await update.message.reply_text("Heure manquante. Reprenez l'étape de saisie de l'heure.")
            return TYPING_HOUR
        hh, mm = map(int, hour_str.split(':'))
        now = datetime.utcnow()
        event_time = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if event_time <= now:
            if recurrence == 'daily':
                event_time += timedelta(days=1)
            elif recurrence == 'weekly':
                event_time += timedelta(weeks=1)
            elif recurrence == 'monthly':
                event_time += timedelta(days=30)
            else:
                await update.message.reply_text("Récurrence invalide.")
                return ConversationHandler.END
    else:
        dt: datetime | None = context.user_data.get('date')
        if not isinstance(dt, datetime):
            await update.message.reply_text("Date invalide. Reprenez l'étape de saisie de la date.")
            return TYPING_DATE
        event_time = dt
        if event_time <= datetime.utcnow():
            await update.message.reply_text("La date/heure doit être dans le futur. Réessayez :")
            return TYPING_DATE

    session = Session()
    try:
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
        if not user:
            user = User(
                telegram_id=update.effective_user.id,
                name=update.effective_user.username or 'Unknown'
            )
            session.add(user)
            session.commit()
            session.refresh(user)

        event = Event(
            title=title,
            event_datetime=event_time,
            recurrence=RecurrenceEnum[recurrence.upper()],
            user_id=user.id
        )

        session.add(event)
        session.commit()
        session.refresh(event)
    except Exception as e:
        session.rollback()
        await update.message.reply_text(f"Erreur lors de l'enregistrement : {e}")
        return ConversationHandler.END
    finally:
        session.close()

    schedule_event(telegram_id=user.telegram_id, event=event, context=context)

    if recurrence == 'once':
        recap_time = event_time.strftime("%Y-%m-%d %H:%M")
    else:
        recap_time = event_time.strftime("%H:%M")

    await update.message.reply_text(
        f"🎉 *Ton rappel a bien été enregistré !*\n\n"
        f"📌 *Titre* : {title}\n"
        f"🔁 *Récurrence* : {recurrence}\n"
        f"⏰ *Prochain rappel* : `{recap_time}`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('📋 Voir mes rappels', callback_data='add_list_events')]])
    )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('in_conversation'):
        context.user_data['in_conversation'] = False
        await update.message.reply_text(
            "❌ *Conversation annulée avec succès.*\n\n"
            "👉 Tu peux maintenant lancer une nouvelle commande.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "ℹ️ *Aucune conversation en cours.*\n\n"
            "👉 Lance une commande comme `/reminder` pour commencer.",
            parse_mode="Markdown"
        )
    return ConversationHandler.END


async def command_already_active(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚠️ *Une conversation est déjà en cours.*\n\n"
        "👉 Tape `/cancel` pour l’annuler avant de relancer une nouvelle commande.",
        parse_mode="Markdown"
    )
    return


conv = ConversationHandler(
    entry_points=[
        CommandHandler('reminder', add_event),
        CallbackQueryHandler(add_event, pattern='^list_add_event')
    ],
    states={
        CHOOSING_RECURRENCE: [CallbackQueryHandler(button_click_select_recurrence, pattern='^add_event')],
        TYPING_HOUR: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_hour)],
        TYPING_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_date)],
        TYPING_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_title)]
    },
    fallbacks=[CommandHandler('cancel', cancel), CommandHandler('reminder', command_already_active)]
)