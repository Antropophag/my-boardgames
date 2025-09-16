import argparse
import requests
import xml.etree.ElementTree as ET
import json
import os
import time

BGG_COLLECTION_URL = "https://boardgamegeek.com/xmlapi2/collection"
BGG_THING_URL = "https://boardgamegeek.com/xmlapi2/thing"

def fetch_collection(username):
    print(f"Fetching collection for {username}...")
    params = {
        "username": username,
        "own": 1,
        "subtype": "boardgame",
        "stats": 1
    }
    while True:
        r = requests.get(BGG_COLLECTION_URL, params=params)
        if r.status_code != 202:  # 202 = queued
            break
        print("Collection queued, waiting 3s...")
        time.sleep(3)
    r.raise_for_status()
    return r.content

def fetch_thing(game_ids):
    print(f"Fetching {len(game_ids)} game details...")
    all_games = []
    batch_size = 10  # можно регулировать
    for i in range(0, len(game_ids), batch_size):
        batch_ids = game_ids[i:i+batch_size]
        params = {
            "id": ",".join(batch_ids),
            "stats": 1
        }
        r = requests.get(BGG_THING_URL, params=params)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        for item in root.findall('item'):
            game = {
                "id": item.get('id'),
                "name": item.find('name').get('value'),
                "image": item.find('image').text if item.find('image') is not None else "",
                "minplayers": int(item.find('minplayers').get('value')),
                "maxplayers": int(item.find('maxplayers').get('value')),
                "playingtime": int(item.find('playingtime').get('value')),
                "average": round(float(item.find('statistics/ratings/average').get('value')), 1)
            }
            all_games.append(game)
    return all_games

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True, help="BGG username")
    parser.add_argument("--out", required=True, help="Output JSON file path")
    args = parser.parse_args()

    # Создаём папку для вывода, если её нет
    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    # Получаем коллекцию пользователя
    xml_data = fetch_collection(args.username)
    root = ET.fromstring(xml_data)
    game_ids = [item.get('objectid') for item in root.findall('item')]

    if not game_ids:
        print("No games found in collection.")
        with open(args.out, 'w', encoding='utf-8') as f:
            json.dump([], f)
        return

    # Получаем подробности игр
    all_games = fetch_thing(game_ids)

    # Сохраняем в JSON
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(all_games, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(all_games)} games to {args.out}")

if __name__ == "__main__":
    main()
