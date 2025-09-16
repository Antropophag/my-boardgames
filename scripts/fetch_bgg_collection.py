import requests
import xml.etree.ElementTree as ET
import json
import time

def fetch_collection(username):
    """Получаем основную коллекцию пользователя с проверкой готовности API"""
    url = f"https://boardgamegeek.com/xmlapi2/collection?username={username}&own=1&subtype=boardgame&stats=1"
    
    while True:
        res = requests.get(url)
        root = ET.fromstring(res.content)

        # Проверка, готов ли API к выдаче данных
        if root.attrib.get('termsofuse'):
            print("Collection not ready, waiting 5s...")
            time.sleep(5)
        else:
            break

    own = []
    wishlist = []

    for item in root.findall('item'):
        game_id = item.get('objectid')
        name = item.find('name').text
        image = item.find('image').text

        # Минимальное/максимальное количество игроков
        minplayers = int(item.find('minplayers').text or 0)
        maxplayers = int(item.find('maxplayers').text or 0)
        playingtime = int(item.find('playingtime').text or 0)

        # Средний рейтинг
        average = 0.0
        stats = item.find('stats')
        if stats is not None:
            ratings = stats.find('ratings')
            if ratings is not None:
                avg_tag = ratings.find('average')
                if avg_tag is not None:
                    try:
                        average = float(avg_tag.get('value', 0.0))
                    except ValueError:
                        average = 0.0

        own.append({
            "id": game_id,
            "name": name,
            "minplayers": minplayers,
            "maxplayers": maxplayers,
            "playingtime": playingtime,
            "image": image,
            "average": average
        })

    return {"own": own, "wishlist": wishlist}


def main():
    username = "Antropophag"  # <-- поменяй на свой ник
    collection = fetch_collection(username)
    
    with open("data/games.json", "w", encoding="utf-8") as f:
        json.dump(collection, f, ensure_ascii=False, indent=2)
    
    print(f"Collection saved: {len(collection['own'])} games")


if __name__ == "__main__":
    main()
