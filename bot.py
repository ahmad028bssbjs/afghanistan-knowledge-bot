import os
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# -----------------------------
# تنظیمات لاگ
# -----------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# -----------------------------
# دریافت توکن از Render
# -----------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")

print("BOT_TOKEN exists:", bool(BOT_TOKEN))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN تنظیم نشده است.")


# -----------------------------
# دستور /start
# -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🇦🇫 به ربات دانشنامه افغانستان خوش آمدید!\n\n"
        "📚 این دانشنامه در حال آماده‌سازی است.\n\n"
        "بعداً می‌توانی چیزهایی مثل:\n"
        "• تاریخ\n"
        "• شاهان\n"
        "• جنگ‌ها\n"
        "• شهرها\n"
        "• ولایت‌ها و ولسوالی‌ها\n"
        "• کوه‌ها و رودخانه‌ها\n"
        "• بندها\n"
        "را جستجو کنی."
    )


# -----------------------------
# اجرای ربات
# -----------------------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    print("🇦🇫 Afghanistan Knowledge Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
