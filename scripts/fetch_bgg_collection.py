import argparse
import json
import requests
import xml.etree.ElementTree as ET
import time
import sys

BGG_API_COLLECTION = "https://boardgamegeek.com/xmlapi2/collection"
BGG_API_THING = "https://boardgamegeek.com/xmlapi2/thing"
HEADERS_BASE = {"User-Agent": "Antropophag-GitHubAction/1.0"}

def fetch_collection_ready(username, api_key=None, subtype="boardgame", stats=1, delay=15, retries=20):
    headers = HEADERS_BASE.copy()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    params = {"username": username, "subtype": subtype, "stats": stats}

    for attempt in range(retries):
        print(f"➡️  Fetching collection (attempt {attempt+1}/{retries})...")
        try:
            response = requests.get(BGG_API_COLLECTION, params=params, headers=headers, timeout=30)
            print(f"   ↳ {response.url} → {response.status_code}")

            if response.status_code == 401:
                print("❌ Ошибка 401: Профиль недоступен или API key неверный.")
                sys.exit(1)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            totalitems = int(root.attrib.get("totalitems", 0))

            if totalitems > 0:
                print(f"✅ Найдено {totalitems} игр.")
                return root

            print(f"⚠ Коллекция пуста, повтор через {delay} секунд...")
            time.sleep(delay)

        except requests.RequestException as e:
            print(f"⚠ Ошибка сети: {e}")
            time.sleep(delay)

    print("❌ Коллекция так и не загрузилась после всех попыток.")
    sys.exit(1)

def fetch_game_stats_batch(ids, api_key=None):
    stats = {}
    batch_size = 20
    headers = HEADERS_BASE.copy()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i+batch_size]
        ids_str = ",".join(batch_ids)
        print(f"➡️  Fetching stats for games {i+1}-{i+len(batch_ids)} / {len(ids)}...")

        try:
            response = requests.get(BGG_API_THING, params={"id": ids_str, "stats": 1}, headers=headers, timeout=30)
            print(f"   ↳ {response.url} → {response.status_code}")

            if response.status_code == 401:
                print("❌ Ошибка 401 при запросе статистики. Проверь API key.")
                continue

            response.raise_for_status()

        except requests.RequestException as e:
            print(f"⚠ Ошибка при загрузке статистики: {e}")
            time.sleep(5)
            continue

        root = ET.fromstring(response.content)
        for item in root.findall("item"):
            game_id = item.attrib["id"]

            avgweight_node = item.find("statistics/ratings/averageweight")
            avgweight = float(avgweight_node.attrib.get("value")) if avgweight_node is not None else None

            overallrank = None
            for rank in item.findall("statistics/ratings/ranks/rank"):
                if rank.attrib.get("name") == "boardgame":
                    value = rank.attrib.get("value")
                    overallrank = int(value) if value and value.isdigit() else None
                    break

            stats[game_id] = {
                "averageweight": avgweight,
                "overallrank": overallrank
            }

        time.sleep(5)
    return stats

def parse_collection(root, api_key=None):
    data = {"own": [], "wishlist": [], "preordered": []}
    ids_to_fetch = []

    for item in root.findall("item"):
        status = item.find("status")
        if status is None:
            continue
        if status.attrib.get("own") == "1":
            category = "own"
        elif status.attrib.get("wishlist") == "1":
            category = "wishlist"
        elif status.attrib.get("preordered") == "1":
            category = "preordered"
        else:
            continue

        stats = item.find("stats")
        if stats is not None:
            minplayers = int(stats.attrib.get("minplayers", 0))
            maxplayers = int(stats.attrib.get("maxplayers", 0))
            playingtime = int(stats.attrib.get("playingtime", 0))
            rating_node = stats.find("rating/average")
            average = float(rating_node.attrib.get("value", 0)) if rating_node is not None else 0.0
        else:
            minplayers = maxplayers = playingtime = 0
            average = 0.0

        image_node = item.find("image")
        image = image_node.text if image_node is not None else ""

        thumbnail_node = item.find("thumbnail")
        thumbnail = thumbnail_node.text if thumbnail_node is not None else ""

        objectid = item.attrib.get("objectid", "")
        game = {
            "id": objectid,
            "name": item.find("name").text if item.find("name") is not None else "",
            "minplayers": minplayers,
            "maxplayers": maxplayers,
            "playingtime": playingtime,
            "image": image,
            "thumbnail": thumbnail,
            "average": average,
            "averageweight": None,
            "overallrank": None,
            "url": f"https://boardgamegeek.com/boardgame/{objectid}"
        }

        data[category].append(game)
        ids_to_fetch.append(objectid)

    # Получаем weight и rank
    stats_data = fetch_game_stats_batch(ids_to_fetch, api_key)
    for category in data:
        for game in data[category]:
            game_stats = stats_data.get(game["id"], {})
            game["averageweight"] = game_stats.get("averageweight")
            game["overallrank"] = game_stats.get("overallrank")

    return data

def main():
    parser = argparse.ArgumentParser(description="Fetch BGG collection")
    parser.add_argument("--username", required=True, help="BGG username")
    parser.add_argument("--out", required=True, help="Output JSON file path")
    parser.add_argument("--apikey", required=False, help="BGG API key (after approval)")
    args = parser.parse_args()

    if not args.apikey:
        print("⚠ No API key provided. You may encounter 401 errors on private or new collections.")

    print(f"🎲 Fetching BGG collection for user: {args.username}")
    root = fetch_collection_ready(args.username, api_key=args.apikey)
    collection = parse_collection(root, api_key=args.apikey)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(collection, f, ensure_ascii=False, indent=2)

    print(f"✅ Collection saved to {args.out}")

if __name__ == "__main__":
    main()
