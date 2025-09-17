import requests
import xml.etree.ElementTree as ET
import json

USERNAME = "Antropophag"

# Список типов коллекции, которые хотим получить
COLLECTION_TYPES = {
    "own": "own=1",
    "wishlist": "wishlist=1"
}

result = {}

for key, param in COLLECTION_TYPES.items():
    url = f"https://boardgamegeek.com/xmlapi2/collection?username={USERNAME}&subtype=boardgame&stats=1&{param}"
    response = requests.get(url)
    response.raise_for_status()

    root = ET.fromstring(response.content)
    games = []

    for item in root.findall('item'):
        game_id = item.attrib['objectid']
        name = item.find('name').text
        image = item.find('image').text if item.find('image') is not None else None

        stats = item.find('stats')
        minplayers = int(stats.attrib.get('minplayers', 0))
        maxplayers = int(stats.attrib.get('maxplayers', 0))
        playingtime = int(stats.attrib.get('playingtime', 0))

        rating = stats.find('rating')
        average = float(rating.find('average').attrib.get('value', 0)) if rating is not None else 0.0

        games.append({
            "id": game_id,
            "name": name,
            "minplayers": minplayers,
            "maxplayers": maxplayers,
            "playingtime": playingtime,
            "image": image,
            "average": average
        })

    result[key] = games

# Вывод JSON
print(json.dumps(result, indent=2, ensure_ascii=False))
