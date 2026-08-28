# =========================================================
# dam_details.py
# اطلاعات و مشخصات سدهای افغانستان
# =========================================================

import json
import math
import unicodedata
from pathlib import Path


# =========================================================
# تنظیمات
# =========================================================

PROVINCE_CENTERS_FILE = (
    Path(__file__).parent
    / "data"
    / "provinces"
    / "province_centers.json"
)


# =========================================================
# تبدیل مقدار خالی
# =========================================================

def clean_value(value, default="ثبت نشده"):
    if value is None:
        return default

    if isinstance(value, (list, dict)):
        if not value:
            return default
        return str(value)

    value = str(value).strip()

    if value in (
        "",
        "-999",
        "-999.0",
        "-999.00",
        "None",
        "none",
        "null",
        "NULL",
        "NaN",
        "nan",
    ):
        return default

    return value


# =========================================================
# نام فارسی سد
# =========================================================

def get_dam_name_fa(dam):

    if not isinstance(dam, dict):
        return "سد بدون نام"

    name = (
        dam.get("name_fa")
        or dam.get("dam_name_fa")
        or dam.get("name")
        or dam.get("dam_name")
    )

    return clean_value(
        name,
        "سد بدون نام"
    )


# =========================================================
# نام انگلیسی سد
# =========================================================

def get_dam_name_en(dam):

    if not isinstance(dam, dict):
        return ""

    name = (
        dam.get("name_en")
        or dam.get("dam_name_en")
        or dam.get("english_name")
    )

    value = clean_value(
        name,
        ""
    )

    if value == "ثبت نشده":
        return ""

    return value


# =========================================================
# استخراج مختصات
# =========================================================

def get_coordinates(dam):

    if not isinstance(dam, dict):
        return None, None

    latitude = (
        dam.get("latitude")
        if dam.get("latitude") is not None
        else dam.get("lat")
    )

    if latitude is None:
        latitude = (
            dam.get("Latitude")
            or dam.get("LAT")
        )

    longitude = (
        dam.get("longitude")
        if dam.get("longitude") is not None
        else dam.get("lon")
    )

    if longitude is None:
        longitude = (
            dam.get("lng")
            or dam.get("Longitude")
            or dam.get("LON")
            or dam.get("LONG")
        )

    # -----------------------------------------------------
    # coordinates
    # -----------------------------------------------------

    if (
        (latitude is None or longitude is None)
        and dam.get("coordinates") is not None
    ):

        coordinates = dam.get(
            "coordinates"
        )

        if isinstance(
            coordinates,
            (list, tuple)
        ):

            if len(coordinates) >= 2:

                # GeoJSON:
                # [longitude, latitude]

                longitude = coordinates[0]
                latitude = coordinates[1]

        elif isinstance(
            coordinates,
            dict
        ):

            latitude = (
                coordinates.get("latitude")
                or coordinates.get("lat")
                or latitude
            )

            longitude = (
                coordinates.get("longitude")
                or coordinates.get("lon")
                or coordinates.get("lng")
                or longitude
            )

    # -----------------------------------------------------
    # تبدیل به float
    # -----------------------------------------------------

    try:

        if latitude is not None:
            latitude = float(latitude)

    except (
        ValueError,
        TypeError
    ):

        latitude = None

    try:

        if longitude is not None:
            longitude = float(longitude)

    except (
        ValueError,
        TypeError
    ):

        longitude = None

    # -----------------------------------------------------
    # بررسی محدوده
    # -----------------------------------------------------

    if latitude is not None:

        if latitude < -90 or latitude > 90:
            latitude = None

    if longitude is not None:

        if longitude < -180 or longitude > 180:
            longitude = None

    return latitude, longitude


# =========================================================
# وضعیت سد
# =========================================================

def get_status_fa(status):

    status = clean_value(
        status
    )

    statuses = {

        "active":
            "فعال",

        "under_construction":
            "در حال ساخت",

        "proposed":
            "پیشنهادی",

        "active_partially":
            "فعال به‌صورت جزئی",

        "inactive":
            "غیرفعال",

        "planned":
            "برنامه‌ریزی‌شده",

        "completed":
            "تکمیل‌شده",

        "unknown":
            "نامشخص"
    }

    return statuses.get(
        status,
        status
    )


# =========================================================
# نرمال‌سازی نام ولایت
# =========================================================

def normalize_province_name(name):

    if name is None:
        return ""

    name = str(name).strip()

    if not name:
        return ""

    # -----------------------------------------------------
    # نام‌های فارسی
    # -----------------------------------------------------

    persian_names = {

        "کابل": "Kabul",
        "قندهار": "Kandahar",
        "هرات": "Herat",
        "ننگرهار": "Nangarhar",
        "بدخشان": "Badakhshan",
        "تخار": "Takhar",
        "بغلان": "Baghlan",
        "فاریاب": "Faryab",
        "غزنی": "Ghazni",
        "پروان": "Parwan",
        "کاپیسا": "Kapisa",
        "لوگر": "Logar",
        "میدان وردک": "Wardak",
        "میدان‌وردک": "Wardak",
        "وردک": "Wardak",
        "هلمند": "Helmand",
        "زابل": "Zabul",
        "فراه": "Farah",
        "سرپل": "Sar-e Pul",
        "سمنگان": "Samangan",
        "نیمروز": "Nimroz",
        "پکتیا": "Paktia",
        "پنجشیر": "Panjshir",
        "بادغیس": "Badghis",
        "بدغیس": "Badghis",
        "کنر": "Kunar",
        "بامیان": "Bamyan",
        "خوست": "Khost",
        "نورستان": "Nuristan",
        "غور": "Ghor",
        "ارزگان": "Uruzgan",
        "لغمان": "Laghman",
        "پکتیکا": "Paktika",
        "دایکندی": "Daykundi",
        "کندز": "Kunduz",
        "بلخ": "Balkh",
        "جوزجان": "Jowzjan",
    }

    if name in persian_names:
        return persian_names[name]

    # -----------------------------------------------------
    # نرمال‌سازی Unicode
    # -----------------------------------------------------

    normalized = unicodedata.normalize(
        "NFKD",
        name
    )

    normalized = "".join(
        char
        for char in normalized
        if not unicodedata.combining(char)
    )

    normalized = (
        normalized
        .replace("’", "'")
        .replace("‘", "'")
        .replace("–", "-")
        .replace("—", "-")
    )

    normalized = " ".join(
        normalized.split()
    )

    # -----------------------------------------------------
    # یکسان‌سازی نام‌های انگلیسی
    # -----------------------------------------------------

    english_names = {

        "Kabul": "Kabul",
        "Kandahar": "Kandahar",
        "Herat": "Herat",
        "Nangarhar": "Nangarhar",
        "Badakhshan": "Badakhshan",
        "Takhar": "Takhar",
        "Baghlan": "Baghlan",
        "Faryab": "Faryab",
        "Ghazni": "Ghazni",
        "Parwan": "Parwan",
        "Kapisa": "Kapisa",
        "Logar": "Logar",
        "Wardak": "Wardak",
        "Helmand": "Helmand",
        "Zabul": "Zabul",
        "Farah": "Farah",
        "Sar-e Pul": "Sar-e Pul",
        "Sar e Pul": "Sar-e Pul",
        "Samangan": "Samangan",
        "Nimroz": "Nimroz",
        "Paktia": "Paktia",
        "Panjshir": "Panjshir",
        "Badghis": "Badghis",
        "Kunar": "Kunar",
        "Bamyan": "Bamyan",
        "Khost": "Khost",
        "Nuristan": "Nuristan",
        "Ghor": "Ghor",
        "Uruzgan": "Uruzgan",
        "Laghman": "Laghman",
        "Paktika": "Paktika",
        "Daykundi": "Daykundi",
        "Kunduz": "Kunduz",
        "Balkh": "Balkh",
        "Jowzjan": "Jowzjan",
    }

    return english_names.get(
        normalized,
        normalized
    )


# =========================================================
# نام فارسی مراکز ولایت
# =========================================================

PROVINCE_CENTER_FA = {

    "Kabul": "کابل",
    "Kandahar": "قندهار",
    "Balkh": "مزار شریف",
    "Herat": "هرات",
    "Nangarhar": "جلال‌آباد",
    "Kunduz": "قندوز",
    "Baghlan": "پلخمری",
    "Faryab": "میمنه",
    "Jowzjan": "شبرغان",
    "Helmand": "لشکرگاه",
    "Takhar": "تالقان",
    "Ghazni": "غزنی",
    "Parwan": "چاریکار",
    "Badakhshan": "فیض‌آباد",
    "Zabul": "قلات",
    "Farah": "فراه",
    "Sar-e Pul": "سرپل",
    "Samangan": "ایبک",
    "Nimroz": "زرنج",
    "Paktia": "گردیز",
    "Panjshir": "بازارک",
    "Badghis": "قلعه نو",
    "Kunar": "اسعدآباد",
    "Bamyan": "بامیان",
    "Khost": "خوست",
    "Nuristan": "پارون",
    "Ghor": "فیروزکوه",
    "Uruzgan": "ترینکوت",
    "Logar": "پل علم",
    "Laghman": "مهترلام",
    "Wardak": "میدان‌شهر",
    "Kapisa": "محمود راقی",
    "Paktika": "شرنه",
    "Daykundi": "نیلی",
}


# =========================================================
# بارگذاری مراکز ولایات
# =========================================================

def load_province_centers():

    if not PROVINCE_CENTERS_FILE.exists():

        print(
            "⚠️ فایل مراکز ولایات پیدا نشد:"
        )

        print(
            PROVINCE_CENTERS_FILE
        )

        return []

    try:

        with open(
            PROVINCE_CENTERS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

    except Exception as e:

        print(
            "⚠️ خطا در خواندن "
            "province_centers.json:"
        )

        print(e)

        return []

    # -----------------------------------------------------
    # پشتیبانی از چند ساختار JSON
    # -----------------------------------------------------

    if isinstance(data, dict):

        if isinstance(
            data.get("province_centers"),
            list
        ):

            data = data[
                "province_centers"
            ]

        elif isinstance(
            data.get("centers"),
            list
        ):

            data = data[
                "centers"
            ]

        else:

            data = []

    if not isinstance(data, list):

        print(
            "⚠️ ساختار province_centers.json معتبر نیست."
        )

        return []

    centers = []

    for item in data:

        if not isinstance(
            item,
            dict
        ):
            continue

        province = (
            item.get("province_en")
            or item.get("province")
            or item.get("name_en")
        )

        if not province:
            continue

        latitude = (
            item.get("latitude")
            if item.get("latitude") is not None
            else item.get("lat")
        )

        longitude = (
            item.get("longitude")
            if item.get("longitude") is not None
            else item.get("lon")
        )

        try:

            latitude = float(
                latitude
            )

            longitude = float(
                longitude
            )

        except (
            ValueError,
            TypeError
        ):

            continue

        if (
            latitude < -90
            or latitude > 90
        ):
            continue

        if (
            longitude < -180
            or longitude > 180
        ):
            continue

        centers.append({

            "province_en": str(
                province
            ).strip(),

            "name_en": (
                item.get("name_en")
                or ""
            ),

            "name_fa": (
                item.get("name_fa")
                or ""
            ),

            "latitude": latitude,

            "longitude": longitude,
        })

    print(
        f"✅ مراکز ولایت‌ها بارگذاری شد: "
        f"{len(centers)} ولایت"
    )

    return centers


# =========================================================
# بارگذاری
# =========================================================

PROVINCE_CENTERS = load_province_centers()


# =========================================================
# پیدا کردن مرکز ولایت
# =========================================================

def get_province_center(province):

    if not province:
        return None

    province = str(
        province
    ).strip()

    normalized = normalize_province_name(
        province
    )

    # -----------------------------------------------------
    # جستجوی دقیق با نام نرمال‌شده
    # -----------------------------------------------------

    for center in PROVINCE_CENTERS:

        center_province = str(
            center.get(
                "province_en",
                ""
            )
        ).strip()

        center_normalized = (
            normalize_province_name(
                center_province
            )
        )

        if center_normalized == normalized:

            return center

    # -----------------------------------------------------
    # جستجوی مستقیم
    # -----------------------------------------------------

    for center in PROVINCE_CENTERS:

        center_province = str(
            center.get(
                "province_en",
                ""
            )
        ).strip()

        if (
            center_province.lower()
            == province.lower()
        ):

            return center

    return None


# =========================================================
# محاسبه فاصله Haversine
# =========================================================

def calculate_distance_km(
    lat1,
    lon1,
    lat2,
    lon2
):

    try:

        lat1 = float(lat1)
        lon1 = float(lon1)
        lat2 = float(lat2)
        lon2 = float(lon2)

    except (
        ValueError,
        TypeError
    ):

        return None

    if (
        lat1 < -90
        or lat1 > 90
        or lat2 < -90
        or lat2 > 90
    ):
        return None

    if (
        lon1 < -180
        or lon1 > 180
        or lon2 < -180
        or lon2 > 180
    ):
        return None

    earth_radius_km = 6371.0088

    lat1_rad = math.radians(
        lat1
    )

    lat2_rad = math.radians(
        lat2
    )

    delta_lat = math.radians(
        lat2 - lat1
    )

    delta_lon = math.radians(
        lon2 - lon1
    )

    a = (
        math.sin(
            delta_lat / 2
        ) ** 2
        +
        math.cos(lat1_rad)
        *
        math.cos(lat2_rad)
        *
        math.sin(
            delta_lon / 2
        ) ** 2
    )

    # جلوگیری از خطای احتمالی اعشاری
    a = min(
        1.0,
        max(0.0, a)
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return (
        earth_radius_km * c
    )


# =========================================================
# دریافت مرکز ولایت و فاصله
# =========================================================

def get_province_center_info(
    province,
    latitude,
    longitude
):

    center = get_province_center(
        province
    )

    if center is None:

        # اگر مرکز در JSON نبود،
        # حداقل نام فارسی مرکز را بده

        key = normalize_province_name(
            province
        )

        fallback_name = (
            PROVINCE_CENTER_FA.get(
                key
            )
        )

        return (
            fallback_name
            or "ثبت نشده",
            None
        )

    # -----------------------------------------------------
    # مختصات مرکز
    # -----------------------------------------------------

    center_lat = center.get(
        "latitude"
    )

    center_lon = center.get(
        "longitude"
    )

    # -----------------------------------------------------
    # محاسبه فاصله
    # -----------------------------------------------------

    distance = calculate_distance_km(
        latitude,
        longitude,
        center_lat,
        center_lon
    )

    if distance is not None:

        distance = round(
            distance,
            1
        )

    # -----------------------------------------------------
    # نام مرکز
    # -----------------------------------------------------

    key = normalize_province_name(
        province
    )

    center_name = (
        center.get("name_fa")
        or PROVINCE_CENTER_FA.get(key)
        or center.get("name_en")
        or "ثبت نشده"
    )

    return (
        clean_value(
            center_name
        ),
        distance
    )


# =========================================================
# ساخت متن کامل اطلاعات سد
# =========================================================

def build_dam_text(
    dam,
    number=None
):

    if not isinstance(
        dam,
        dict
    ):

        return (
            "❌ اطلاعات سد نامعتبر است."
        )

    # -----------------------------------------------------
    # اطلاعات پایه
    # -----------------------------------------------------

    name_fa = get_dam_name_fa(
        dam
    )

    name_en = get_dam_name_en(
        dam
    )

    province = clean_value(
        dam.get("province")
    )

    district = clean_value(
        dam.get("district")
    )

    status = get_status_fa(
        dam.get("status")
    )

    # -----------------------------------------------------
    # شناسه‌ها
    # -----------------------------------------------------

    geodar_id = clean_value(
        dam.get("geodar_id")
        or dam.get("id_v11")
        or dam.get("geodar")
    )

    grand_id = clean_value(
        dam.get("grand_id")
        or dam.get("id_grd_v13")
        or dam.get("grand")
    )

    # -----------------------------------------------------
    # مختصات
    # -----------------------------------------------------

    latitude, longitude = (
        get_coordinates(dam)
    )

    lat = clean_value(
        latitude
    )

    lon = clean_value(
        longitude
    )

    # -----------------------------------------------------
    # مرکز ولایت و فاصله
    # -----------------------------------------------------

    (
        province_center,
        calculated_distance
    ) = get_province_center_info(
        province,
        latitude,
        longitude
    )

    if calculated_distance is not None:

        distance = (
            f"{calculated_distance:.1f}"
        )

    else:

        distance = "ثبت نشده"

    # -----------------------------------------------------
    # اطلاعات جغرافیایی
    # -----------------------------------------------------

    geo_method = clean_value(
        dam.get("geo_method")
        or dam.get("geo_mtd")
    )

    qa_rank = clean_value(
        dam.get("qa_rank")
    )

    source = clean_value(
        dam.get("source")
        or dam.get("val_src")
        or dam.get("har_src")
    )

    # -----------------------------------------------------
    # اطلاعات فنی
    # -----------------------------------------------------

    height = clean_value(
        dam.get("height_m")
        or dam.get("height")
    )

    storage = clean_value(
        dam.get(
            "storage_capacity_mcm"
        )
        or dam.get(
            "reservoir_volume_mcm_v11"
        )
        or dam.get(
            "rv_mcm_v11"
        )
        or dam.get(
            "storage_mcm"
        )
    )

    power = clean_value(
        dam.get(
            "power_capacity_mw"
        )
        or dam.get(
            "power_mw"
        )
        or dam.get(
            "capacity_mw"
        )
    )

    irrigation = clean_value(
        dam.get(
            "irrigation_area_ha"
        )
        or dam.get(
            "irrigation_ha"
        )
    )

    # -----------------------------------------------------
    # توضیحات
    # -----------------------------------------------------

    description = clean_value(
        dam.get("description"),
        ""
    )

    location_description = clean_value(
        dam.get(
            "location_description"
        ),
        ""
    )

    type_description = clean_value(
        dam.get(
            "type_description"
        ),
        ""
    )

    history_description = clean_value(
        dam.get(
            "history_description"
        ),
        ""
    )

    purpose_description = clean_value(
        dam.get(
            "purpose_description"
        ),
        ""
    )

    importance_description = clean_value(
        dam.get(
            "importance_description"
        ),
        ""
    )

    power_description = clean_value(
        dam.get(
            "power_description"
        ),
        ""
    )

    # =====================================================
    # ساخت متن
    # =====================================================

    text = ""

    # -----------------------------------------------------
    # شماره
    # -----------------------------------------------------

    if number is not None:

        text += (
            f"🔢 <b>سد شماره {number}</b>\n\n"
        )

    # -----------------------------------------------------
    # نام
    # -----------------------------------------------------

    text += (
        f"🏗 <b>{name_fa}</b>\n"
    )

    if name_en:

        text += (
            f"🇬🇧 {name_en}\n"
        )

    text += "\n"

    # -----------------------------------------------------
    # موقعیت
    # -----------------------------------------------------

    text += (
        "📍 <b>موقعیت</b>\n"
        f"🇦🇫 ولایت: {province}\n"
        f"🏘 ولسوالی: {district}\n"
        f"🏙 مرکز ولایت: "
        f"{province_center}\n"
        f"📏 فاصله تا مرکز ولایت: "
        f"{distance} km\n"
        f"📌 وضعیت: {status}\n\n"
    )

    # -----------------------------------------------------
    # مختصات
    # -----------------------------------------------------

    text += (
        "🌐 <b>مختصات جغرافیایی</b>\n"
        f"عرض جغرافیایی: {lat}\n"
        f"طول جغرافیایی: {lon}\n\n"
    )

    # -----------------------------------------------------
    # اطلاعات فنی
    # -----------------------------------------------------

    text += (
        "🏗 <b>اطلاعات فنی</b>\n"
        f"📏 ارتفاع دیواره: "
        f"{height} متر\n"
        f"💧 ظرفیت ذخیره: "
        f"{storage} میلیون متر مکعب\n"
        f"⚡ ظرفیت برق: "
        f"{power} مگاوات\n"
        f"🌾 مساحت آبیاری: "
        f"{irrigation} هکتار\n\n"
    )

    # -----------------------------------------------------
    # شناسه پایگاه داده
    # -----------------------------------------------------

    text += (
        "🆔 <b>اطلاعات پایگاه داده</b>\n"
        f"GeoDAR ID: {geodar_id}\n"
        f"GRanD ID: {grand_id}\n\n"
    )

    # -----------------------------------------------------
    # روش تعیین موقعیت
    # -----------------------------------------------------

    text += (
        "🛰 <b>روش تعیین موقعیت</b>\n"
        f"{geo_method}\n\n"
    )

    # -----------------------------------------------------
    # کنترل کیفیت
    # -----------------------------------------------------

    text += (
        "✅ <b>رتبه کنترل کیفیت</b>\n"
        f"{qa_rank}\n\n"
    )

    # -----------------------------------------------------
    # توضیحات
    # -----------------------------------------------------

    if description:

        text += (
            "📖 <b>توضیحات</b>\n"
            f"{description}\n\n"
        )

    # -----------------------------------------------------
    # موقعیت و محل
    # -----------------------------------------------------

    if location_description:

        text += (
            "📍 <b>موقعیت و محل سد</b>\n"
            f"{location_description}\n\n"
        )

    # -----------------------------------------------------
    # نوع سد
    # -----------------------------------------------------

    if type_description:

        text += (
            "🏗 <b>نوع سد</b>\n"
            f"{type_description}\n\n"
        )

    # -----------------------------------------------------
    # تاریخچه
    # -----------------------------------------------------

    if history_description:

        text += (
            "📜 <b>تاریخچه و ساخت</b>\n"
            f"{history_description}\n\n"
        )

    # -----------------------------------------------------
    # کاربرد
    # -----------------------------------------------------

    if purpose_description:

        text += (
            "🎯 <b>کاربرد</b>\n"
            f"{purpose_description}\n\n"
        )

    # -----------------------------------------------------
    # اهمیت
    # -----------------------------------------------------

    if importance_description:

        text += (
            "⭐ <b>اهمیت</b>\n"
            f"{importance_description}\n\n"
        )

    # -----------------------------------------------------
    # برق
    # -----------------------------------------------------

    if power_description:

        text += (
            "⚡ <b>برق و ظرفیت تولید</b>\n"
            f"{power_description}\n\n"
        )

    # -----------------------------------------------------
    # منبع
    # -----------------------------------------------------

    text += (
        "📚 <b>منبع</b>\n"
        f"{source}"
    )

    return text
