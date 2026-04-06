"""Build global airport dataset from OpenFlights data.

Downloads and processes airport data into a clean JSON file.
Run: python -m app.airports.build_data

Source: https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat
Format: CSV — ID, Name, City, Country, IATA, ICAO, Lat, Lon, Alt, Timezone, DST, Tz, Type, Source
"""

import csv
import json
import io
from pathlib import Path

import httpx

OPENFLIGHTS_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat"
OUTPUT_PATH = Path(__file__).parent.parent.parent / "data" / "airports.json"

# Chinese city/country names for common airports
ZH_NAMES: dict[str, dict] = {
    # 台灣
    "TPE": {"city_zh": "台北", "country_zh": "台灣"}, "TSA": {"city_zh": "台北", "country_zh": "台灣"},
    "KHH": {"city_zh": "高雄", "country_zh": "台灣"}, "RMQ": {"city_zh": "台中", "country_zh": "台灣"},
    # 日本
    "NRT": {"city_zh": "東京", "country_zh": "日本"}, "HND": {"city_zh": "東京", "country_zh": "日本"},
    "KIX": {"city_zh": "大阪", "country_zh": "日本"}, "ITM": {"city_zh": "大阪", "country_zh": "日本"},
    "NGO": {"city_zh": "名古屋", "country_zh": "日本"}, "CTS": {"city_zh": "札幌", "country_zh": "日本"},
    "FUK": {"city_zh": "福岡", "country_zh": "日本"}, "OKA": {"city_zh": "沖繩", "country_zh": "日本"},
    # 韓國
    "ICN": {"city_zh": "首爾", "country_zh": "韓國"}, "GMP": {"city_zh": "首爾", "country_zh": "韓國"},
    "PUS": {"city_zh": "釜山", "country_zh": "韓國"},
    # 中國
    "PVG": {"city_zh": "上海", "country_zh": "中國"}, "SHA": {"city_zh": "上海", "country_zh": "中國"},
    "PEK": {"city_zh": "北京", "country_zh": "中國"}, "PKX": {"city_zh": "北京", "country_zh": "中國"},
    "CAN": {"city_zh": "廣州", "country_zh": "中國"}, "SZX": {"city_zh": "深圳", "country_zh": "中國"},
    "CTU": {"city_zh": "成都", "country_zh": "中國"}, "XIY": {"city_zh": "西安", "country_zh": "中國"},
    # 港澳
    "HKG": {"city_zh": "香港", "country_zh": "香港"}, "MFM": {"city_zh": "澳門", "country_zh": "澳門"},
    # 東南亞
    "BKK": {"city_zh": "曼谷", "country_zh": "泰國"}, "DMK": {"city_zh": "曼谷", "country_zh": "泰國"},
    "SIN": {"city_zh": "新加坡", "country_zh": "新加坡"},
    "KUL": {"city_zh": "吉隆坡", "country_zh": "馬來西亞"},
    "MNL": {"city_zh": "馬尼拉", "country_zh": "菲律賓"},
    "SGN": {"city_zh": "胡志明市", "country_zh": "越南"}, "HAN": {"city_zh": "河內", "country_zh": "越南"},
    "CGK": {"city_zh": "雅加達", "country_zh": "印尼"}, "DPS": {"city_zh": "峇里島", "country_zh": "印尼"},
    "RGN": {"city_zh": "仰光", "country_zh": "緬甸"}, "REP": {"city_zh": "暹粒", "country_zh": "柬埔寨"},
    "PNH": {"city_zh": "金邊", "country_zh": "柬埔寨"},
    # 歐洲
    "LHR": {"city_zh": "倫敦", "country_zh": "英國"}, "LGW": {"city_zh": "倫敦", "country_zh": "英國"},
    "CDG": {"city_zh": "巴黎", "country_zh": "法國"}, "ORY": {"city_zh": "巴黎", "country_zh": "法國"},
    "FRA": {"city_zh": "法蘭克福", "country_zh": "德國"}, "MUC": {"city_zh": "慕尼黑", "country_zh": "德國"},
    "AMS": {"city_zh": "阿姆斯特丹", "country_zh": "荷蘭"},
    "FCO": {"city_zh": "羅馬", "country_zh": "義大利"}, "MXP": {"city_zh": "米蘭", "country_zh": "義大利"},
    "MAD": {"city_zh": "馬德里", "country_zh": "西班牙"}, "BCN": {"city_zh": "巴塞隆納", "country_zh": "西班牙"},
    "VIE": {"city_zh": "維也納", "country_zh": "奧地利"}, "ZRH": {"city_zh": "蘇黎世", "country_zh": "瑞士"},
    "IST": {"city_zh": "伊斯坦堡", "country_zh": "土耳其"},
    "ATH": {"city_zh": "雅典", "country_zh": "希臘"}, "PRG": {"city_zh": "布拉格", "country_zh": "捷克"},
    "HEL": {"city_zh": "赫爾辛基", "country_zh": "芬蘭"},
    # 美洲
    "LAX": {"city_zh": "洛杉磯", "country_zh": "美國"}, "SFO": {"city_zh": "舊金山", "country_zh": "美國"},
    "JFK": {"city_zh": "紐約", "country_zh": "美國"}, "EWR": {"city_zh": "紐約", "country_zh": "美國"},
    "ORD": {"city_zh": "芝加哥", "country_zh": "美國"}, "SEA": {"city_zh": "西雅圖", "country_zh": "美國"},
    "YVR": {"city_zh": "溫哥華", "country_zh": "加拿大"}, "YYZ": {"city_zh": "多倫多", "country_zh": "加拿大"},
    # 大洋洲
    "SYD": {"city_zh": "雪梨", "country_zh": "澳洲"}, "MEL": {"city_zh": "墨爾本", "country_zh": "澳洲"},
    "AKL": {"city_zh": "奧克蘭", "country_zh": "紐西蘭"},
    # 中東
    "DXB": {"city_zh": "杜拜", "country_zh": "阿聯酋"}, "DOH": {"city_zh": "杜哈", "country_zh": "卡達"},
}

# Top 100 popular airports (higher search priority)
TOP_AIRPORTS = {
    "TPE", "NRT", "HND", "KIX", "ICN", "HKG", "PVG", "PEK", "CAN",
    "BKK", "SIN", "KUL", "MNL", "SGN", "CGK", "DPS",
    "LHR", "CDG", "FRA", "AMS", "FCO", "MAD", "BCN", "IST",
    "LAX", "SFO", "JFK", "ORD", "SEA", "YVR",
    "SYD", "MEL", "AKL", "DXB", "DOH",
    "KHH", "RMQ", "TSA", "CTS", "FUK", "OKA", "NGO",
    "GMP", "PUS", "MFM", "HAN", "DMK", "ITM",
}


def download_and_process() -> list[dict]:
    """Download OpenFlights data and process into clean format."""
    print("Downloading airport data from OpenFlights...")
    resp = httpx.get(OPENFLIGHTS_URL, timeout=30)
    resp.raise_for_status()

    airports = []
    reader = csv.reader(io.StringIO(resp.text))

    for row in reader:
        if len(row) < 14:
            continue

        iata = row[4].strip().strip('"')

        # Skip airports without IATA code or placeholder codes
        if not iata or iata == "\\N" or len(iata) != 3:
            continue

        name = row[1].strip().strip('"')
        city = row[2].strip().strip('"')
        country = row[3].strip().strip('"')

        zh = ZH_NAMES.get(iata, {})

        airport = {
            "iata": iata,
            "name": name,
            "city": city,
            "country": country,
            "city_zh": zh.get("city_zh", ""),
            "country_zh": zh.get("country_zh", ""),
            "lat": float(row[6]) if row[6] else 0,
            "lon": float(row[7]) if row[7] else 0,
            "tz": row[11].strip().strip('"') if len(row) > 11 else "",
            "popular": iata in TOP_AIRPORTS,
        }
        airports.append(airport)

    # Deduplicate by IATA code (keep first occurrence)
    seen = set()
    unique = []
    for a in airports:
        if a["iata"] not in seen:
            seen.add(a["iata"])
            unique.append(a)

    # Sort: popular first, then alphabetically
    unique.sort(key=lambda a: (not a["popular"], a["iata"]))

    print(f"Processed {len(unique)} airports ({sum(1 for a in unique if a['popular'])} popular)")
    return unique


def build():
    """Build and save airports.json."""
    airports = download_and_process()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(airports, f, ensure_ascii=False, separators=(",", ":"))

    size_kb = OUTPUT_PATH.stat().st_size / 1024
    print(f"Saved to {OUTPUT_PATH} ({size_kb:.0f} KB, {len(airports)} airports)")


if __name__ == "__main__":
    build()
