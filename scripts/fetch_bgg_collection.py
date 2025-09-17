import argparse
import json
import requests
import xml.etree.ElementTree as ET
import time

BGG_API_COLLECTION = "https://boardgamegeek.com/xmlapi2/collection"
BGG_API_THING = "https://boardgamegeek.com/xmlapi2/thing"

def fetch_collection(username, subtype="boardgame", retries=10, delay=5):
    """
    Загружает коллекцию BGG пользователя с повтором, если API возвращает пустой результат.
    """
    params = {
        "username": username,
        "subtype": subtype,
        "stats": 1,
        "own": 1,
        "wishlist": 1,
        "preordered": 1
    }

    for attempt in range(retries):
        response = requests.get(BGG_API_COLLECTION, params=params)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        totalitems = int(root.attrib.get("totalitems", 0))
        if totalitems > 0:
            break
        print(f"⚠ Collection empty, retry {attempt + 1}/{retries} in {delay}s...")
        time.sleep(delay)
    else:
        print("❌ Collection still empty after retries")
        return {"own": [], "wishlist": [], "preordered": []}

    data = {"own": [], "wishlist": [], "preordered": []}
    ids = []

    for item in root.findall('item'):
        status = item.find('status')
        if status is None:
            continue

        if status.attrib.get('own') == '1':
            category = 'own'
        elif status.attrib.get('wishlist') == '1':
            category = 'wishlist'
        elif status.attrib.get('preordered') == '1':
            category = 'preordered'
        else:
            continue

        stats = item.find('stats')
        if stats is not None:
            minplayers = int(stats.attrib.get('minplayers', 0))
            maxplayers = int(stats.attrib.get('maxplayers', 0))
            playingtime = int(stats.attrib.get('playingtime', 0))
            rating_node = stats.find('rating/average')
            average = float(rating_node.attrib.get('value', 0)) if rating_node is not None else 0.0
        else:
            minplayers = maxplayers = playingtime = 0
            average = 0.0

        image_node = item.find('image')
        image = image_node.text if image_node is not None else ""

        game = {
            "id": item.attrib.get('objectid', ""),
            "name": item.find('name').text if item.find('name') is not None else "",
            "minplayers": minplayers,
            "maxplayers": maxplayers,
            "playingtime": playingtime,
            "image": image,
            "average": average,
            "averageweight": None  # будет обновлено ниже
        }

        data[category].append(game)
        ids.append(item.attrib.get('objectid', ""))

    # Получаем averageweight через батчи
    weights = fetch_averageweight_batch(ids)
    for category in data:
        for game in data[category]:
            if game["id"] in weights:
                game["averageweight"] = weights[game["id"]]

    return data

def fetch_averageweight_batch(ids, batch_size=50, delay=5):
    """
    Получает averageweight для списка id игр через API thing (батчи)
    """
    weights = {}
    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i+batch_size]
        params = {
            "id": ",".join(batch_ids),
            "stats": 1
        }
        response = requests.get(BGG_API_THING, params=params)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        for item in root.findall('item'):
            game_id = item.attrib.get('id')
            stats = item.find('statistics/ratings')
            if stats is not None:
                weight_node = stats.find('averageweight')
                weights[game_id] = float(weight_node.attrib.get('value', 0)) if weight_node is not None else None
            else:
                weights[game_id] = None
        time.sleep(delay)  # пауза между батчами
    return weights

def main():
    parser = argparse.ArgumentParser(description="Fetch BGG collection")
    parser.add_argument("--username", required=True, help="BGG username")
    parser.add_argument("--out", required=True, help="Output JSON file path")
    args = parser.parse_args()

    collection = fetch_collection(args.username)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(collection, f, ensure_ascii=False, indent=2)

    print(f"✅ Collection saved to {args.out}")

if __name__ == "__main__":
    main()
