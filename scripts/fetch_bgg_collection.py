import requests
import xml.etree.ElementTree as ET
import json
import time

def fetch_collection(username):
    url = f"https://boardgamegeek.com/xmlapi2/collection?username={username}&own=1&subtype=boardgame&stats=1"
    
    # Ждем, пока коллекция будет готова
    while True:
        res = requests.get(url)
        root = ET.fromstring(res.content)

        message = root.find('message')
        if message is not None and "Collection not ready" in message.text:
            print("Collection not ready, waiting 5s...")
            time.sleep(5)
        else:
            break

    def get_int(tag, default=0):
        return int(tag.text) if tag is not None and tag.text else default

    def get_text(tag, default=""):
        return tag.text if tag is not None and tag.text else default

    own = []
    wishlist = []

    for item in root.findall('item'):
        game_id = item.get('objectid', "0")
        name = get_text(item.find('name'), "Unknown")
        image = get_text(item.find('image'), "")

        minplayers = get_int(item.find('minplayers'))
        maxplayers = get_int(item.find('maxplayers'))
        playingtime = get_int(item.find('playingtime'))

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
    username = "Antropophag"
    print(f"Fetching collection for user: {username}")
    collection = fetch_collection(username)
    with open("data/games.json", "w", encoding="utf-8") as f:
        json.dump(collection, f, ensure_ascii=False, indent=2)
    print(f"Collection saved to data/games.json ({len(collection['own'])} games)")

if __name__ == "__main__":
    main()
