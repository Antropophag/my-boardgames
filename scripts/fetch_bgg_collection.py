import argparse
import json
import requests
import xml.etree.ElementTree as ET
import time

BGG_API_COLLECTION = "https://boardgamegeek.com/xmlapi2/collection"
BGG_API_THING = "https://boardgamegeek.com/xmlapi2/thing"

def fetch_collection(username, subtype="boardgame"):
    """
    Загружает коллекцию BGG пользователя и возвращает список игр с базовыми данными.
    Обрабатывает статус 202 (подготовка данных) с повторным запросом.
    """
    params = {
        "username": username,
        "subtype": subtype,
        "stats": 1,
    }

    while True:
        response = requests.get(BGG_API_COLLECTION, params=params)
        if response.status_code == 202:
            print("BGG формирует коллекцию, ждем 5 секунд...")
            time.sleep(5)
            continue
        response.raise_for_status()
        break

    root = ET.fromstring(response.content)
    data = {"own": [], "wishlist": [], "preordered": []}

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
            "averageweight": None,
        }

        data[category].append(game)

    return data

def fetch_averageweight_batch(game_ids):
    """
    Получает averageweight для пакета игр (макс. 100 игр за раз)
    """
    if not game_ids:
        return {}
    params = {
        "id": ",".join(game_ids),
        "stats": 1
    }
    while True:
        response = requests.get(BGG_API_THING, params=params)
        if response.status_code == 202:
            print("BGG формирует данные игр, ждем 5 секунд...")
            time.sleep(5)
            continue
        response.raise_for_status()
        break

    root = ET.fromstring(response.content)
    result = {}
    for item in root.findall('item'):
        gid = item.attrib.get('id')
        weight_node = item.find('statistics/ratings/averageweight')
        if weight_node is not None:
            try:
                result[gid] = float(weight_node.attrib.get('value'))
            except:
                result[gid] = None
        else:
            result[gid] = None
    return result

def main():
    parser = argparse.ArgumentParser(description="Fetch BGG collection with averageweight")
    parser.add_argument("--username", required=True, help="BGG username")
    parser.add_argument("--out", required=True, help="Output JSON file path")
    args = parser.parse_args()

    collection = fetch_collection(args.username)

    # Собираем все ID игр по категориям
    all_games = []
    for category in collection:
        all_games.extend(collection[category])

    # Обрабатываем пакетами по 50 игр
    BATCH_SIZE = 50
    for i in range(0, len(all_games), BATCH_SIZE):
        batch = all_games[i:i+BATCH_SIZE]
        ids = [game["id"] for game in batch]
        weights = fetch_averageweight_batch(ids)
        for game in batch:
            game["averageweight"] = weights.get(game["id"])
        # Пауза 5 секунд между пакетами
        time.sleep(5)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(collection, f, ensure_ascii=False, indent=2)

    print(f"Collection saved to {args.out}")

if __name__ == "__main__":
    main()
