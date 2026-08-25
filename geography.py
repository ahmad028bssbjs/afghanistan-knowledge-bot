import json
from pathlib import Path


# =========================================================
# مسیرهای داده
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

CENTERS_FILE = (
    BASE_DIR
    / "data/district_centers/district_centers.json"
)

MAPPING_FILE = (
    BASE_DIR
    / "data/district_centers/district_boundary_mapping.json"
)


# =========================================================
# Afghanistan Geography
# =========================================================

class AfghanistanGeography:

    def __init__(self):

        self.centers = []
        self.mapping = []

        self.by_id = {}
        self.by_name = {}

        self._load()


    # =====================================================
    # بارگذاری داده‌ها
    # =====================================================

    def _load(self):

        # -----------------------------
        # مراکز ولسوالی‌ها
        # -----------------------------

        with open(
            CENTERS_FILE,
            encoding="utf-8"
        ) as f:

            data = json.load(f)

            self.centers = data["district_centers"]


        # -----------------------------
        # Mapping مرکز ←→ مرز
        # -----------------------------

        with open(
            MAPPING_FILE,
            encoding="utf-8"
        ) as f:

            data = json.load(f)

            self.mapping = data["mapping"]


        # =================================================
        # Index بر اساس ID
        # =================================================

        self.by_id = {
            x["district_id"]: x
            for x in self.mapping
        }


        # =================================================
        # Index بر اساس نام
        # =================================================

        for x in self.mapping:

            name_en = (
                x["district_name_en"]
                .lower()
                .strip()
            )

            name_fa = (
                x["district_name_fa"]
                .strip()
            )

            self.by_name.setdefault(
                name_en,
                []
            ).append(x)

            self.by_name.setdefault(
                name_fa,
                []
            ).append(x)


    # =====================================================
    # ولایت‌ها
    # =====================================================

    def get_provinces(self):

        provinces = {}

        for x in self.mapping:

            province_id = x["province_id"]

            if province_id not in provinces:

                provinces[province_id] = {

                    "id": province_id,

                    "name_fa": x["province_fa"],

                    "name_en": x["province_en"]
                }

        return list(provinces.values())


    # =====================================================
    # پیدا کردن ولایت
    # =====================================================

    def get_province(self, value):

        if value is None:
            return None

        value = str(value).lower().strip()

        for province in self.get_provinces():

            if (
                province["id"].lower() == value
                or
                province["name_fa"].lower() == value
                or
                province["name_en"].lower() == value
            ):

                return province

        return None


    # =====================================================
    # ولسوالی‌های یک ولایت
    # =====================================================

    def get_districts(self, province_id):

        return [

            x
            for x in self.mapping

            if x["province_id"] == province_id

        ]


    # =====================================================
    # ولسوالی‌های ولایت با ID یا نام
    # =====================================================

    def get_districts_by_province(self, province):

        province_data = self.get_province(
            province
        )

        if not province_data:

            return []

        return self.get_districts(
            province_data["id"]
        )


    # =====================================================
    # پیدا کردن ولسوالی با ID
    # =====================================================

    def get_district(self, district_id):

        return self.by_id.get(
            district_id
        )


    # =====================================================
    # جستجوی ولسوالی
    # =====================================================

    def search_district(self, name):

        if not name:
            return []

        name = (
            str(name)
            .lower()
            .strip()
        )

        return self.by_name.get(
            name,
            []
        )


    # =====================================================
    # جستجوی تقریبی ولسوالی
    # =====================================================

    def search_district_partial(self, query):

        if not query:
            return []

        query = (
            str(query)
            .lower()
            .strip()
        )

        results = []

        for district in self.mapping:

            name_en = (
                district["district_name_en"]
                .lower()
            )

            name_fa = (
                district["district_name_fa"]
                .lower()
            )

            if (
                query in name_en
                or
                query in name_fa
            ):

                results.append(district)

        return results


# =========================================================
# تست مستقیم
# =========================================================

if __name__ == "__main__":

    geo = AfghanistanGeography()


    # -----------------------------------------------------
    # آمار کلی
    # -----------------------------------------------------

    print(
        "ولایت‌ها:",
        len(geo.get_provinces())
    )

    print(
        "مرکزها:",
        len(geo.centers)
    )

    print(
        "Mapping:",
        len(geo.mapping)
    )


    # -----------------------------------------------------
    # نمونه ولایت‌ها
    # -----------------------------------------------------

    print(
        "\nنمونه ولایت‌ها:"
    )

    for province in geo.get_provinces()[:5]:

        print(
            province["id"],
            "=>",
            province["name_fa"],
            "/",
            province["name_en"]
        )


    # -----------------------------------------------------
    # تست ولایت بدخشان
    # -----------------------------------------------------

    province = geo.get_province(
        "بدخشان"
    )

    print(
        "\nولایت انتخاب‌شده:"
    )

    print(province)


    # -----------------------------------------------------
    # ولسوالی‌های بدخشان
    # -----------------------------------------------------

    districts = geo.get_districts_by_province(
        "بدخشان"
    )

    print(
        "\nتعداد ولسوالی‌های بدخشان:",
        len(districts)
    )


    print(
        "\nنمونه ولسوالی‌ها:"
    )

    for district in districts[:10]:

        print(
            district["district_id"],
            "=>",
            district["district_name_fa"],
            "/",
            district["district_name_en"],
            "| boundary:",
            district["boundary_name"]
        )


    # -----------------------------------------------------
    # تست ID
    # -----------------------------------------------------

    district = geo.get_district(
        "AF1705"
    )

    print(
        "\nتست AF1705:"
    )

    print(district)


    # -----------------------------------------------------
    # تست جستجوی نام
    # -----------------------------------------------------

    results = geo.search_district(
        "Khash"
    )

    print(
        "\nجستجوی Khash:"
    )

    for result in results:

        print(
            result["district_id"],
            result["district_name_en"],
            "=>",
            result["boundary_name"]
        )


    # -----------------------------------------------------
    # تست جستجوی تقریبی
    # -----------------------------------------------------

    results = geo.search_district_partial(
        "kha"
    )

    print(
        "\nجستجوی تقریبی kha:",
        len(results)
    )

    for result in results[:10]:

        print(
            result["district_name_en"]
        )
