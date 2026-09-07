import json
import re
import time
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


# =========================================================
# Settings
# =========================================================

WIKI_ROOT = "https://wikiwiki.jp/splatoon3mix/"
OUTPUT = Path("data/weapons.json")

CATEGORY_PAGES = {
    "シューター": "ブキ/シューター属",
    "ブラスター": "ブキ/ブラスター属",
    "ローラー": "ブキ/ローラー属",
    "フデ": "ブキ/フデ属",
    "チャージャー": "ブキ/チャージャー属",
    "スロッシャー": "ブキ/スロッシャー属",
    "スピナー": "ブキ/スピナー属",
    "マニューバー": "ブキ/マニューバー属",
    "シェルター": "ブキ/シェルター属",
    "ストリンガー": "ブキ/ストリンガー属",
    "ワイパー": "ブキ/ワイパー属",
}


# =========================================================
# HTTP session
# =========================================================

session = requests.Session()

session.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 "
            "(compatible; SplatoonWeaponAnalyzer/1.0; "
            "+https://github.com/)"
        ),
        "Accept-Language": "ja,en;q=0.8",
    }
)


# =========================================================
# Text helpers
# =========================================================

def clean(text):
    text = text or ""

    text = text.replace("\xa0", " ")

    text = re.sub(r"[\r\n\t]+", " ", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize(text):
    return (
        clean(text)
        .replace(" ", "")
        .replace("　", "")
        .lower()
    )


# =========================================================
# HTTP helpers
# =========================================================

def get(url, retries=3):
    last_error = None

    for attempt in range(retries):
        try:
            response = session.get(
                url,
                timeout=30,
            )

            response.raise_for_status()

            response.encoding = (
                response.apparent_encoding
                or response.encoding
            )

            return response.text

        except requests.RequestException as exc:
            last_error = exc

            time.sleep(
                1.5 * (attempt + 1)
            )

    raise RuntimeError(
        f"取得失敗: {url}\n{last_error}"
    )


def soup_from(url):
    html = get(url)

    return BeautifulSoup(
        html,
        "html.parser",
    )


# =========================================================
# URL helpers
# =========================================================

def absolute_url(href):
    return urljoin(
        WIKI_ROOT,
        href,
    )


def is_wiki_weapon_url(url):
    """
    WikiWikiの個別ブキページらしいURLだけを通す。
    """

    parsed = urlparse(url)

    if (
        parsed.netloc
        and parsed.netloc != "wikiwiki.jp"
    ):
        return False

    path = unquote(parsed.path)

    if not path.startswith(
        "/splatoon3mix/ブキ/"
    ):
        return False

    name = path.rsplit(
        "/",
        1,
    )[-1]

    if not name:
        return False

    excluded = {
        "ブキ",
        "ブキ性能",
        "シューター属",
        "ブラスター属",
        "ローラー属",
        "フデ属",
        "チャージャー属",
        "スロッシャー属",
        "スピナー属",
        "マニューバー属",
        "シェルター属",
        "ストリンガー属",
        "ワイパー属",
        "比較",
        "サブウェポン",
        "スペシャルウェポン",
    }

    if name in excluded:
        return False

    if "属" in name:
        return False

    return True


# =========================================================
# Weapon discovery
# =========================================================

def page_links(soup):
    result = set()

    for a in soup.select("a[href]"):

        href = a.get(
            "href",
            "",
        ).strip()

        if not href:
            continue

        if href.startswith("#"):
            continue

        if href.startswith("http"):
            url = href
        else:
            url = absolute_url(href)

        url = url.split(
            "#",
            1,
        )[0]

        if is_wiki_weapon_url(url):
            result.add(url)

    return result


def discover_weapon_urls():

    urls = {}

    for category, page in CATEGORY_PAGES.items():

        url = urljoin(
            WIKI_ROOT,
            page,
        )

        print(
            f"[category] {category}: {url}"
        )

        soup = soup_from(url)

        for weapon_url in page_links(soup):

            name = unquote(
                urlparse(
                    weapon_url
                ).path.rsplit(
                    "/",
                    1,
                )[-1]
            )

            urls[weapon_url] = {
                "name": name,
                "category": category,
            }

        time.sleep(0.25)

    print(
        f"[discover] {len(urls)} pages found"
    )

    return urls


# =========================================================
# Table parsing
# =========================================================

def extract_tables(soup):

    rows = []

    for table in soup.find_all("table"):

        for tr in table.find_all("tr"):

            cells = tr.find_all(
                ["th", "td"]
            )

            if len(cells) < 2:
                continue

            values = []

            for cell in cells:

                value = clean(
                    cell.get_text(
                        " ",
                        strip=True,
                    )
                )

                if value:
                    values.append(value)

            if len(values) >= 2:
                rows.append(values)

    return rows


def all_text(soup):
    return clean(
        soup.get_text(
            " ",
            strip=True,
        )
    )


# =========================================================
# Table value helpers
# =========================================================

def find_value(rows, labels):

    wanted = [
        normalize(label)
        for label in labels
    ]

    # First: exact / startswith match
    for row in rows:

        if not row:
            continue

        first = normalize(row[0])

        for label in wanted:

            if (
                first == label
                or first.startswith(label)
            ):

                if len(row) >= 2:
                    return clean(
                        " ".join(
                            row[1:]
                        )
                    )

    # Second: search inside whole row
    for row in rows:

        joined = normalize(
            " ".join(row)
        )

        for label in wanted:

            if label not in joined:
                continue

            for i, cell in enumerate(row):

                if label in normalize(cell):

                    if i + 1 < len(row):

                        return clean(
                            " ".join(
                                row[i + 1:]
                            )
                        )

    return ""


# =========================================================
# Number helpers
# =========================================================

def first_number(value):

    if not value:
        return None

    match = re.search(
        r"-?\d+(?:\.\d+)?",
        value.replace(",", ""),
    )

    if not match:
        return None

    try:
        return float(
            match.group(0)
        )

    except ValueError:
        return None


def number_range(value):

    if not value:
        return None, None

    nums = re.findall(
        r"-?\d+(?:\.\d+)?",
        value.replace(",", ""),
    )

    if not nums:
        return None, None

    values = [
        float(x)
        for x in nums
    ]

    if len(values) == 1:
        return (
            values[0],
            values[0],
        )

    return (
        max(
            values[0],
            values[1],
        ),
        min(
            values[0],
            values[1],
        ),
    )


def int_or_float(value):

    if value is None:
        return None

    if float(value).is_integer():
        return int(value)

    return round(
        float(value),
        4,
    )


# =========================================================
# Damage curve helper
# =========================================================

def extract_damage_curve(value):

    if not value:
        return []

    points = []

    # Wikiの表記に距離とダメージの対応が
    # 明示されている場合だけ簡易的に取得する。
    pattern = re.compile(
        r"(\d+(?:\.\d+)?)"
        r"\s*(?:ダメージ|damage)"
        r".*?"
        r"(\d+(?:\.\d+)?)",
        re.IGNORECASE,
    )

    for match in pattern.finditer(
        value
    ):

        points.append(
            {
                "distance": float(
                    match.group(1)
                ),
                "damage": float(
                    match.group(2)
                ),
            }
        )

    return points


# =========================================================
# Overview parsing
# =========================================================

def parse_overview(
    soup,
    rows,
):

    text = all_text(soup)

    sub = find_value(
        rows,
        [
            "サブウェポン",
            "サブ",
        ],
    )

    special = find_value(
        rows,
        [
            "スペシャルウェポン",
            "スペシャル",
        ],
    )

    points = find_value(
        rows,
        [
            "必要ポイント",
            "必要SP",
            "スペシャル必要ポイント",
        ],
    )

    weight = find_value(
        rows,
        [
            "重量",
            "weight",
        ],
    )

    # Fallback
    if not sub:

        match = re.search(
            r"サブ(?:ウェポン)?\s*[:：]\s*([^、,]+)",
            text,
        )

        if match:
            sub = clean(
                match.group(1)
            )

    if not special:

        match = re.search(
            r"スペシャル(?:ウェポン)?\s*[:：]\s*([^、,]+)",
            text,
        )

        if match:
            special = clean(
                match.group(1)
            )

    return (
        sub,
        special,
        points,
        weight,
    )


# =========================================================
# Individual weapon parser
# =========================================================

def parse_weapon(
    url,
    category_info,
):

    soup = soup_from(url)

    rows = extract_tables(
        soup
    )

    # -----------------------------------------------------
    # Name
    # -----------------------------------------------------

    title = ""

    if soup.title:
        title = clean(
            soup.title.get_text()
        )

    heading = ""

    page_heading = soup.find(
        ["h1", "h2"]
    )

    if page_heading:
        heading = clean(
            page_heading.get_text(
                " ",
                strip=True,
            )
        )

    name = category_info[
        "name"
    ]

    if heading:

        heading = re.sub(
            r"^ブキ[/／]",
            "",
            heading,
        )

        heading = re.sub(
            r"\s*[-|｜].*$",
            "",
            heading,
        )

        if 1 <= len(heading) <= 40:
            name = heading

    elif title:

        title_name = re.sub(
            r"\s*[-|｜].*$",
            "",
            title,
        )

        title_name = re.sub(
            r"^ブキ[/／]",
            "",
            title_name,
        )

        if 1 <= len(title_name) <= 40:
            name = title_name

    # -----------------------------------------------------
    # Overview
    # -----------------------------------------------------

    (
        sub,
        special,
        points_raw,
        weight,
    ) = parse_overview(
        soup,
        rows,
    )

    # -----------------------------------------------------
    # Performance
    # -----------------------------------------------------

    effective_raw = find_value(
        rows,
        [
            "有効射程",
            "射程",
        ],
    )

    paint_raw = find_value(
        rows,
        [
            "塗り射程",
        ],
    )

    damage_raw = find_value(
        rows,
        [
            "ダメージ",
        ],
    )

    kills_raw = find_value(
        rows,
        [
            "確定数",
        ],
    )

    killtime_raw = find_value(
        rows,
        [
            "キルタイム",
        ],
    )

    fire_frame_raw = find_value(
        rows,
        [
            "連射フレーム",
            "発射フレーム",
        ],
    )

    shots_raw = find_value(
        rows,
        [
            "秒間発射数",
        ],
    )

    dps_raw = find_value(
        rows,
        [
            "DPS",
        ],
    )

    spread_raw = find_value(
        rows,
        [
            "拡散",
        ],
    )

    jump_spread_raw = find_value(
        rows,
        [
            "ジャンプ中拡散",
        ],
    )

    reticle_raw = find_value(
        rows,
        [
            "レティクル反応距離",
        ],
    )

    blast_radius_raw = find_value(
        rows,
        [
            "爆風半径",
            "爆風範囲",
        ],
    )

    blast_damage_raw = find_value(
        rows,
        [
            "爆風ダメージ",
        ],
    )

    direct_damage_raw = find_value(
        rows,
        [
            "直撃ダメージ",
            "直接ダメージ",
        ],
    )

    damage_range_raw = find_value(
        rows,
        [
            "ダメージ射程",
            "爆風射程",
            "ダメージ範囲",
        ],
    )

    # -----------------------------------------------------
    # Numbers
    # -----------------------------------------------------

    effective_max, effective_min = number_range(
        effective_raw
    )

    paint_max, _ = number_range(
        paint_raw
    )

    damage_max, damage_min = number_range(
        damage_raw
    )

    blast_range_max, _ = number_range(
        damage_range_raw
    )

    blast_radius = first_number(
        blast_radius_raw
    )

    blast_damage = first_number(
        blast_damage_raw
    )

    direct_damage = first_number(
        direct_damage_raw
    )

    points_num = first_number(
        points_raw
    )

    killtime = first_number(
        killtime_raw
    )

    fire_frame = first_number(
        fire_frame_raw
    )

    shots_per_second = first_number(
        shots_raw
    )

    dps = first_number(
        dps_raw
    )

    spread = first_number(
        spread_raw
    )

    jump_spread = first_number(
        jump_spread_raw
    )

    reticle = first_number(
        reticle_raw
    )

    # -----------------------------------------------------
    # Blast range
    # -----------------------------------------------------

    blast_range = blast_range_max

    if (
        blast_range is None
        and blast_radius is not None
        and effective_max is not None
    ):

        blast_range = (
            effective_max
            + blast_radius
        )

    # -----------------------------------------------------
    # Fire rate
    # -----------------------------------------------------

    fire_rate = fire_frame

    if fire_rate is None:
        fire_rate = shots_per_second

    # -----------------------------------------------------
    # Direct damage
    # -----------------------------------------------------

    if (
        direct_damage is None
        and damage_max is not None
    ):

        direct_damage = damage_max

    # -----------------------------------------------------
    # ID
    # -----------------------------------------------------

    weapon_id = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "-",
        name,
    ).strip("-").lower()

    if not weapon_id:

        weapon_id = (
            "weapon-"
            + str(
                abs(
                    hash(url)
                )
            )
        )

    # -----------------------------------------------------
    # Final data
    # -----------------------------------------------------

    data = {

        "id": weapon_id,

        "name": name,

        "category": category_info[
            "category"
        ],

        "sub": sub or "不明",

        "special": special or "不明",

        "specialPoints": int_or_float(
            points_num
        ),

        "specialPointsRaw": (
            points_raw or ""
        ),

        "weight": (
            weight or ""
        ),

        "range": {

            "effective": int_or_float(
                effective_max
            ),

            "paint": int_or_float(
                paint_max
            ),

            "reticle": int_or_float(
                reticle
            ),

            "blast": int_or_float(
                blast_range
            ),
        },

        "damage": {

            "max": int_or_float(
                damage_max
            ),

            "min": int_or_float(
                damage_min
            ),

            "direct": int_or_float(
                direct_damage
            ),

            "blast": int_or_float(
                blast_damage
            ),
        },

        "kills": (
            kills_raw or ""
        ),

        "killTime": int_or_float(
            killtime
        ),

        "fireFrame": int_or_float(
            fire_frame
        ),

        "fireRate": int_or_float(
            fire_rate
        ),

        "fireRateRaw": (
            fire_frame_raw or ""
        ),

        "shotsPerSecond": int_or_float(
            shots_per_second
        ),

        "dps": int_or_float(
            dps
        ),

        "spread": int_or_float(
            spread
        ),

        "jumpSpread": int_or_float(
            jump_spread
        ),

        "blast": {

            "range": int_or_float(
                blast_range
            ),

            "radius": int_or_float(
                blast_radius
            ),
        },

        "damageRaw": (
            damage_raw or ""
        ),

        "damageCurve": (
            extract_damage_curve(
                damage_raw
            )
        ),

        "source": url,

        "sourceName": (
            "WikiWiki - Splatoon3 Wiki"
        ),
    }

    return data


# =========================================================
# Duplicate removal
# =========================================================

def deduplicate(items):

    result = []

    seen = set()

    for item in items:

        key = (
            normalize(
                item.get(
                    "name",
                    "",
                )
            ),
            item.get(
                "category",
                "",
            ),
        )

        if key in seen:
            continue

        seen.add(key)

        result.append(item)

    return result


# =========================================================
# Validation
# =========================================================

def validate(items):

    # Splatoon 3には多数のブキが存在するため、
    # 取得数が異常に少ない場合は既存JSONを守る。
    if len(items) < 50:

        raise RuntimeError(
            "取得したブキ数が少なすぎます: "
            f"{len(items)}件。\n"
            "WikiWiki側の構造変更や通信失敗の可能性があるため、"
            "weapons.jsonを上書きしません。"
        )

    required = [
        "id",
        "name",
        "category",
        "range",
        "damage",
        "source",
    ]

    for item in items:

        missing = [
            key
            for key in required
            if key not in item
        ]

        if missing:

            raise RuntimeError(
                "必須フィールド不足: "
                f"{item.get('name')} / {missing}"
            )


# =========================================================
# Main
# =========================================================

def main():

    print(
        "=== Splatoon 3 Weapon Scraper ==="
    )

    print(
        f"Source: {WIKI_ROOT}"
    )

    # -----------------------------------------------------
    # Discover
    # -----------------------------------------------------

    discovered = (
        discover_weapon_urls()
    )

    if not discovered:

        raise RuntimeError(
            "ブキページを1件も発見できませんでした。"
        )

    # -----------------------------------------------------
    # Parse
    # -----------------------------------------------------

    weapons = []

    failures = []

    total = len(
        discovered
    )

    for index, (
        url,
        info,
    ) in enumerate(
        sorted(
            discovered.items()
        ),
        start=1,
    ):

        print(
            f"[{index}/{total}] "
            f"{info['name']}"
        )

        try:

            weapon = parse_weapon(
                url,
                info,
            )

            weapons.append(
                weapon
            )

        except Exception as exc:

            failures.append(
                {
                    "url": url,
                    "name": info[
                        "name"
                    ],
                    "error": str(exc),
                }
            )

            print(
                f"  -> ERROR: {exc}"
            )

        time.sleep(0.2)

    # -----------------------------------------------------
    # Cleanup
    # -----------------------------------------------------

    weapons = deduplicate(
        weapons
    )

    weapons.sort(
        key=lambda x: (
            x.get(
                "category",
                "",
            ),
            x.get(
                "name",
                "",
            ),
        )
    )

    print(
        "[result] "
        f"success={len(weapons)} "
        f"failure={len(failures)}"
    )

    # -----------------------------------------------------
    # Validation
    # -----------------------------------------------------

    validate(
        weapons
    )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT.open(
        "w",
        encoding="utf-8",
    ) as fp:

        json.dump(
            weapons,
            fp,
            ensure_ascii=False,
            indent=2,
        )

        fp.write(
            "\n"
        )

    print(
        f"[saved] {OUTPUT} "
        f"({len(weapons)} weapons)"
    )

    # -----------------------------------------------------
    # Failed pages
    # -----------------------------------------------------

    if failures:

        print(
            "[warning] "
            "Some pages failed:"
        )

        for failure in failures[:20]:

            print(
                f"  - "
                f"{failure['name']}: "
                f"{failure['error']}"
            )


# =========================================================
# Entry point
# =========================================================

if __name__ == "__main__":
    main()
