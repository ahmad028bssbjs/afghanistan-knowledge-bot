import os
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from database import search_documents


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN تنظیم نشده است.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🇦🇫 به ربات دانشنامه افغانستان خوش آمدید!\n\n"
        "🔎 برای جستجو، نام موضوع موردنظر را بفرست.\n\n"
        "مثال:\n"
        "احمدشاه ابدالی\n"
        "غزنی\n"
        "بند کجکی\n"
        "جنگ اول افغان و انگلیس"
    )


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()

    if not query:
        return

    results = search_documents(query)

    if not results:
        await update.message.reply_text(
            f"🔎 برای «{query}» چیزی در دانشنامه پیدا نشد.\n\n"
            "📚 منابع بیشتری به‌زودی اضافه می‌شوند."
        )
        return

    message = f"🔎 نتایج جستجو برای: {query}\n\n"

    for i, (_, title, category, content) in enumerate(results, 1):
        short_content = content[:500]

        message += (
            f"📌 {i}. {title}\n"
            f"📂 دسته: {category}\n"
            f"{short_content}\n\n"
        )

        if len(message) > 3500:
            break

    await update.message.reply_text(message)


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            search
        )
    )

    print("🇦🇫 Afghanistan Knowledge Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
