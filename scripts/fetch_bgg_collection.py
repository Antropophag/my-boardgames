import argparse
import json
import requests
import xml.etree.ElementTree as ET

BGG_API_COLLECTION = "https://boardgamegeek.com/xmlapi2/collection"

def fetch_collection(username, subtype="boardgame"):
    """
    Загружает коллекцию BGG пользователя и возвращает список игр для own, wishlist и preordered
    """
    params = {
        "username": username,
        "subtype": subtype,
        "stats": 1,  # чтобы подтягивались min/max players, playingtime, рейтинг и averageweight
    }
    response = requests.get(BGG_API_COLLECTION, params=params)
    response.raise_for_status()

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

            weight_node = stats.find('averageweight')
            averageweight = float(weight_node.text) if weight_node is not None else None
        else:
            minplayers = maxplayers = playingtime = 0
            average = 0.0
            averageweight = None

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
            "averageweight": averageweight
        }

        data[category].append(game)

    return data

def main():
    parser = argparse.ArgumentParser(description="Fetch BGG collection")
    parser.add_argument("--username", required=True, help="BGG username")
    parser.add_argument("--out", required=True, help="Output JSON file path")
    args = parser.parse_args()

    collection = fetch_collection(args.username)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(collection, f, ensure_ascii=False, indent=2)

    print(f"Collection saved to {args.out}")

if __name__ == "__main__":
    main()
