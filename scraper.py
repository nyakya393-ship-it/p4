import json
import re
import time
import hashlib

from urllib.parse import urljoin, quote

import requests

from bs4 import BeautifulSoup


WIKI_ROOT = "https://wikiwiki.jp/splatoon3mix/"

INKIPEDIA_ROOT = "https://splatoonwiki.org/"

INKIPEDIA_LIST = (
    "https://splatoonwiki.org/wiki/"
    "List_of_main_weapons_in_Splatoon_3"
)


CATEGORIES = {

    "シューター":
        "ブキ/シューター属",

    "ブラスター":
        "ブキ/ブラスター属",

    "ローラー":
        "ブキ/ローラー属",

    "フデ":
        "ブキ/フデ属",

    "チャージャー":
        "ブキ/チャージャー属",

    "スロッシャー":
        "ブキ/スロッシャー属",

    "スピナー":
        "ブキ/スピナー属",

    "マニューバー":
        "ブキ/マニューバー属",

    "シェルター":
        "ブキ/シェルター属",

    "ストリンガー":
        "ブキ/ストリンガー属",

    "ワイパー":
        "ブキ/ワイパー属"

}


session = requests.Session()

session.headers.update({

    "User-Agent":
        "Splatoon3-Weapon-Analyzer/1.0 "

        "(GitHub Actions)"

})


def get(url):

    response = session.get(
        url,
        timeout=30
    )

    response.raise_for_status()

    return response.text


def clean(text):

    return re.sub(
        r"\s+",
        " ",
        text or ""
    ).strip()


def normalize(text):

    return (

        clean(text)

        .replace("（","(")

        .replace("）",")")

        .replace("　","")

    )


def first_number(text):

    if not text:

        return None


    match = re.search(

        r"(?<!\d)"
        r"(\d+(?:\.\d+)?)",

        str(text).replace(",","")

    )


    if not match:

        return None


    number = float(
        match.group(1)
    )


    if number.is_integer():

        return int(number)

    return number


def range_numbers(text):

    if not text:

        return None, None


    match = re.search(

        r"(\d+(?:\.\d+)?)"
        r"\s*[～~\-]\s*"
        r"(\d+(?:\.\d+)?)",

        text

    )


    if match:

        return (

            float(match.group(1)),

            float(match.group(2))

        )


    number = first_number(text)

    return number, None


def rows_from_page(soup):

    rows = []


    for tr in soup.select("tr"):

        cells = [

            clean(
                cell.get_text(
                    " ",
                    strip=True
                )
            )

            for cell in tr.select(
                "th,td"
            )

        ]


        if len(cells) >= 2:

            rows.append(cells)


    return rows


def find_exact(rows, labels):

    labels = [

        normalize(label)

        for label in labels

    ]


    for row in rows:

        for index, cell in enumerate(row):

            current = normalize(cell)


            if current in labels:

                if index + 1 < len(row):

                    return row[index + 1]


                if len(row) >= 2:

                    return row[-1]


    return None


def find_contains(rows, labels):

    labels = [

        normalize(label)

        for label in labels

    ]


    for row in rows:

        for index, cell in enumerate(row):

            current = normalize(cell)


            if any(
                label in current
                for label in labels
            ):

                if index + 1 < len(row):

                    return row[index + 1]


                if len(row) >= 2:

                    return row[-1]


    return None


def get_page_title(soup, fallback):

    h1 = soup.select_one("h1")


    if not h1:

        return fallback


    title = clean(
        h1.get_text(
            " ",
            strip=True
        )
    )


    title = title.replace(

        " - Splatoon3 - "
        "スプラトゥーン3 攻略＆検証 Wiki*",

        ""

    )


    return title


def get_weapon_links(
    category_path
):

    url = urljoin(

        WIKI_ROOT,

        quote(
            category_path,
            safe="/"
        )

    )


    soup =
        BeautifulSoup(
            get(url),
            "lxml"
        )


    links = {}


    for a in soup.select(
        "a[href]"
    ):

        href =
            a.get("href","")

        text =
            clean(
                a.get_text(
                    " ",
                    strip=True
                )
            )


        if not text:

            continue


        if "/ブキ/" not in href:

            continue


        full =
            urljoin(
                WIKI_ROOT,
                href
            )


        excluded = [

            "属",

            "ブキ性能",

            "比較",

            "サブウェポン",

            "スペシャルウェポン"

        ]


        if any(
            item in full
            for item in excluded
        ):

            continue


        links[full] = text


    return links


def get_inkipedia_links():

    result = {}


    try:

        soup =
            BeautifulSoup(
                get(INKIPEDIA_LIST),
                "lxml"
            )


        for a in soup.select(
            "a[href]"
        ):

            href =
                a.get("href","")

            name =
                clean(
                    a.get_text(
                        " ",
                        strip=True
                    )
                )


            if not name:

                continue


            if "/wiki/" not in href:

                continue


            result[name] =
                urljoin(
                    INKIPEDIA_ROOT,
                    href
                )


    except Exception as error:

        print(
            "Inkipedia lookup failed:",
            error
        )


    return result


def parse_weapon(
    url,
    category
):

    soup =
        BeautifulSoup(
            get(url),
            "lxml"
        )


    rows =
        rows_from_page(
            soup
        )


    name =
        get_page_title(
            soup,
            url.rsplit("/",1)[-1]
        )


    sub =
        find_exact(
            rows,
            [
                "サブウェポン",
                "サブ"
            ]
        )


    special =
        find_exact(
            rows,
            [
                "スペシャルウェポン",
                "スペシャル"
            ]
        )


    special_points =
        first_number(
            find_contains(
                rows,
                [
                    "必要P",
                    "必要ポイント"
                ]
            )
        )


    direct_range =
        first_number(
            find_exact(
                rows,
                [
                    "有効射程（直撃）",
                    "有効射程(直撃)"
                ]
            )
        )


    blast_range =
        first_number(
            find_exact(
                rows,
                [
                    "ダメージ射程（爆風）",
                    "ダメージ射程(爆風)"
                ]
            )
        )


    normal_range =
        first_number(
            find_exact(
                rows,
                [
                    "有効射程"
                ]
            )
        )


    range_value = (

        direct_range

        if direct_range is not None

        else normal_range

    )


    maintain_range =
        first_number(
            find_exact(
                rows,
                [
                    "確定数維持射程"
                ]
            )
        )


    reticle_range =
        first_number(
            find_exact(
                rows,
                [
                    "レティクル反応距離"
                ]
            )
        )


    paint_range =
        first_number(
            find_exact(
                rows,
                [
                    "塗り射程"
                ]
            )
        )


    damage_text =
        find_exact(
            rows,
            [
                "ダメージ"
            ]
        )


    damage_max, damage_min =
        range_numbers(
            damage_text
        )


    direct_damage =
        first_number(
            find_exact(
                rows,
                [
                    "ダメージ（直撃）",
                    "ダメージ(直撃)"
                ]
            )
        )


    blast_damage =
        first_number(
            find_exact(
                rows,
                [
                    "ダメージ（爆風）",
                    "ダメージ(爆風)"
                ]
            )
        )


    if direct_damage is not None:

        if damage_max is None:

            damage_max =
                direct_damage

        if damage_min is None:

            damage_min =
                direct_damage


    kills =
        find_exact(
            rows,
            [
                "確定数"
            ]
        )


    fire_rate_text =
        find_exact(
            rows,
            [
                "連射フレーム"
            ]
        )


    fire_rate =
        first_number(
            fire_rate_text
        )


    shots_per_second =
        first_number(
            find_exact(
                rows,
                [
                    "秒間発射数"
                ]
            )
        )


    kill_time =
        first_number(
            find_contains(
                rows,
                [
                    "キルタイム"
                ]
            )
        )


    dps =
        first_number(
            find_contains(
                rows,
                [
                    "DPS"
                ]
            )
        )


    blast_radius =
        first_number(
            find_exact(
                rows,
                [
                    "爆風半径"
                ]
            )
        )


    start_frame = None

    end_frame = None


    if damage_text:

        frame_match =
            re.search(

                r"\((\d+)F"
                r"\s*[～~\-]\s*"
                r"(\d+)F\)",

                damage_text

            )


        if frame_match:

            start_frame =
                int(
                    frame_match.group(1)
                )

            end_frame =
                int(
                    frame_match.group(2)
                )


    weapon_id =
        hashlib.sha1(
            url.encode("utf-8")
        ).hexdigest()[:12]


    return {

        "id":
            weapon_id,

        "name":
            name,

        "category":
            category,

        "sub":
            sub,

        "special":
            special,

        "specialPoints":
            special_points,

        "range":
            range_value,

        "maintainRange":
            maintain_range,

        "reticleRange":
            reticle_range,

        "paintRange":
            paint_range,

        "damageMax":
            damage_max,

        "damageMin":
            damage_min,

        "damageStartFrame":
            start_frame,

        "damageEndFrame":
            end_frame,

        "kills":
            kills,

        "killTime":
            kill_time,

        "fireRate":
            fire_rate,

        "shotsPerSecond":
            shots_per_second,

        "dps":
            dps,

        "blastRange":
            blast_range,

        "blastRadius":
            blast_radius,

        "directDamage":
            direct_damage,

        "blastDamage":
            blast_damage,

        "wikiUrl":
            url

    }


def main():

    weapon_pages = {}


    for category, path in CATEGORIES.items():

        print(
            "取得カテゴリ:",
            category
        )


        links =
            get_weapon_links(
                path
            )


        for url in links:

            weapon_pages.setdefault(
                url,
                category
            )


    print(
        "発見したブキページ:",
        len(weapon_pages)
    )


    inki_links =
        get_inkipedia_links()


    weapons = []


    for index, (
        url,
        category
    ) in enumerate(
        sorted(
            weapon_pages.items()
        ),
        start=1
    ):

        try:

            weapon =
                parse_weapon(
                    url,
                    category
                )


            weapon[
                "inkipediaUrl"
            ] = inki_links.get(
                weapon["name"]
            )


            weapons.append(
                weapon
            )


            print(

                f"[{index}/"
                f"{len(weapon_pages)}]"
                f" {weapon['name']}"

            )


        except Exception as error:

            print(
                "取得失敗:",
                url,
                error
            )


        time.sleep(.08)


    weapons.sort(

        key=lambda weapon: (

            weapon["category"],
            weapon["name"]

        )

    )


    with open(
        "data/weapons.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(

            weapons,
            file,

            ensure_ascii=False,

            indent=2

        )


    print(
        "保存完了:",
        len(weapons),
        "件"
    )


if __name__ == "__main__":

    main()
