import asyncio
import os
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from telegram.error import BadRequest

BOT_TOKEN = os.environ.get("BOT_TOKEN")

STAGE_TOPIC_ID = 4
MAX_VIOLATIONS = 3
BAN_DURATION = 172800

violations = {}


async def process_media(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = update.message

    if message.message_thread_id != STAGE_TOPIC_ID:
        return

    if not (message.photo or message.video):
        return

    chat_id = message.chat_id
    message_id = message.message_id
    user = message.from_user
    user_id = user.id

    username = f"@{user.username}" if user.username else user.first_name

    await asyncio.sleep(20)

    try:
        await context.bot.forward_message(chat_id, chat_id, message_id)

    except BadRequest:

        violations[user_id] = violations.get(user_id, 0) + 1
        strike = violations[user_id]

        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=STAGE_TOPIC_ID,
            text=f"⚠️ {username} violation {strike}/{MAX_VIOLATIONS}: Media removed under 20 seconds."
        )

        if strike >= MAX_VIOLATIONS:

            await context.bot.ban_chat_member(
                chat_id,
                user_id,
                until_date=int(time.time()) + BAN_DURATION
            )

            await context.bot.send_message(
                chat_id=chat_id,
                message_thread_id=STAGE_TOPIC_ID,
                text=f"🚫 {username} banned for 2 days (3 violations)."
            )

            violations[user_id] = 0

        return


async def media_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    asyncio.create_task(process_media(update, context))


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(
    MessageHandler(
        (filters.PHOTO | filters.VIDEO) & filters.ChatType.SUPERGROUP,
        media_handler
    )
)

print("Violation Bot running...")
app.run_polling()
