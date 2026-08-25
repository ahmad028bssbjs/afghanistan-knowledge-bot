import os
import json
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from database import search_documents, add_document
from geography import AfghanistanGeography


# =========================================================
# تنظیمات
# =========================================================

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN تنظیم نشده است.")


# =========================================================
# جغرافیای افغانستان
# =========================================================

GEO = AfghanistanGeography()


# =========================================================
# اطلاعات بندهای افغانستان
# =========================================================

def load_dams():

    path = "afghanistan_dams.json"

    if not os.path.exists(path):

        print("⚠️ afghanistan_dams.json پیدا نشد.")

        return []

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


DAMS = load_dams()


# =========================================================
# جستجوی بندها
# =========================================================

def search_dams(query):

    query = query.lower().strip()

    results = []

    for dam in DAMS:

        text = " ".join(
            str(value)
            for value in dam.values()
        ).lower()

        if query in text:

            results.append(dam)

    return results


# =========================================================
# نمایش اطلاعات بند
# =========================================================

def dam_text(dam):

    object_id = dam.get(
        "OBJECTID",
        "نامشخص"
    )

    lat = dam.get(
        "lat",
        ""
    )

    lon = dam.get(
        "lon",
        ""
    )

    geo_method = dam.get(
        "geo_mtd",
        ""
    )

    qa_rank = dam.get(
        "qa_rank",
        ""
    )

    rv = dam.get(
        "rv_mcm_v11",
        ""
    )

    source = dam.get(
        "har_src",
        ""
    )

    text = (
        f"🏗 بند GeoDAR #{object_id}\n\n"

        f"📍 موقعیت:\n"
        f"عرض جغرافیایی: {lat}\n"
        f"طول جغرافیایی: {lon}\n\n"

        f"🛰 روش تعیین موقعیت:\n"
        f"{geo_method or 'ثبت نشده'}\n\n"

        f"✅ رتبه کنترل کیفیت:\n"
        f"{qa_rank or 'ثبت نشده'}\n\n"

        f"💧 حجم مخزن:\n"
        f"{rv if rv not in ('', '-999.0', '-999') else 'ثبت نشده'}\n\n"

        f"📚 منبع:\n"
        f"{source or 'ثبت نشده'}"
    )

    return text


# =========================================================
# /start
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    keyboard = [

        [
            InlineKeyboardButton(
                "🇦🇫 جغرافیای افغانستان",
                callback_data="geo_provinces"
            )
        ],

        [
            InlineKeyboardButton(
                "🏗 بندها و سدها",
                callback_data="dams"
            )
        ],

        [
            InlineKeyboardButton(
                "💧 مخزن‌ها",
                callback_data="reservoirs"
            )
        ]

    ]

    await update.message.reply_text(

        "🇦🇫 دانشنامه افغانستان\n\n"
        "یک موضوع را جستجو کن یا از منوی زیر استفاده کن.\n\n"

        "مثال:\n"
        "بند\n"
        "سد\n"
        "کابل\n"
        "مخزن",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# نمایش ۳۴ ولایت
# =========================================================

async def show_provinces(
    query
):

    provinces = GEO.get_provinces()

    buttons = []

    row = []

    for province in provinces:

        button = InlineKeyboardButton(

            province["name_fa"],

            callback_data=(
                f"province:{province['id']}"
            )
        )

        row.append(button)

        if len(row) == 2:

            buttons.append(row)

            row = []

    if row:

        buttons.append(row)

    buttons.append([

        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data="back_start"
        )

    ])

    await query.edit_message_text(

        "🇦🇫 **ولایت‌های افغانستان**\n\n"
        "یک ولایت را انتخاب کن:",

        reply_markup=InlineKeyboardMarkup(
            buttons
        ),

        parse_mode="Markdown"
    )


# =========================================================
# نمایش ولسوالی‌های یک ولایت
# =========================================================

async def show_districts(
    query,
    province_id
):

    province = GEO.get_province(
        province_id
    )

    if not province:

        await query.answer(
            "ولایت پیدا نشد.",
            show_alert=True
        )

        return

    districts = GEO.get_districts(
        province_id
    )

    buttons = []

    row = []

    for district in districts:

        button = InlineKeyboardButton(

            district["district_name_fa"],

            callback_data=(
                f"district:{district['district_id']}"
            )
        )

        row.append(button)

        if len(row) == 2:

            buttons.append(row)

            row = []

    if row:

        buttons.append(row)

    buttons.append([

        InlineKeyboardButton(
            "🔙 برگشت به ولایت‌ها",
            callback_data="geo_provinces"
        )

    ])

    await query.edit_message_text(

        f"🇦🇫 ولایت {province['name_fa']}\n\n"
        f"تعداد ولسوالی‌ها: {len(districts)}\n\n"
        "یک ولسوالی را انتخاب کن:",

        reply_markup=InlineKeyboardMarkup(
            buttons
        )
    )


# =========================================================
# نمایش اطلاعات ولسوالی
# =========================================================

async def show_district(
    query,
    district_id
):

    district = GEO.get_district(
        district_id
    )

    if not district:

        await query.answer(
            "ولسوالی پیدا نشد.",
            show_alert=True
        )

        return

    lat = district.get("latitude")
    lon = district.get("longitude")

    boundary_id = district.get(
        "boundary_id",
        "ثبت نشده"
    )

    boundary_name = district.get(
        "boundary_name",
        "ثبت نشده"
    )

    text = (
        f"📍 {district['district_name_fa']}\n\n"
        f"🏛 ولایت: {district['province_fa']}\n\n"
        f"🇬🇧 نام انگلیسی: {district['district_name_en']}\n\n"
        f"🆔 شناسه ولسوالی: {district['district_id']}\n\n"
        f"📌 مرکز ولسوالی:\n"
        f"عرض: {lat}\n"
        f"طول: {lon}\n\n"
        f"🗺 مرز جغرافیایی:\n"
        f"{boundary_name}\n\n"
        f"🔗 Boundary ID:\n"
        f"{boundary_id}"
    )

    buttons = []

    # 📍 مختصات واقعی ثبت‌شده
    if lat is not None and lon is not None:

        maps_url = (
            "https://www.google.com/maps/search/"
            f"?api=1&query={lat},{lon}"
        )

        buttons.append([
            InlineKeyboardButton(
                "📍 مختصات جغرافیایی",
                url=maps_url
            )
        ])

    # 🏙 جستجوی مرکز ولسوالی
    from urllib.parse import quote

    district_name = district.get(
        "district_name_en",
        ""
    )

    province_name = district.get(
        "province_en",
        ""
    )

    place_query = (
        f"{district_name}, "
        f"{province_name}, "
        "Afghanistan"
    )

    center_url = (
        "https://www.google.com/maps/search/"
        f"?api=1&query={quote(place_query)}"
    )

    buttons.append([
        InlineKeyboardButton(
            "🏙️ جستجوی مرکز ولسوالی",
            url=center_url
        )
    ])

    # 🔙 برگشت به ولسوالی‌ها
    buttons.append([
        InlineKeyboardButton(
            "🔙 برگشت به ولسوالی‌ها",
            callback_data=(
                f"province:{district['province_id']}"
            )
        )
    ])

    # 🔙 برگشت به ولایت‌ها
    buttons.append([
        InlineKeyboardButton(
            "🔙 برگشت به ولایت‌ها",
            callback_data="geo_provinces"
        )
    ])

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    data = query.data


    # -----------------------------------------------------
    # ولایت‌ها
    # -----------------------------------------------------

    if data == "geo_provinces":

        await show_provinces(
            query
        )

        return


    # -----------------------------------------------------
    # انتخاب ولایت
    # -----------------------------------------------------

    if data.startswith(
        "province:"
    ):

        province_id = data.split(
            ":",
            1
        )[1]

        await show_districts(
            query,
            province_id
        )

        return


    # -----------------------------------------------------
    # انتخاب ولسوالی
    # -----------------------------------------------------

    if data.startswith(
        "district:"
    ):

        district_id = data.split(
            ":",
            1
        )[1]

        await show_district(
            query,
            district_id
        )

        return


    # -----------------------------------------------------
    # بازگشت به Start
    # -----------------------------------------------------

    if data == "back_start":

        keyboard = [

            [
                InlineKeyboardButton(
                    "🇦🇫 جغرافیای افغانستان",
                    callback_data="geo_provinces"
                )
            ],

            [
                InlineKeyboardButton(
                    "🏗 بندها و سدها",
                    callback_data="dams"
                )
            ],

            [
                InlineKeyboardButton(
                    "💧 مخزن‌ها",
                    callback_data="reservoirs"
                )
            ]

        ]

        await query.edit_message_text(

            "🇦🇫 دانشنامه افغانستان\n\n"
            "یک موضوع را انتخاب کن:",

            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )

        return


    # -----------------------------------------------------
    # بندها
    # -----------------------------------------------------

    if data == "dams":

        if not DAMS:

            await query.edit_message_text(
                "⚠️ اطلاعات بندها پیدا نشد."
            )

            return

        message = (
            "🏗 **بندها و سدهای افغانستان**\n\n"
        )

        buttons = []

        for dam in DAMS[:20]:

            message += (
                dam_text(dam)
                + "\n"
                + "────────────\n\n"
            )

            lat = dam.get("lat")
            lon = dam.get("lon")

            if lat and lon:

                url = (
                    "https://www.google.com/maps/search/"
                    f"?api=1&query={lat},{lon}"
                )

                buttons.append([

                    InlineKeyboardButton(
                        "📍 مشاهده روی Google Maps",
                        url=url
                    )

                ])

            if len(message) > 3500:

                message += "..."

                break

        buttons.append([

            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data="back_start"
            )

        ])

        await query.edit_message_text(

            message[:4000],

            reply_markup=InlineKeyboardMarkup(
                buttons
            ),

            parse_mode="Markdown"
        )

        return


    # -----------------------------------------------------
    # مخزن‌ها
    # -----------------------------------------------------

    if data == "reservoirs":

        await query.edit_message_text(

            "💧 بخش مخزن‌ها\n\n"
            "این بخش را در مرحله بعد کامل می‌کنیم.",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🔙 بازگشت",
                        callback_data="back_start"
                    )
                ]

            ])
        )

        return


# =========================================================
# جستجوی متن
# =========================================================

async def search(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.message.text.strip()

    if not query:

        return


    # =====================================================
    # جستجوی بند
    # =====================================================

    dam_queries = [
        "بند",
        "سد",
        "dam"
    ]

    is_dam_search = any(

        word in query.lower()

        for word in dam_queries

    )


    if is_dam_search:

        results = search_dams(
            query
        )


        if query in [
            "بند",
            "سد",
            "dam"
        ]:

            results = DAMS


        if not results:

            await update.message.reply_text(

                "🔎 بندی با این جستجو پیدا نشد."

            )

            return


        message = (
            f"🏗 نتایج بندها برای «{query}»\n\n"
        )

        buttons = []


        for dam in results[:20]:

            message += (

                dam_text(dam)

                + "\n"
                + "────────────\n\n"

            )


            lat = dam.get("lat")
            lon = dam.get("lon")


            if lat and lon:

                url = (

                    "https://www.google.com/maps/search/"
                    f"?api=1&query={lat},{lon}"

                )

                buttons.append([

                    InlineKeyboardButton(

                        "📍 مشاهده روی Google Maps",

                        url=url

                    )

                ])


            if len(message) > 3500:

                message += "..."

                break


        await update.message.reply_text(

            message,

            reply_markup=(

                InlineKeyboardMarkup(buttons)

                if buttons

                else None

            )

        )

        return


    # =====================================================
    # جستجوی اطلاعات قبلی
    # =====================================================

    results = search_documents(
        query
    )


    if not results:

        await update.message.reply_text(

            f"🔎 برای «{query}» چیزی پیدا نشد."

        )

        return


    message = (

        f"🔎 نتایج برای «{query}»\n\n"

    )


    for i, result in enumerate(

        results,

        1

    ):

        _, title, category, content = result

        message += (

            f"📌 {i}. {title}\n"
            f"📂 {category}\n"
            f"📝 {content[:500]}\n\n"

        )


    await update.message.reply_text(

        message[:4000]

    )


# =========================================================
# اجرای ربات
# =========================================================

def main():

    app = (

        Application

        .builder()

        .token(BOT_TOKEN)

        .build()

    )


    # -----------------------------------------------------
    # /start
    # -----------------------------------------------------

    app.add_handler(

        CommandHandler(
            "start",
            start
        )

    )


    # -----------------------------------------------------
    # دکمه‌های Inline
    # -----------------------------------------------------

    app.add_handler(

        CallbackQueryHandler(
            button_handler
        )

    )


    # -----------------------------------------------------
    # پیام‌های متنی
    # -----------------------------------------------------

    app.add_handler(

        MessageHandler(

            filters.TEXT & ~filters.COMMAND,

            search

        )

    )


    print(
        "🇦🇫 Afghanistan Knowledge Bot is running..."
    )


    app.run_polling()


# =========================================================
# Main
# =========================================================

if __name__ == "__main__":

    main()
