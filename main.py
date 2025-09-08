import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import logging
from config import TOKEN
from db import Base, init_db, Session
import models
from handlers.start import start
from handlers.list_events import list_events
from  handlers.add_event import conv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from jobs.schedule import scheduler
from handlers.delete_event import delete_event, button_click_delete_event
from jobs.schedule import schedule_event
from models import Event, StatutEnum

logger = logging.getLogger(__name__)


async def _post_init(app: Application) -> None:
    try:
        loop = asyncio.get_running_loop()

        if not scheduler.running:
            scheduler._eventloop = loop
            scheduler.start()
        app.bot_data['scheduler'] = scheduler
        logger.info("Scheduler démarré avec succès")
    except Exception as e:
        logger.warning(f"[Main] Failed to start scheduler: {e}")


async def load_events(context: ContextTypes.DEFAULT_TYPE):
    session = Session()
    try:
        events = session.query(Event).filter_by(status=StatutEnum.ACTIVE).all()
        for event in events:
            schedule_event(event.user.telegram_id, event, context)
    finally:
        session.close()



def main() -> None:
    app = Application.builder().token(TOKEN).post_init(_post_init).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(list_events, pattern='^add_list_events'))
    app.add_handler(CommandHandler('listreminders', list_events))
    app.add_handler(CommandHandler('deletereminder', delete_event))
    app.add_handler(CallbackQueryHandler(button_click_delete_event, pattern='^delete_event'))
    app.job_queue.run_once(load_events, when=1)

    try:
        init_db()
    except Exception as e:
        logger.error(f"[Main] Failed to initialize database: {e}")

    print("Bot démarré... Appuie sur CTRL+C pour arrêter.")
    app.run_polling()


if __name__ == '__main__':
    logger.info("[Main] Running main application...")
    main()