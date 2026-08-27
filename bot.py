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
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN تنظیم نشده است.")


# =========================================================
# جغرافیای افغانستان
# =========================================================

GEO = AfghanistanGeography()


# =========================================================
# اطلاعات سدهای افغانستان
# =========================================================

DAMS_FILE = "data/dams/geodar_afghanistan_complete.json"


def load_dams():

    if not os.path.exists(DAMS_FILE):

        print("⚠️ فایل اطلاعات سدها پیدا نشد:")
        print(DAMS_FILE)

        return []

    try:

        with open(
            DAMS_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        # -------------------------------------------------
        # فایل اصلی به شکل:
        #
        # {
        #   "country": "Afghanistan",
        #   "count": 7,
        #   "dams": [...]
        # }
        # -------------------------------------------------

        if isinstance(data, dict):

            dams = data.get("dams", [])

        elif isinstance(data, list):

            dams = data

        else:

            print("⚠️ ساختار فایل سدها نامعتبر است.")

            return []

        if not isinstance(dams, list):

            print("⚠️ بخش dams یک لیست نیست.")

            return []

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
# ابزارهای کمکی سدها
# =========================================================

def dam_id(dam):

    return str(
        dam.get(
            "geodar_id",
            dam.get(
                "id_v11",
                dam.get(
                    "OBJECTID",
                    "?"
                )
            )
        )
    )


def dam_name(dam):

    return dam.get(
        "dam_name",
        f"سد GeoDAR #{dam_id(dam)}"
    )


def dam_lat(dam):

    value = dam.get(
        "latitude",
        dam.get(
            "lat",
            ""
        )
    )

    return value


def dam_lon(dam):

    value = dam.get(
        "longitude",
        dam.get(
            "lon",
            ""
        )
    )

    return value


def clean_value(value, default="ثبت نشده"):

    if value is None:
        return default

    value = str(value).strip()

    if value in (
        "",
        "-999",
        "-999.0",
        "-999.00"
    ):
        return default

    return value


# =========================================================
# متن کامل اطلاعات سد
# =========================================================

def dam_text(dam, number=None):

    d_id = dam_id(dam)

    name = dam_name(dam)

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
        ),
        "ثبت نشده"
    )

    # پشتیبانی از نام‌های مختلف فیلد حجم
    reservoir_volume = dam.get(
        "reservoir_volume_mcm_v11",
        dam.get(
            "rv_mcm_v11",
            dam.get(
                "reservoir_volume_mcm_v10",
                ""
            )
        )
    )

    reservoir_volume = clean_value(
        reservoir_volume
    )

    geo_method = clean_value(
        dam.get(
            "geo_method",
            dam.get(
                "geo_mtd",
                ""
            )
        )
    )

    qa_rank = clean_value(
        dam.get("qa_rank")
    )

    grand_id = clean_value(
        dam.get(
            "grand_id",
            dam.get(
                "id_grd_v13",
                ""
            )
        )
    )

    source = clean_value(
        dam.get("source")
    )

    lat = dam_lat(dam)

    lon = dam_lon(dam)

    if number is None:

        number = d_id

    text = (
        f"🔢 سد شماره {number}\n\n"

        f"🏗 {name}\n\n"

        f"🆔 GeoDAR ID: {d_id}\n\n"

        f"🇦🇫 ولایت: {province}\n"
        f"🏘 ولسوالی: {district}\n"
        f"🏙 مرکز ولایت: {center}\n"
        f"📏 فاصله تا مرکز: {distance} km\n\n"

        f"📍 مختصات:\n"
        f"عرض: {lat}\n"
        f"طول: {lon}\n\n"

        f"🆔 GRanD ID: {grand_id}\n\n"

        f"🛰 روش تعیین موقعیت:\n"
        f"{geo_method}\n\n"

        f"✅ رتبه کیفیت: {qa_rank}\n\n"

        f"💧 حجم مخزن:\n"
        f"{reservoir_volume} MCM\n\n"

        f"📚 منبع:\n"
        f"{source}"
    )

    return text


# =========================================================
# دکمه‌های سدها
# =========================================================

def dam_buttons():

    buttons = []

    for index, dam in enumerate(DAMS, 1):

        name = dam_name(dam)

        lat = dam_lat(dam)
        lon = dam_lon(dam)

        # ---------------------------------------------
        # دکمه مشاهده همان سد روی Google Maps
        # ---------------------------------------------

        if lat not in (
            None,
            ""
        ) and lon not in (
            None,
            ""
        ):

            maps_url = (
                "https://www.google.com/maps/search/"
                f"?api=1&query={lat},{lon}"
            )

            buttons.append([

                InlineKeyboardButton(
                    f"📍 {name} — مشاهده روی نقشه",
                    url=maps_url
                )

            ])

        else:

            buttons.append([

                InlineKeyboardButton(
                    f"🏗 {name}",
                    callback_data=f"dam:{dam_id(dam)}"
                )

            ])

    # ---------------------------------------------
    # برگشت
    # ---------------------------------------------

    buttons.append([

        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data="back_start"
        )

    ])

    return buttons


# =========================================================
# نمایش فهرست سدها
# =========================================================

async def show_dams(query):

    if not DAMS:

        await query.edit_message_text(

            "⚠️ اطلاعات سدها پیدا نشد.\n\n"
            f"فایل مورد انتظار:\n{DAMS_FILE}",

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

    text = (
        "🏗 **بندها و سدهای افغانستان**\n\n"
        f"تعداد سدهای ثبت‌شده: {len(DAMS)}\n\n"
        "━━━━━━━━━━━━━━\n\n"
    )

    # فقط خلاصه؛ اطلاعات کامل با انتخاب سد
    for index, dam in enumerate(DAMS, 1):

        name = dam_name(dam)

        province = clean_value(
            dam.get("province")
        )

        district = clean_value(
            dam.get("district")
        )

        text += (
            f"🔢 {index}. **{name}**\n"
            f"🇦🇫 ولایت: {province}\n"
            f"🏘 ولسوالی: {district}\n\n"
        )

    text += (
        "━━━━━━━━━━━━━━\n"
        "📍 برای مشاهده هر سد روی نقشه، "
        "دکمه مربوط به همان سد را انتخاب کن."
    )

    await query.edit_message_text(

        text,

        reply_markup=InlineKeyboardMarkup(
            dam_buttons()
        ),

        parse_mode="Markdown"
    )


# =========================================================
# نمایش اطلاعات یک سد
# =========================================================

async def show_single_dam(
    query,
    dam
):

    if not dam:

        await query.answer(
            "سد پیدا نشد.",
            show_alert=True
        )

        return

    # پیدا کردن شماره سد
    number = 1

    for index, item in enumerate(
        DAMS,
        1
    ):

        if dam_id(item) == dam_id(dam):

            number = index
            break

    text = dam_text(
        dam,
        number
    )

    buttons = []

    lat = dam_lat(dam)
    lon = dam_lon(dam)

    # ---------------------------------------------
    # Google Maps
    # ---------------------------------------------

    if lat not in (
        None,
        ""
    ) and lon not in (
        None,
        ""
    ):

        maps_url = (
            "https://www.google.com/maps/search/"
            f"?api=1&query={lat},{lon}"
        )

        buttons.append([

            InlineKeyboardButton(
                f"📍 مشاهده {dam_name(dam)} روی نقشه",
                url=maps_url
            )

        ])

    # ---------------------------------------------
    # بازگشت به فهرست سدها
    # ---------------------------------------------

    buttons.append([

        InlineKeyboardButton(
            "🔙 برگشت به فهرست سدها",
            callback_data="dams"
        )

    ])

    # ---------------------------------------------
    # بازگشت به Start
    # ---------------------------------------------

    buttons.append([

        InlineKeyboardButton(
            "🏠 منوی اصلی",
            callback_data="back_start"
        )

    ])

    await query.edit_message_text(

        text,

        reply_markup=InlineKeyboardMarkup(
            buttons
        )
    )


# =========================================================
# جستجوی سدها
# =========================================================

def search_dams(query):

    query = query.lower().strip()

    results = []

    for dam in DAMS:

        # نام سد را هم جداگانه وارد جستجو می‌کنیم
        name = dam_name(dam)

        text = " ".join(
            str(value)
            for value in dam.values()
        )

        text = (
            name
            + " "
            + text
        ).lower()

        if query in text:

            results.append(dam)

    return results


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

    # مختصات
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

    # جستجوی مرکز ولسوالی
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

        reply_markup=InlineKeyboardMarkup(
            buttons
        )
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

    # =====================================================
    # ولایت‌ها
    # =====================================================

    if data == "geo_provinces":

        await show_provinces(
            query
        )

        return

    # =====================================================
    # انتخاب ولایت
    # =====================================================

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

    # =====================================================
    # انتخاب ولسوالی
    # =====================================================

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

    # =====================================================
    # انتخاب یک سد
    # =====================================================

    if data.startswith("dam:"):

        selected_id = data.split(
            ":",
            1
        )[1]

        selected_dam = None

        for dam in DAMS:

            if dam_id(dam) == selected_id:

                selected_dam = dam
                break

        await show_single_dam(
            query,
            selected_dam
        )

        return

    # =====================================================
    # بخش سدها
    # =====================================================

    if data == "dams":

        await show_dams(
            query
        )

        return

    # =====================================================
    # بازگشت به Start
    # =====================================================

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

    # =====================================================
    # مخزن‌ها
    # =====================================================

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
# جستجوی متنی
# =========================================================

async def search(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.message.text.strip()

    if not query:

        return

    query_lower = query.lower()

    # =====================================================
    # جستجوی سد
    # =====================================================

    dam_queries = [
        "بند",
        "سد",
        "dam"
    ]

    is_dam_search = any(

        word in query_lower

        for word in dam_queries

    )

    if is_dam_search:

        results = search_dams(
            query
        )

        if query_lower in [
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

        for index, dam in enumerate(
            results[:20],
            1
        ):

            name = dam_name(dam)

            province = clean_value(
                dam.get("province")
            )

            district = clean_value(
                dam.get("district")
            )

            message += (

                f"🔢 {index}. {name}\n"
                f"🇦🇫 ولایت: {province}\n"
                f"🏘 ولسوالی: {district}\n\n"

            )

            lat = dam_lat(dam)
            lon = dam_lon(dam)

            if lat not in (
                None,
                ""
            ) and lon not in (
                None,
                ""
            ):

                maps_url = (
                    "https://www.google.com/maps/search/"
                    f"?api=1&query={lat},{lon}"
                )

                buttons.append([

                    InlineKeyboardButton(
                        f"📍 {name} — مشاهده روی نقشه",
                        url=maps_url
                    )

                ])

        await update.message.reply_text(

            message[:4000],

            reply_markup=(

                InlineKeyboardMarkup(
                    buttons
                )

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

    print("=" * 60)
    print("🇦🇫 Afghanistan Knowledge Bot")
    print("✅ ربات در حال اجرا است...")
    print(f"🏗 تعداد سدهای بارگذاری‌شده: {len(DAMS)}")
    print("=" * 60)

    app.run_polling()


# =========================================================
# Main
# =========================================================

if __name__ == "__main__":

    main()
