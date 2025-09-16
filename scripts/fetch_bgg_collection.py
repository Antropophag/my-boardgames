import requests
import xml.etree.ElementTree as ET
import json
import time

def safe_int(tag):
    try:
        return int(tag.text)
    except:
        return 0

def safe_float(tag):
    try:
        return float(tag.get('value', 0.0))
    except:
        return 0.0

def fetch_collection(username, own_only=True):
    """Fetches user's collection or wishlist from BGG"""
    url = f"https://boardgamegeek.com/xmlapi2/collection?username={username}&subtype=boardgame&stats=1"
    if own_only:
        url += "&own=1"
    else:
        url += "&wishlist=1"

    while True:
        res = requests.get(url)
        root = ET.fromstring(res.content)

        # Если API ещё не готово, ждем
        if root.tag == 'message' or root.attrib.get('termsofuse'):
            print("Collection not ready, waiting 5s...")
            time.sleep(5)
        else:
            break

    games = []

    for item in root.findall('item'):
        game_id = item.get('objectid')
        name_tag = item.find('name')
        image_tag = item.find('image')

        stats = item.find('stats')
        average = safe_float(stats.find('ratings/average')) if stats is not None else 0.0

        games.append({
            "id": game_id,
            "name": name_tag.text if name_tag is not None else "",
            "minplayers": safe_int(item.find('minplayers')),
            "maxplayers": safe_int(item.find('maxplayers')),
            "playingtime": safe_int(item.find('playingtime')),
            "image": image_tag.text if image_tag is not None else "",
            "average": average
        })

    return games

def main():
    username = "Antropophag"

    print("Fetching owned games...")
    own = fetch_collection(username, own_only=True)

    print("Fetching wishlist games...")
    wishlist = fetch_collection(username, own_only=False)

    collection = {
        "own": own,
        "wishlist": wishlist
    }

    with open("data/games.json", "w", encoding="utf-8") as f:
        json.dump(collection, f, ensure_ascii=False, indent=2)

    print(f"Collection saved to data/games.json. Own: {len(own)}, Wishlist: {len(wishlist)}")

if __name__ == "__main__":
    main()
