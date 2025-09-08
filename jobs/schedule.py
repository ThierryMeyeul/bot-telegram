import logging
from datetime import timedelta, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from telegram.ext import ContextTypes

from db import Session
from models import Event, RecurrenceEnum, StatutEnum


scheduler = AsyncIOScheduler()


async def send_reminder(chat_id: int, event_id: int, title: str, context: ContextTypes.DEFAULT_TYPE):
    try:
        session = Session()
        event = session.query(Event).filter_by(id=event_id).first()
        recurrence_label = {
            RecurrenceEnum.DAILY: "chaque jour 🗓️",
            RecurrenceEnum.WEEKLY: "chaque semaine 📆",
            RecurrenceEnum.MONTHLY: "chaque mois 📅"
        }.get(event.recurrence, "")

        await context.bot.send_message(
            chat_id=chat_id,
            text=f"⏰ *Rappel récurrent :* `{title}`\n\n"
                 f"🔁 Cet événement revient *{recurrence_label}*.\n"
                 f"👉 N’oublie pas de t’y préparer !",
            parse_mode="Markdown"
        )
        if not event:
            return

        if event.recurrence == RecurrenceEnum.ONCE:
            event.status = StatutEnum.COMPLETED
            session.commit()
        else:
            if event.recurrence == RecurrenceEnum.DAILY:
                event.event_datetime +=timedelta(days=1)
            elif event.recurrence == RecurrenceEnum.WEEKLY:
                event.event_datetime += timedelta(weeks=1)
            elif event.recurrence == RecurrenceEnum.MONTHLY:
                event.event_datetime += timedelta(days=30)
            session.commit()
            schedule_event(telegram_id=event.user.telegram_id, event=event, context=context)
    finally:
        session.close()

logger = logging.getLogger(__name__)


def schedule_event(telegram_id: int, event: Event, context: ContextTypes.DEFAULT_TYPE):
    reminder_time = event.event_datetime
    if reminder_time > datetime.utcnow() and event.status == StatutEnum.ACTIVE:
        scheduler.add_job(
            send_reminder,
            trigger=DateTrigger(run_date=reminder_time),
            args=[telegram_id, event.id, event.title, context],
            id=f'event_{event.id}',
            replace_existing=True
        )
        logger.info(f'Scheduled event {event.id} at {reminder_time}')