import requests
import xml.etree.ElementTree as ET
import json

def fetch_collection(username, collection_type):
    """
    collection_type: "own" или "wishlist"
    """
    params = {
        "username": username,
        "subtype": "boardgame",
        "stats": 1
    }
    if collection_type == "own":
        params["own"] = 1
    elif collection_type == "wishlist":
        params["wishlist"] = 1

    url = "https://boardgamegeek.com/xmlapi2/collection"
    res = requests.get(url, params=params)
    root = ET.fromstring(res.content)

    games = []
    for item in root.findall('item'):
        # Иногда тег отсутствует, используем 0 по умолчанию
        def get_int(tag_name):
            t = item.find(tag_name)
            return int(t.text) if t is not None and t.text.isdigit() else 0

        # Average rating
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

        # Извлекаем название и изображение
        name_tag = item.find('name')
        image_tag = item.find('image')
        name = name_tag.text if name_tag is not None else "Unknown"
        image = image_tag.text if image_tag is not None else ""

        games.append({
            "id": item.get("objectid"),
            "name": name,
            "minplayers": get_int("minplayers"),
            "maxplayers": get_int("maxplayers"),
            "playingtime": get_int("playingtime"),
            "image": image,
            "average": average
        })
    return games

def main():
    username = "Antropophag"
    own_games = fetch_collection(username, "own")
    wishlist_games = fetch_collection(username, "wishlist")

    data = {
        "own": own_games,
        "wishlist": wishlist_games
    }

    with open("data/games.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(own_games)} own games and {len(wishlist_games)} wishlist games to data/games.json")

if __name__ == "__main__":
    main()
