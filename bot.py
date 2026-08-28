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

from database import search_documents
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
    raise RuntimeError("BOT_TOKEN تنظیم نشده است.")


# =========================================================
# جغرافیای افغانستان
# =========================================================

GEO = AfghanistanGeography()


# =========================================================
# فایل سدها
# =========================================================

DAMS_FILE = "data/dams/geodar_afghanistan_complete.json"


def load_dams():

    if not os.path.exists(DAMS_FILE):

        print("⚠️ فایل سدها پیدا نشد:")
        print(DAMS_FILE)

        return []

    try:

        with open(
            DAMS_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        dams = data.get("dams", [])

        print("=" * 60)
        print("✅ اطلاعات سدها بارگذاری شد")
        print(f"فایل: {DAMS_FILE}")
        print(f"تعداد سدها: {len(dams)}")
        print("=" * 60)

        return dams

    except Exception as e:

        print("❌ خطا در خواندن فایل سدها:")
        print(e)

        return []


DAMS = load_dams()


# =========================================================
# جستجوی سدها
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

def clean_value(value, default="ثبت نشده"):

    if value is None:
        return default

    value = str(value).strip()

    if value in (
        "",
        "-999",
        "-999.0",
        "-999.00",
        "None",
        "null"
    ):
        return default

    return value


# =========================================================
# اطلاعات کامل یک سد
# =========================================================

def dam_text(dam, number=None):

    geodar_id = clean_value(
        dam.get("geodar_id")
    )

    dam_name = clean_value(
        dam.get("dam_name"),
        "نام ثبت نشده"
    )

    district = clean_value(
        dam.get("district")
    )

    province = clean_value(
        dam.get("province")
    )

    province_center = clean_value(
        dam.get("province_center")
    )

    distance = clean_value(
        dam.get("distance_to_province_center_km")
    )

    lat = clean_value(
        dam.get("latitude")
    )

    lon = clean_value(
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
        dam.get("reservoir_volume_mcm_v11")
    )

    source = clean_value(
        dam.get("source")
    )

    # -----------------------------------------------------
    # اطلاعات توضیحی جدید
    # -----------------------------------------------------

    description = clean_value(
        dam.get("description"),
        ""
    )

    location_description = clean_value(
        dam.get("location_description"),
        ""
    )

    type_description = clean_value(
        dam.get("type_description"),
        ""
    )

    history_description = clean_value(
        dam.get("history_description"),
        ""
    )

    purpose_description = clean_value(
        dam.get("purpose_description"),
        ""
    )

    importance_description = clean_value(
        dam.get("importance_description"),
        ""
    )

    power_description = clean_value(
        dam.get("power_description"),
        ""
    )

    # =====================================================
    # ساخت متن
    # =====================================================

    text = ""

    if number is not None:

        text += (
            f"🔢 سد شماره {number}\n\n"
        )

    text += (
        f"🏗 **{dam_name}**\n"
        f"🇬🇧 {dam_name}\n\n"
    )

    text += (
        f"🆔 GeoDAR ID: {geodar_id}\n\n"
    )

    text += (
        "📍 **موقعیت**\n"
        f"🇦🇫 ولایت: {province}\n"
        f"🏘 ولسوالی: {district}\n"
        f"🏙 مرکز ولایت: {province_center}\n"
        f"📏 فاصله تا مرکز ولایت: {distance} km\n\n"
    )

    text += (
        "🌐 **مختصات**\n"
        f"عرض جغرافیایی: {lat}\n"
        f"طول جغرافیایی: {lon}\n\n"
    )

    text += (
        "🆔 **اطلاعات پایگاه داده**\n"
        f"GRanD ID: {grand_id}\n\n"
    )

    text += (
        "🛰 **روش تعیین موقعیت**\n"
        f"{geo_method}\n\n"
    )

    text += (
        "✅ **رتبه کنترل کیفیت**\n"
        f"{qa_rank}\n\n"
    )

    text += (
        "💧 **حجم مخزن**\n"
        f"{reservoir} MCM\n\n"
    )

    # -----------------------------------------------------
    # توضیحات
    # -----------------------------------------------------

    if description:
        text += (
            "📖 **توضیحات**\n"
            f"{description}\n\n"
        )

    if location_description:
        text += (
            "📍 **موقعیت و محل سد**\n"
            f"{location_description}\n\n"
        )

    if type_description:
        text += (
            "🏗 **نوع سد**\n"
            f"{type_description}\n\n"
        )

    if history_description:
        text += (
            "📜 **تاریخچه و ساخت**\n"
            f"{history_description}\n\n"
        )

    if purpose_description:
        text += (
            "🎯 **کاربرد**\n"
            f"{purpose_description}\n\n"
        )

    if importance_description:
        text += (
            "⭐ **اهمیت**\n"
            f"{importance_description}\n\n"
        )

    if power_description:
        text += (
            "⚡ **برق و ظرفیت تولید**\n"
            f"{power_description}\n\n"
        )

    text += (
        "📚 **منبع**\n"
        f"{source}"
    )

    return text


# =========================================================
# دکمه‌های سد
# =========================================================

def dam_buttons(dam):

    buttons = []

    dam_name = clean_value(
        dam.get("dam_name"),
        "سد"
    )

    lat = dam.get("latitude")
    lon = dam.get("longitude")

    # -----------------------------------------------------
    # Google Maps
    # -----------------------------------------------------

    if lat is not None and lon is not None:

        maps_url = (
            "https://www.google.com/maps/search/"
            f"?api=1&query={lat},{lon}"
        )

        buttons.append([

            InlineKeyboardButton(
                f"📍 نقشه {dam_name}",
                url=maps_url
            )

        ])

    return buttons


# =========================================================
# منوی اصلی
# =========================================================

def main_keyboard():

    return InlineKeyboardMarkup([

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

    ])


# =========================================================
# /start
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "🇦🇫 **دانشنامه افغانستان**\n\n"
        "یک موضوع را انتخاب کن یا جستجو کن.\n\n"
        "مثال:\n"
        "بند\n"
        "سد\n"
        "کابل\n"
        "مخزن",

        reply_markup=main_keyboard(),

        parse_mode="Markdown"
    )


# =========================================================
# نمایش ولایت‌ها
# =========================================================

async def show_provinces(query):

    provinces = GEO.get_provinces()

    buttons = []

    row = []

    for province in provinces:

        row.append(

            InlineKeyboardButton(
                province["name_fa"],
                callback_data=(
                    f"province:{province['id']}"
                )
            )

        )

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

        reply_markup=InlineKeyboardMarkup(buttons),

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

        row.append(

            InlineKeyboardButton(

                district["district_name_fa"],

                callback_data=(
                    f"district:{district['district_id']}"
                )

            )

        )

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

        reply_markup=InlineKeyboardMarkup(buttons)
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
                f"province:{district['province_id']}"
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
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# =========================================================
# نمایش سدها
# =========================================================

async def show_dams(query):

    if not DAMS:

        await query.edit_message_text(

            "⚠️ اطلاعات سدها پیدا نشد.",

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

    # -----------------------------------------------------
    # برای جلوگیری از عبور پیام تلگرام از محدودیت،
    # هر سد جداگانه ارسال نمی‌شود؛
    # یک فهرست خلاصه + دکمه برای هر سد می‌سازیم.
    # -----------------------------------------------------

    message = (
        "🏗 **بندها و سدهای افغانستان**\n\n"
        f"تعداد سدهای ثبت‌شده: {len(DAMS)}\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
    )

    buttons = []

    for index, dam in enumerate(DAMS, 1):

        name = clean_value(
            dam.get("dam_name"),
            "سد بدون نام"
        )

        province = clean_value(
            dam.get("province")
        )

        district = clean_value(
            dam.get("district")
        )

        message += (
            f"🔢 **سد شماره {index}**\n"
            f"🏗 {name}\n"
            f"🇦🇫 ولایت: {province}\n"
            f"🏘 ولسوالی: {district}\n\n"
        )

        buttons.append([

            InlineKeyboardButton(
                f"📖 اطلاعات {name}",
                callback_data=f"dam:{index - 1}"
            )

        ])

        buttons.append([

            InlineKeyboardButton(
                f"📍 نقشه {name}",
                url=(
                    "https://www.google.com/maps/search/"
                    f"?api=1&query="
                    f"{dam.get('latitude')},{dam.get('longitude')}"
                )
            )

        ])

    buttons.append([

        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data="back_start"
        )

    ])

    await query.edit_message_text(

        message,

        reply_markup=InlineKeyboardMarkup(buttons),

        parse_mode="Markdown"
    )


# =========================================================
# نمایش اطلاعات یک سد
# =========================================================

async def show_single_dam(
    query,
    dam_index
):

    try:

        index = int(dam_index)

    except ValueError:

        await query.answer(
            "شناسه سد نامعتبر است.",
            show_alert=True
        )

        return

    if index < 0 or index >= len(DAMS):

        await query.answer(
            "سد پیدا نشد.",
            show_alert=True
        )

        return

    dam = DAMS[index]

    text = dam_text(
        dam,
        index + 1
    )

    buttons = dam_buttons(dam)

    # -----------------------------------------------------
    # سد قبلی / بعدی
    # -----------------------------------------------------

    navigation = []

    if index > 0:

        navigation.append(

            InlineKeyboardButton(
                "⬅️ سد قبلی",
                callback_data=f"dam:{index - 1}"
            )

        )

    if index < len(DAMS) - 1:

        navigation.append(

            InlineKeyboardButton(
                "سد بعدی ➡️",
                callback_data=f"dam:{index + 1}"
            )

        )

    if navigation:
        buttons.append(navigation)

    buttons.append([

        InlineKeyboardButton(
            "🔙 فهرست سدها",
            callback_data="dams"
        )

    ])

    await query.edit_message_text(

        text[:4000],

        reply_markup=InlineKeyboardMarkup(buttons),

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

        await show_provinces(query)

        return

    # -----------------------------------------------------
    # انتخاب ولایت
    # -----------------------------------------------------

    if data.startswith("province:"):

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

    if data.startswith("district:"):

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
    # فهرست سدها
    # -----------------------------------------------------

    if data == "dams":

        await show_dams(query)

        return

    # -----------------------------------------------------
    # اطلاعات یک سد
    # -----------------------------------------------------

    if data.startswith("dam:"):

        dam_index = data.split(
            ":",
            1
        )[1]

        await show_single_dam(
            query,
            dam_index
        )

        return

    # -----------------------------------------------------
    # مخزن‌ها
    # -----------------------------------------------------

    if data == "reservoirs":

        await query.edit_message_text(

            "💧 **بخش مخزن‌ها**\n\n"
            "این بخش را در مرحله بعد کامل می‌کنیم.",

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

        await query.edit_message_text(

            "🇦🇫 **دانشنامه افغانستان**\n\n"
            "یک موضوع را انتخاب کن:",

            reply_markup=main_keyboard(),

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

    user_query = update.message.text.strip()

    if not user_query:

        return

    query_lower = user_query.lower()

    # -----------------------------------------------------
    # تشخیص جستجوی سد
    # -----------------------------------------------------

    dam_keywords = [
        "بند",
        "سد",
        "dam",
        "dams"
    ]

    is_dam_search = any(

        word in query_lower

        for word in dam_keywords

    )

    if is_dam_search:

        results = search_dams(
            user_query
        )

        # اگر فقط «سد» یا «بند» نوشته شد،
        # همه سدها را نمایش بده.

        if query_lower in (
            "بند",
            "سد",
            "dam",
            "dams"
        ):

            results = DAMS

        if not results:

            await update.message.reply_text(

                "🔎 بندی با این جستجو پیدا نشد."

            )

            return

        message = (
            f"🏗 **نتایج سدها برای «{user_query}»**\n\n"
        )

        buttons = []

        for index, dam in enumerate(
            results[:20],
            1
        ):

            name = clean_value(
                dam.get("dam_name"),
                "سد بدون نام"
            )

            province = clean_value(
                dam.get("province")
            )

            district = clean_value(
                dam.get("district")
            )

            message += (
                f"🔢 {index}. **{name}**\n"
                f"🇦🇫 ولایت: {province}\n"
                f"🏘 ولسوالی: {district}\n\n"
            )

            # پیدا کردن index واقعی در DAMS

            try:

                real_index = DAMS.index(dam)

            except ValueError:

                real_index = 0

            buttons.append([

                InlineKeyboardButton(
                    f"📖 اطلاعات {name}",
                    callback_data=f"dam:{real_index}"
                )

            ])

            lat = dam.get("latitude")
            lon = dam.get("longitude")

            if lat is not None and lon is not None:

                maps_url = (
                    "https://www.google.com/maps/search/"
                    f"?api=1&query={lat},{lon}"
                )

                buttons.append([

                    InlineKeyboardButton(
                        f"📍 نقشه {name}",
                        url=maps_url
                    )

                ])

        await update.message.reply_text(

            message[:4000],

            reply_markup=InlineKeyboardMarkup(buttons),

            parse_mode="Markdown"
        )

        return

    # -----------------------------------------------------
    # جستجوی اطلاعات عمومی
    # -----------------------------------------------------

    results = search_documents(
        user_query
    )

    if not results:

        await update.message.reply_text(

            f"🔎 برای «{user_query}» چیزی پیدا نشد."

        )

        return

    message = (
        f"🔎 **نتایج برای «{user_query}»**\n\n"
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

    print("=" * 60)
    print("🇦🇫 Afghanistan Knowledge Bot")
    print("✅ ربات در حال اجرا است...")
    print(
        f"🏗 تعداد سدهای بارگذاری‌شده: {len(DAMS)}"
    )
    print("=" * 60)

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
    # دکمه‌ها
    # -----------------------------------------------------

    app.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )

    # -----------------------------------------------------
    # پیام متنی
    # -----------------------------------------------------

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            search
        )
    )

    app.run_polling()


# =========================================================
# Main
# =========================================================

if __name__ == "__main__":

    main()
