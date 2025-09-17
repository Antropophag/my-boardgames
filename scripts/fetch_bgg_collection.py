import requests
import xml.etree.ElementTree as ET
import json

BGG_API = "https://boardgamegeek.com/xmlapi2/collection"

def fetch_games(username, collection_type):
    """
    collection_type: "own" или "wishlist"
    """
    params = {
        "username": username,
        "subtype": "boardgame",
        "stats": 1  # обязательно для рейтингов
    }
    if collection_type == "own":
        params["own"] = 1
    else:
        params["wishlist"] = 1

    res = requests.get(BGG_API, params=params)
    root = ET.fromstring(res.content)

    games = []
    for item in root.findall('item'):
        game_id = item.get('objectid')
        name_tag = item.find('name')
        image_tag = item.find('image')
        minp_tag = item.find('minplayers')
        maxp_tag = item.find('maxplayers')
        playtime_tag = item.find('playingtime')
        stats_tag = item.find('stats')

        name = name_tag.text if name_tag is not None else "Unknown"
        image = image_tag.text if image_tag is not None else ""
        minplayers = int(minp_tag.text) if minp_tag is not None else 0
        maxplayers = int(maxp_tag.text) if maxp_tag is not None else 0
        playingtime = int(playtime_tag.text) if playtime_tag is not None else 0

        average = 0.0
        if stats_tag is not None:
            ratings = stats_tag.find('ratings')
            if ratings is not None:
                avg_tag = ratings.find('average')
                if avg_tag is not None:
                    try:
                        average = float(avg_tag.get('value', 0.0))
                    except ValueError:
                        average = 0.0

        games.append({
            "id": game_id,
            "name": name,
            "minplayers": minplayers,
            "maxplayers": maxplayers,
            "playingtime": playingtime,
            "image": image,
            "average": average
        })
    return games

def main():
    username = "Antropophag"
    collection = {
        "own": fetch_games(username, "own"),
        "wishlist": fetch_games(username, "wishlist")
    }
    with open("data/games.json", "w", encoding="utf-8") as f:
        json.dump(collection, f, ensure_ascii=False, indent=2)
    print(f"Collection saved: {len(collection['own'])} own, {len(collection['wishlist'])} wishlist")

if __name__ == "__main__":
    main()
