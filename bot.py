import os
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get("8860953631:AAFDAk0bVYwRHRtFlwWL7DrVvGHD_Qcum5o")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🇦🇫 به ربات دانشنامه افغانستان خوش آمدید!\n\n"
        "فعلاً موتور جستجو در حال آماده‌سازی است."
    )


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN تنظیم نشده است.")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    print("🇦🇫 Afghanistan Knowledge Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
