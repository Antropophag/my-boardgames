import requests
import xml.etree.ElementTree as ET
import json
import time

def fetch_collection_basic(username):
    """Быстрое получение коллекции без статистики"""
    url = f"https://boardgamegeek.com/xmlapi2/collection?username={username}&own=1&subtype=boardgame"
    res = requests.get(url)
    root = ET.fromstring(res.content)

    own = []
    wishlist = []

    for item in root.findall('item'):
        game_id = item.get('objectid')
        name = item.find('name').text
        image = item.find('image').text

        own.append({
            "id": game_id,
            "name": name,
            "minplayers": int(item.find('minplayers').text or 0),
            "maxplayers": int(item.find('maxplayers').text or 0),
            "playingtime": int(item.find('playingtime').text or 0),
            "image": image,
            "average": 0.0  # пока 0, потом подтянем
        })

    return {"own": own, "wishlist": wishlist}

def fetch_average(game_id):
    """Получение средней оценки для одной игры"""
    url = f"https://boardgamegeek.com/xmlapi2/thing?id={game_id}&stats=1"
    while True:
        res = requests.get(url)
        root = ET.fromstring(res.content)
        # Если API вернул message или error, подождем
        if root.tag in ('message', 'error'):
            print(f"Stats for {game_id} not ready, waiting 5s...")
            time.sleep(5)
        else:
            break

    average = 0.0
    ratings = root.find('.//ratings')
    if ratings is not None:
        avg_tag = ratings.find('average')
        if avg_tag is not None:
            try:
                average = float(avg_tag.get('value', 0.0))
            except ValueError:
                average = 0.0
    return average

def main():
    username = "Antropophag"
    collection = fetch_collection_basic(username)

    print(f"Found {len(collection['own'])} games. Fetching averages...")

    for game in collection['own']:
        game['average'] = fetch_average(game['id'])
        print(f"{game['name']}: {game['average']}")

    # Сохраняем результат
    with open("data/games.json", "w", encoding="utf-8") as f:
        json.dump(collection, f, ensure_ascii=False, indent=2)
    print("Collection saved to data/games.json")

if __name__ == "__main__":
    main()
