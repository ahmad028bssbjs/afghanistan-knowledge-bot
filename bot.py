import os
import json
import logging
from urllib.parse import quote

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

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError(
        "❌ BOT_TOKEN تنظیم نشده است."
    )


# =========================================================
# جغرافیای افغانستان
# =========================================================

GEO = AfghanistanGeography()


# =========================================================
# اطلاعات سدها
# =========================================================

DAMS_FILE = (
    "data/dams/geodar_afghanistan_complete.json"
)


def load_dams():

    if not os.path.exists(DAMS_FILE):

        print("=" * 60)
        print("⚠️ فایل اطلاعات سدها پیدا نشد!")
        print(DAMS_FILE)
        print("=" * 60)

        return []

    try:

        with open(
            DAMS_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        # ساختار فایل:
        #
        # {
        #   "country": "Afghanistan",
        #   "country_iso": "AFG",
        #   "source": "GeoDAR v1.1",
        #   "count": 7,
        #   "dams": [...]
        # }

        if isinstance(data, dict):

            dams = data.get(
                "dams",
                []
            )

        elif isinstance(data, list):

            dams = data

        else:

            print(
                "❌ ساختار فایل سدها نامعتبر است."
            )

            return []

        print("=" * 60)
        print("✅ اطلاعات سدها بارگذاری شد")
        print("فایل:", DAMS_FILE)
        print("تعداد سدها:", len(dams))
        print("=" * 60)

        return dams

    except Exception as e:

        print("=" * 60)
        print("❌ خطا هنگام خواندن فایل سدها")
        print(e)
        print("=" * 60)

        return []


DAMS = load_dams()


# =========================================================
# جستجوی سد
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
# تبدیل مقدار خالی
# =========================================================

def clean_value(value):

    if value is None:
        return "ثبت نشده"

    value = str(value)

    if value.strip() == "":
        return "ثبت نشده"

    if value in (
        "-999",
        "-999.0",
        "None"
    ):
        return "ثبت نشده"

    return value


# =========================================================
# متن اطلاعات سد
# =========================================================

def dam_text(dam):

    dam_id = clean_value(
        dam.get("geodar_id")
    )

    province = clean_value(
        dam.get("province")
    )

    district = clean_value(
        dam.get("district")
    )

    center = clean_value(
        dam.get("province_center")
    )

    distance = clean_value(
        dam.get(
            "distance_to_province_center_km"
        )
    )

    latitude = clean_value(
        dam.get("latitude")
    )

    longitude = clean_value(
        dam.get("longitude")
    )

    grand_id = clean_value(
        dam.get("grand_id")
    )

    geo_method = clean_value(
        dam.get("geo_method")
    )

    qa_rank = clean_value(
        dam.get("qa_rank")
    )

    reservoir = clean_value(
        dam.get(
            "reservoir_volume_mcm_v11"
        )
    )

    source = clean_value(
        dam.get("source")
    )

    return (
        f"🏗 **سد GeoDAR #{dam_id}**\n\n"

        f"🇦🇫 **ولایت:** {province}\n"

        f"🏘 **ولسوالی:** {district}\n"

        f"🏙 **مرکز ولایت:** {center}\n"

        f"📏 **فاصله تا مرکز:** "
        f"{distance} km\n\n"

        f"📍 **مختصات:**\n"
        f"عرض: {latitude}\n"
        f"طول: {longitude}\n\n"

        f"🆔 **GRanD ID:** {grand_id}\n\n"

        f"🛰 **روش تعیین موقعیت:**\n"
        f"{geo_method}\n\n"

        f"✅ **رتبه کیفیت:** {qa_rank}\n\n"

        f"💧 **حجم مخزن:**\n"
        f"{reservoir} MCM\n\n"

        f"📚 **منبع:** {source}"
    )


# =========================================================
# دکمه‌های صفحه سدها
# =========================================================

def dam_buttons(dam):

    latitude = dam.get(
        "latitude"
    )

    longitude = dam.get(
        "longitude"
    )

    buttons = []

    if latitude is not None and longitude is not None:

        maps_url = (
            "https://www.google.com/maps/search/"
            f"?api=1&query="
            f"{latitude},{longitude}"
        )

        buttons.append([

            InlineKeyboardButton(
                "📍 مشاهده روی Google Maps",
                url=maps_url
            )

        ])

    return buttons


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

        "یک موضوع را جستجو کن "
        "یا از منوی زیر استفاده کن.\n\n"

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
# نمایش ولایت‌ها
# =========================================================

async def show_provinces(query):

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
# نمایش ولسوالی‌ها
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
                f"district:"
                f"{district['district_id']}"
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

        f"تعداد ولسوالی‌ها: "
        f"{len(districts)}\n\n"

        "یک ولسوالی را انتخاب کن:",

        reply_markup=InlineKeyboardMarkup(
            buttons
        )
    )


# =========================================================
# اطلاعات ولسوالی
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

    lat = district.get(
        "latitude"
    )

    lon = district.get(
        "longitude"
    )

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

        f"🏛 ولایت: "
        f"{district['province_fa']}\n\n"

        f"🇬🇧 نام انگلیسی: "
        f"{district['district_name_en']}\n\n"

        f"🆔 شناسه ولسوالی: "
        f"{district['district_id']}\n\n"

        f"📌 مرکز ولسوالی:\n"
        f"عرض: {lat}\n"
        f"طول: {lon}\n\n"

        f"🗺 مرز جغرافیایی:\n"
        f"{boundary_name}\n\n"

        f"🔗 Boundary ID:\n"
        f"{boundary_id}"
    )

    buttons = []

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

    buttons.append([

        InlineKeyboardButton(
            "🔙 برگشت به ولسوالی‌ها",
            callback_data=(
                f"province:"
                f"{district['province_id']}"
            )
        )

    ])

    buttons.append([

        InlineKeyboardButton(
            "🔙 برگشت به ولایت‌ها",
            callback_data="geo_provinces"
        )

    ])

    await query.edit_message_text(

        text,

        reply_markup=InlineKeyboardMarkup(
            buttons
        )
    )


# =========================================================
# نمایش سدها
# =========================================================

async def show_dams(query):

    if not DAMS:

        await query.edit_message_text(

            "⚠️ اطلاعات سدها پیدا نشد.\n\n"

            "فایل مورد نیاز:\n"
            f"{DAMS_FILE}",

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

    message = (
        "🏗 **بندها و سدهای افغانستان**\n\n"
        f"تعداد سدهای ثبت‌شده: {len(DAMS)}\n\n"
    )

    buttons = []

    for index, dam in enumerate(
        DAMS,
        1
    ):

        message += (
            f"━━━━━━━━━━━━━━\n\n"
            f"🔢 **سد شماره {index}**\n\n"
            f"{dam_text(dam)}\n\n"
        )

        dam_map_buttons = dam_buttons(
            dam
        )

        buttons.extend(
            dam_map_buttons
        )

        # محدودیت تلگرام
        if len(message) > 3500:

            message += (
                "\n⚠️ ادامه اطلاعات "
                "در پیام بعدی خواهد بود."
            )

            break

    buttons.append([

        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data="back_start"
        )

    ])

    await query.edit_message_text(

        message,

        reply_markup=InlineKeyboardMarkup(
            buttons
        ),

        parse_mode="Markdown"
    )


# =========================================================
# مدیریت دکمه‌ها
# =========================================================

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
    # سدها
    # -----------------------------------------------------

    if data == "dams":

        await show_dams(
            query
        )

        return


    # -----------------------------------------------------
    # مخزن‌ها
    # -----------------------------------------------------

    if data == "reservoirs":

        await query.edit_message_text(

            "💧 **بخش مخزن‌ها**\n\n"

            "این بخش را در مرحله بعد "
            "کامل می‌کنیم.",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🔙 بازگشت",
                        callback_data="back_start"
                    )
                ]

            ]),

            parse_mode="Markdown"
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

            "🇦🇫 **دانشنامه افغانستان**\n\n"
            "یک موضوع را انتخاب کن:",

            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),

            parse_mode="Markdown"
        )

        return


# =========================================================
# جستجوی متنی
# =========================================================

async def search(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.message.text.strip()

    if not query:

        return


    # =====================================================
    # جستجوی سد
    # =====================================================

    dam_keywords = [
        "بند",
        "سد",
        "dam",
        "dams",
        "geodar"
    ]

    is_dam_search = any(

        word in query.lower()

        for word in dam_keywords

    )


    if is_dam_search:

        results = search_dams(
            query
        )

        # اگر فقط «سد» یا «بند» نوشته شد
        if query.lower() in [
            "بند",
            "سد",
            "dam",
            "dams",
            "geodar"
        ]:

            results = DAMS


        if not results:

            await update.message.reply_text(

                "🔎 بندی با این جستجو پیدا نشد."

            )

            return


        message = (
            f"🏗 **نتایج بندها برای "
            f"«{query}»**\n\n"
        )

        buttons = []

        for index, dam in enumerate(
            results,
            1
        ):

            message += (
                f"━━━━━━━━━━━━━━\n\n"
                f"🔢 **نتیجه {index}**\n\n"
                f"{dam_text(dam)}\n\n"
            )

            buttons.extend(
                dam_buttons(dam)
            )

            if len(message) > 3500:

                message += "\n..."

                break


        await update.message.reply_text(

            message,

            reply_markup=(

                InlineKeyboardMarkup(
                    buttons
                )

                if buttons

                else None

            ),

            parse_mode="Markdown"
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

            f"🔎 برای «{query}» "
            "چیزی پیدا نشد."

        )

        return


    message = (
        f"🔎 **نتایج برای «{query}»**\n\n"
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

        message[:4000],

        parse_mode="Markdown"

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


    # /start
    app.add_handler(

        CommandHandler(
            "start",
            start
        )

    )


    # دکمه‌ها
    app.add_handler(

        CallbackQueryHandler(
            button_handler
        )

    )


    # پیام‌های متنی
    app.add_handler(

        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            search
        )

    )


    print("=" * 60)
    print(
        "🇦🇫 Afghanistan Knowledge Bot"
    )
    print(
        "✅ ربات در حال اجرا است..."
    )
    print(
        "🏗 تعداد سدهای بارگذاری‌شده:",
        len(DAMS)
    )
    print("=" * 60)


    app.run_polling()


# =========================================================
# Main
# =========================================================

if __name__ == "__main__":

    main()
