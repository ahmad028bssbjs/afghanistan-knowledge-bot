import os
import json
import logging
from urllib.parse import quote
from threading import Thread

from flask import Flask

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
# Render Keep Alive
# =========================================================

web_app = Flask(__name__)


@web_app.route("/")
def home():
    return "🇦🇫 Afghanistan Knowledge Bot is alive!"


@web_app.route("/health")
def health():
    return "OK"


def run_web():

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    web_app.run(
        host="0.0.0.0",
        port=port
    )


def keep_alive():

    thread = Thread(
        target=run_web,
        daemon=True
    )

    thread.start()


# =========================================================
# جغرافیای افغانستان
# =========================================================

GEO = AfghanistanGeography()


# =========================================================
# فایل سدها
# =========================================================

DAMS_FILE = (
    "data/dams/"
    "geodar_afghanistan_complete.json"
)


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

        dams = data.get(
            "dams",
            []
        )

        print("=" * 60)
        print("✅ اطلاعات سدها بارگذاری شد")
        print(f"📁 فایل: {DAMS_FILE}")
        print(f"🏗 تعداد سدها: {len(dams)}")
        print("=" * 60)

        return dams

    except Exception as e:

        print("❌ خطا در خواندن فایل سدها:")
        print(e)

        return []


DAMS = load_dams()


# =========================================================
# نرمال‌سازی متن برای تطبیق ولایت و ولسوالی
# =========================================================

def normalize_text(value):

    if value is None:
        return ""

    value = str(value).strip().lower()

    replacements = {
        "ي": "ی",
        "ى": "ی",
        "ك": "ک",
        "ۀ": "ه",
        "ة": "ه",
        "‌": "",
        "\u200c": "",
        "-": " ",
        "_": " ",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    # حذف فاصله‌های اضافی
    value = " ".join(value.split())

    return value


# =========================================================
# تبدیل نام ولایت به شکل‌های قابل تطبیق
# =========================================================

PROVINCE_ALIASES = {

    "kabul": "کابل",
    "kabūl": "کابل",

    "ghazni": "غزنی",
    "ghaznī": "غزنی",

    "helmand": "هلمند",

    "nangarhar": "ننگرهار",

    "kandahar": "قندهار",
    "kandahār": "قندهار",

    "herat": "هرات",

    "kapisa": "کاپیسا",
    "kapīsā": "کاپیسا",

    "maidan wardak": "میدان وردک",
    "maidān wardak": "میدان وردک",

    "badakhshan": "بدخشان",

    "daikundi": "دایکندی",
    "daykundi": "دایکندی",

    "paktika": "پکتیکا",
    "paktīkā": "پکتیکا",

    "uruzgan": "ارزگان",
    "ūrūzgān": "ارزگان",

    "faryab": "فاریاب",

    "logar": "لوگر",

    "baghlan": "بغلان",

    "nimroz": "نیمروز",
    "nimrōz": "نیمروز",
}


def canonical_province(value):

    normalized = normalize_text(value)

    if normalized in PROVINCE_ALIASES:

        return normalize_text(
            PROVINCE_ALIASES[normalized]
        )

    return normalized


# =========================================================
# پیدا کردن سدهای یک ولایت
# =========================================================

def get_dams_by_province(
    province_name
):

    target = canonical_province(
        province_name
    )

    results = []

    for dam in DAMS:

        dam_province = canonical_province(
            dam.get("province")
        )

        if dam_province == target:

            results.append(dam)

    return results


# =========================================================
# پیدا کردن سدهای یک ولسوالی
# =========================================================

def get_dams_by_district(
    province_name,
    district_name
):

    target_province = canonical_province(
        province_name
    )

    target_district = normalize_text(
        district_name
    )

    results = []

    for dam in DAMS:

        dam_province = canonical_province(
            dam.get("province")
        )

        dam_district = normalize_text(
            dam.get("district")
        )

        if (
            dam_province == target_province
            and dam_district == target_district
        ):

            results.append(dam)

    return results


# =========================================================
# جستجوی سدها
# =========================================================

def search_dams(query):

    query_normalized = normalize_text(
        query
    )

    results = []

    for dam in DAMS:

        text = " ".join(
            str(value)
            for value in dam.values()
        )

        if query_normalized in normalize_text(
            text
        ):

            results.append(dam)

    return results


# =========================================================
# تبدیل مقدار خالی
# =========================================================

def clean_value(
    value,
    default="ثبت نشده"
):

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
# نام سد
# =========================================================

def get_dam_name(dam):

    return clean_value(
        dam.get("dam_name"),
        "سد بدون نام"
    )


# =========================================================
# اطلاعات کامل یک سد
# =========================================================

def dam_text(
    dam,
    number=None
):

    geodar_id = clean_value(
        dam.get("geodar_id")
    )

    dam_name = get_dam_name(
        dam
    )

    name_en = clean_value(
        dam.get("name_en")
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
        dam.get(
            "distance_to_province_center_km"
        )
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
        dam.get(
            "reservoir_volume_mcm_v11"
        )
    )

    status = clean_value(
        dam.get("status")
    )

    height = clean_value(
        dam.get("height_m")
    )

    storage = clean_value(
        dam.get("storage_capacity_mcm")
    )

    power = clean_value(
        dam.get("power_capacity_mw")
    )

    irrigation = clean_value(
        dam.get("irrigation_area_ha")
    )

    dam_type = clean_value(
        dam.get("type")
    )

    source = clean_value(
        dam.get("source")
    )

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

    text = ""

    if number is not None:

        text += (
            f"🔢 **سد شماره {number}**\n\n"
        )

    text += (
        f"🏗 **{dam_name}**\n"
    )

    if name_en != "ثبت نشده":

        text += (
            f"🇬🇧 {name_en}\n"
        )

    text += "\n"

    text += (
        f"🆔 GeoDAR ID: {geodar_id}\n\n"
    )

    text += (
        "📍 **موقعیت**\n"
        f"🇦🇫 ولایت: {province}\n"
        f"🏘 ولسوالی: {district}\n"
        f"🏙 مرکز ولایت: {province_center}\n"
        f"📏 فاصله تا مرکز ولایت: "
        f"{distance} km\n\n"
    )

    text += (
        "🌐 **مختصات**\n"
        f"عرض جغرافیایی: {lat}\n"
        f"طول جغرافیایی: {lon}\n\n"
    )

    text += (
        "📊 **وضعیت و مشخصات فنی**\n"
        f"🔹 وضعیت: {status}\n"
        f"🔹 نوع: {dam_type}\n"
        f"🔹 ارتفاع: {height} m\n"
        f"🔹 ظرفیت مخزن: {storage} MCM\n"
        f"🔹 ظرفیت برق: {power} MW\n"
        f"🔹 ساحه آبیاری: {irrigation} ha\n\n"
    )

    text += (
        "🗄 **اطلاعات پایگاه داده**\n"
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

    if reservoir != "ثبت نشده":

        text += (
            "💧 **حجم مخزن GeoDAR**\n"
            f"{reservoir} MCM\n\n"
        )

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
            "🏗 **نوع و سازه**\n"
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

    if source != "ثبت نشده":

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

    dam_name = get_dam_name(
        dam
    )

    lat = dam.get("latitude")
    lon = dam.get("longitude")

    if lat is not None and lon is not None:

        maps_url = (
            "https://www.google.com/maps/search/"
            "?api=1&query="
            f"{lat},{lon}"
        )

        buttons.append([

            InlineKeyboardButton(
                f"📍 نقشه {dam_name}",
                url=maps_url
            )

        ])

    return buttons


# =========================================================
# ساخت دکمه‌های فهرست سدها
# =========================================================

def dam_list_buttons(
    dams,
    offset=0
):

    buttons = []

    for local_index, dam in enumerate(
        dams,
        0
    ):

        try:

            real_index = DAMS.index(
                dam
            )

        except ValueError:

            continue

        name = get_dam_name(
            dam
        )

        buttons.append([

            InlineKeyboardButton(
                f"📖 {name}",
                callback_data=(
                    f"dam:{real_index}"
                )
            )

        ])

        lat = dam.get("latitude")
        lon = dam.get("longitude")

        if (
            lat is not None
            and lon is not None
        ):

            buttons.append([

                InlineKeyboardButton(
                    f"📍 نقشه {name}",
                    url=(
                        "https://www.google.com/maps/search/"
                        "?api=1&query="
                        f"{lat},{lon}"
                    )
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

async def show_provinces(
    query
):

    provinces = GEO.get_provinces()

    buttons = []

    row = []

    for province in provinces:

        row.append(

            InlineKeyboardButton(
                province["name_fa"],
                callback_data=(
                    f"province:"
                    f"{province['id']}"
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

        reply_markup=InlineKeyboardMarkup(
            buttons
        ),

        parse_mode="Markdown"
    )


# =========================================================
# نمایش ولسوالی‌ها + سدهای ولایت
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

    province_fa = province.get(
        "name_fa",
        ""
    )

    province_en = province.get(
        "name_en",
        ""
    )

    province_dams = get_dams_by_province(
        province_fa
    )

    # اگر تطبیق فارسی پیدا نکرد،
    # نام انگلیسی را امتحان می‌کنیم
    if not province_dams:

        province_dams = get_dams_by_province(
            province_en
        )

    buttons = []

    # -----------------------------------------------------
    # ولسوالی‌ها
    # -----------------------------------------------------

    row = []

    for district in districts:

        row.append(

            InlineKeyboardButton(

                district[
                    "district_name_fa"
                ],

                callback_data=(
                    f"district:"
                    f"{district['district_id']}"
                )

            )

        )

        if len(row) == 2:

            buttons.append(row)

            row = []

    if row:
        buttons.append(row)

    # -----------------------------------------------------
    # سدهای ولایت
    # -----------------------------------------------------

    if province_dams:

        buttons.append([

            InlineKeyboardButton(
                f"🏗 سدهای {province_fa} "
                f"({len(province_dams)})",
                callback_data=(
                    f"province_dams:"
                    f"{province_id}"
                )
            )

        ])

    message = (

        f"🇦🇫 **ولایت {province_fa}**\n\n"

        f"🏘 تعداد ولسوالی‌ها: "
        f"{len(districts)}\n"

        f"🏗 تعداد سدها: "
        f"{len(province_dams)}\n\n"

        "یک ولسوالی را انتخاب کن:"
    )

    buttons.append([

        InlineKeyboardButton(
            "🔙 برگشت به ولایت‌ها",
            callback_data="geo_provinces"
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
# نمایش سدهای یک ولایت
# =========================================================

async def show_province_dams(
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

    province_fa = province.get(
        "name_fa",
        ""
    )

    province_en = province.get(
        "name_en",
        ""
    )

    dams = get_dams_by_province(
        province_fa
    )

    if not dams:

        dams = get_dams_by_province(
            province_en
        )

    message = (

        f"🏗 **سدهای ولایت "
        f"{province_fa}**\n\n"

        f"تعداد سدهای ثبت‌شده: "
        f"{len(dams)}\n\n"

        "━━━━━━━━━━━━━━━━━━\n\n"
    )

    if not dams:

        message += (
            "⚠️ برای این ولایت "
            "سد ثبت‌شده‌ای پیدا نشد."
        )

    buttons = dam_list_buttons(
        dams
    )

    buttons.append([

        InlineKeyboardButton(
            "🔙 برگشت به ولایت",
            callback_data=(
                f"province:{province_id}"
            )
        )

    ])

    await query.edit_message_text(

        message[:4000],

        reply_markup=InlineKeyboardMarkup(
            buttons
        ),

        parse_mode="Markdown"
    )


# =========================================================
# نمایش اطلاعات ولسوالی + سدهای آن
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

    district_name_fa = district.get(
        "district_name_fa",
        ""
    )

    district_name_en = district.get(
        "district_name_en",
        ""
    )

    province_fa = district.get(
        "province_fa",
        ""
    )

    province_id = district.get(
        "province_id"
    )

    district_dams = get_dams_by_district(
        province_fa,
        district_name_fa
    )

    # اگر تطبیق فارسی پیدا نشد،
    # نام انگلیسی را امتحان می‌کنیم
    if not district_dams:

        province_en = district.get(
            "province_en",
            ""
        )

        district_dams = get_dams_by_district(
            province_en,
            district_name_en
        )

    text = (

        f"📍 **{district_name_fa}**\n\n"

        f"🏛 ولایت: "
        f"{province_fa}\n\n"

        f"🇬🇧 نام انگلیسی: "
        f"{district_name_en}\n\n"

        f"🆔 شناسه ولسوالی: "
        f"{district_id}\n\n"

        f"📌 مرکز ولسوالی:\n"
        f"عرض: {clean_value(lat)}\n"
        f"طول: {clean_value(lon)}\n\n"

        f"🗺 مرز جغرافیایی:\n"
        f"{boundary_name}\n\n"

        f"🔗 Boundary ID:\n"
        f"{boundary_id}\n\n"

        f"🏗 **سدهای این ولسوالی: "
        f"{len(district_dams)}**\n"
    )

    buttons = []

    # -----------------------------------------------------
    # نقشه مرکز ولسوالی
    # -----------------------------------------------------

    if (
        lat is not None
        and lon is not None
    ):

        maps_url = (
            "https://www.google.com/maps/search/"
            "?api=1&query="
            f"{lat},{lon}"
        )

        buttons.append([

            InlineKeyboardButton(
                "📍 مختصات جغرافیایی",
                url=maps_url
            )

        ])

    # -----------------------------------------------------
    # جستجوی مرکز ولسوالی
    # -----------------------------------------------------

    place_query = (

        f"{district_name_en}, "
        f"{district.get('province_en', '')}, "
        "Afghanistan"
    )

    center_url = (
        "https://www.google.com/maps/search/"
        "?api=1&query="
        f"{quote(place_query)}"
    )

    buttons.append([

        InlineKeyboardButton(
            "🏙️ جستجوی مرکز ولسوالی",
            url=center_url
        )

    ])

    # -----------------------------------------------------
    # دکمه سدهای ولسوالی
    # -----------------------------------------------------

    if district_dams:

        buttons.append([

            InlineKeyboardButton(
                f"🏗 نمایش سدها "
                f"({len(district_dams)})",
                callback_data=(
                    f"district_dams:"
                    f"{district_id}"
                )
            )

        ])

    else:

        text += (
            "\n⚠️ برای این ولسوالی "
            "سد ثبت‌شده‌ای پیدا نشد."
        )

    # -----------------------------------------------------
    # بازگشت
    # -----------------------------------------------------

    buttons.append([

        InlineKeyboardButton(
            "🔙 برگشت به ولسوالی‌ها",
            callback_data=(
                f"province:"
                f"{province_id}"
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

        text[:4000],

        reply_markup=InlineKeyboardMarkup(
            buttons
        ),

        parse_mode="Markdown"
    )


# =========================================================
# نمایش سدهای یک ولسوالی
# =========================================================

async def show_district_dams(
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

    district_name_fa = district.get(
        "district_name_fa",
        ""
    )

    district_name_en = district.get(
        "district_name_en",
        ""
    )

    province_fa = district.get(
        "province_fa",
        ""
    )

    province_en = district.get(
        "province_en",
        ""
    )

    province_id = district.get(
        "province_id"
    )

    dams = get_dams_by_district(
        province_fa,
        district_name_fa
    )

    if not dams:

        dams = get_dams_by_district(
            province_en,
            district_name_en
        )

    message = (

        f"🏗 **سدهای ولسوالی "
        f"{district_name_fa}**\n\n"

        f"🇦🇫 ولایت: {province_fa}\n"

        f"🏗 تعداد سدها: "
        f"{len(dams)}\n\n"

        "━━━━━━━━━━━━━━━━━━\n\n"
    )

    if not dams:

        message += (
            "⚠️ هیچ سدی برای این ولسوالی "
            "ثبت نشده است."
        )

    buttons = dam_list_buttons(
        dams
    )

    buttons.append([

        InlineKeyboardButton(
            "🔙 برگشت به ولسوالی",
            callback_data=(
                f"district:{district_id}"
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

        message[:4000],

        reply_markup=InlineKeyboardMarkup(
            buttons
        ),

        parse_mode="Markdown"
    )


# =========================================================
# نمایش تمام سدها
# =========================================================

async def show_dams(
    query
):

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

    message = (

        "🏗 **بندها و سدهای افغانستان**\n\n"

        f"تعداد سدهای ثبت‌شده: "
        f"{len(DAMS)}\n\n"

        "━━━━━━━━━━━━━━━━━━\n\n"
    )

    buttons = []

    for index, dam in enumerate(
        DAMS,
        1
    ):

        name = get_dam_name(
            dam
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
                callback_data=(
                    f"dam:{index - 1}"
                )
            )

        ])

        lat = dam.get("latitude")
        lon = dam.get("longitude")

        if (
            lat is not None
            and lon is not None
        ):

            buttons.append([

                InlineKeyboardButton(
                    f"📍 نقشه {name}",
                    url=(
                        "https://www.google.com/maps/search/"
                        "?api=1&query="
                        f"{lat},{lon}"
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

        message[:4000],

        reply_markup=InlineKeyboardMarkup(
            buttons
        ),

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

        index = int(
            dam_index
        )

    except ValueError:

        await query.answer(
            "شناسه سد نامعتبر است.",
            show_alert=True
        )

        return

    if (
        index < 0
        or index >= len(DAMS)
    ):

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

    buttons = dam_buttons(
        dam
    )

    navigation = []

    if index > 0:

        navigation.append(

            InlineKeyboardButton(
                "⬅️ سد قبلی",
                callback_data=(
                    f"dam:{index - 1}"
                )
            )

        )

    if (
        index
        < len(DAMS) - 1
    ):

        navigation.append(

            InlineKeyboardButton(
                "سد بعدی ➡️",
                callback_data=(
                    f"dam:{index + 1}"
                )
            )

        )

    if navigation:

        buttons.append(
            navigation
        )

    # -----------------------------------------------------
    # برگشت هوشمند به جغرافیا
    # -----------------------------------------------------

    province = dam.get(
        "province"
    )

    district = dam.get(
        "district"
    )

    # فعلاً دکمه بازگشت عمومی
    buttons.append([

        InlineKeyboardButton(
            "🔙 فهرست سدها",
            callback_data="dams"
        )

    ])

    buttons.append([

        InlineKeyboardButton(
            "🏠 منوی اصلی",
            callback_data="back_start"
        )

    ])

    await query.edit_message_text(

        text[:4000],

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
    # جغرافیا
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
    # سدهای ولایت
    # -----------------------------------------------------

    if data.startswith(
        "province_dams:"
    ):

        province_id = data.split(
            ":",
            1
        )[1]

        await show_province_dams(
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
    # سدهای ولسوالی
    # -----------------------------------------------------

    if data.startswith(
        "district_dams:"
    ):

        district_id = data.split(
            ":",
            1
        )[1]

        await show_district_dams(
            query,
            district_id
        )

        return

    # -----------------------------------------------------
    # فهرست تمام سدها
    # -----------------------------------------------------

    if data == "dams":

        await show_dams(
            query
        )

        return

    # -----------------------------------------------------
    # اطلاعات یک سد
    # -----------------------------------------------------

    if data.startswith(
        "dam:"
    ):

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
    # منوی اصلی
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

    query_lower = normalize_text(
        user_query
    )

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

    # =====================================================
    # جستجوی سد
    # =====================================================

    if is_dam_search:

        results = search_dams(
            user_query
        )

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

            f"🏗 **نتایج سدها برای "
            f"«{user_query}»**\n\n"
        )

        buttons = []

        for dam in results[:20]:

            name = get_dam_name(
                dam
            )

            province = clean_value(
                dam.get("province")
            )

            district = clean_value(
                dam.get("district")
            )

            message += (

                f"🏗 **{name}**\n"
                f"🇦🇫 ولایت: {province}\n"
                f"🏘 ولسوالی: {district}\n\n"
            )

            try:

                real_index = DAMS.index(
                    dam
                )

            except ValueError:

                continue

            buttons.append([

                InlineKeyboardButton(
                    f"📖 اطلاعات {name}",
                    callback_data=(
                        f"dam:{real_index}"
                    )
                )

            ])

            lat = dam.get("latitude")
            lon = dam.get("longitude")

            if (
                lat is not None
                and lon is not None
            ):

                maps_url = (

                    "https://www.google.com/maps/search/"
                    "?api=1&query="
                    f"{lat},{lon}"

                )

                buttons.append([

                    InlineKeyboardButton(
                        f"📍 نقشه {name}",
                        url=maps_url
                    )

                ])

        await update.message.reply_text(

            message[:4000],

            reply_markup=InlineKeyboardMarkup(
                buttons
            ),

            parse_mode="Markdown"
        )

        return

    # =====================================================
    # جستجوی عمومی
    # =====================================================

    results = search_documents(
        user_query
    )

    if not results:

        await update.message.reply_text(

            f"🔎 برای «{user_query}» "
            "چیزی پیدا نشد."

        )

        return

    message = (

        f"🔎 **نتایج برای "
        f"«{user_query}»**\n\n"
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
        f"🏗 تعداد سدهای بارگذاری‌شده: "
        f"{len(DAMS)}"
    )

    print("=" * 60)

    # -----------------------------------------------------
    # Render Web Server
    # -----------------------------------------------------

    keep_alive()

    print(
        "🌐 Render Keep-Alive فعال شد."
    )

    # -----------------------------------------------------
    # Telegram Bot
    # -----------------------------------------------------

    app = (

        Application
        .builder()
        .token(BOT_TOKEN)
        .build()

    )

    # -----------------------------------------------------
    # Commands
    # -----------------------------------------------------

    app.add_handler(

        CommandHandler(
            "start",
            start
        )

    )

    # -----------------------------------------------------
    # Callback buttons
    # -----------------------------------------------------

    app.add_handler(

        CallbackQueryHandler(
            button_handler
        )

    )

    # -----------------------------------------------------
    # Text search
    # -----------------------------------------------------

    app.add_handler(

        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            search
        )

    )

    print(
        "🤖 Telegram polling شروع شد..."
    )

    app.run_polling()


# =========================================================
# Main
# =========================================================

if __name__ == "__main__":

    main()
