import argparse
import json
import requests
import xml.etree.ElementTree as ET
import time

BGG_API_COLLECTION = "https://boardgamegeek.com/xmlapi2/collection"
BGG_API_THING = "https://boardgamegeek.com/xmlapi2/thing"

def fetch_collection_ready(username, subtype="boardgame", stats=1, delay=15, retries=20):
    params = {"username": username, "subtype": subtype, "stats": stats}
    for attempt in range(retries):
        response = requests.get(BGG_API_COLLECTION, params=params)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        totalitems = int(root.attrib.get("totalitems", 0))
        if totalitems > 0:
            return root
        print(f"⚠ Collection empty, retry {attempt+1}/{retries} in {delay}s...")
        time.sleep(delay)
    print("❌ Collection still empty after retries")
    return root

def fetch_game_stats_batch(ids):
    stats = {}
    batch_size = 20
    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i+batch_size]
        ids_str = ",".join(batch_ids)
        try:
            response = requests.get(BGG_API_THING, params={"id": ids_str, "stats": 1})
            response.raise_for_status()
        except requests.HTTPError as e:
            print(f"⚠ Error fetching batch {ids_str}: {e}")
            time.sleep(5)
            continue

        root = ET.fromstring(response.content)
        for item in root.findall("item"):
            game_id = item.attrib["id"]

            # --- Average weight
            avgweight_node = item.find("statistics/ratings/averageweight")
            avgweight = float(avgweight_node.attrib.get("value")) if avgweight_node is not None else None

            # --- Overall rank
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

def parse_collection(root):
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

        objectid = item.attrib.get("objectid", "")
        game = {
            "id": objectid,
            "name": item.find("name").text if item.find("name") is not None else "",
            "minplayers": minplayers,
            "maxplayers": maxplayers,
            "playingtime": playingtime,
            "image": image,
            "average": average,
            "averageweight": None,
            "overallrank": None,
            "url": f"https://boardgamegeek.com/boardgame/{objectid}"
        }

        data[category].append(game)
        ids_to_fetch.append(objectid)

    # тянем weight и rank
    stats_data = fetch_game_stats_batch(ids_to_fetch)
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
    args = parser.parse_args()

    root = fetch_collection_ready(args.username)
    collection = parse_collection(root)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(collection, f, ensure_ascii=False, indent=2)

    print(f"✅ Collection saved to {args.out}")

if __name__ == "__main__":
    main()
