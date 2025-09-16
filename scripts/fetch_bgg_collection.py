import requests
import xml.etree.ElementTree as ET
import json
import os
import argparse
import time

def get_int(elem, default=0):
    return int(elem.text) if elem is not None and elem.text else default

def fetch_collection(username):
    url = f"https://boardgamegeek.com/xmlapi2/collection?username={username}&subtype=boardgame&stats=1"
    print(f"Fetching collection for {username}...")

    retries = 10
    while retries > 0:
        r = requests.get(url)
        if r.status_code == 202:
            print("Collection not ready, waiting 10s...")
            time.sleep(10)
            retries -= 1
        else:
            break
    if r.status_code != 200:
        raise Exception(f"Failed to fetch collection, status {r.status_code}")

    root = ET.fromstring(r.content)

    own_games = []
    wishlist_games = []

    for item in root.findall('item'):
        name_elem = item.find('name')
        minp = get_int(item.find('minplayers'))
        maxp = get_int(item.find('maxplayers'))
        time_play = get_int(item.find('playingtime'))

        game_data = {
            "id": item.get('objectid'),
            "name": name_elem.text if name_elem is not None else "Unknown",
            "minplayers": minp,
            "maxplayers": maxp,
            "playingtime": time_play,
            "image": item.find('image').text if item.find('image') is not None else "",
        }

        # рейтинг Average
        stats = item.find('stats')
        rating = 0.0
        if stats is not None:
            ratings = stats.find('ratings')
            if ratings is not None:
                avg = ratings.find('average')
                if avg is not None and avg.get('value') not in (None, 'N/A'):
                    rating = round(float(avg.get('value')), 1)
        game_data["bgg_rating"] = rating

        # статус игры
        status = item.find('status')
        if status is not None:
            if status.get('own') == '1':
                own_games.append(game_data)
            elif status.get('wishlist') == '1':
                wishlist_games.append(game_data)

    return own_games, wishlist_games

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', required=True)
    parser.add_argument('--out', default='data/games.json')
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    own, wishlist = fetch_collection(args.username)

    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump({"own": own, "wishlist": wishlist}, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(own)} owned games and {len(wishlist)} wishlist games to {args.out}")

if __name__ == "__main__":
    main()
