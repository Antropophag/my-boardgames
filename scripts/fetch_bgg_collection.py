import requests
import xml.etree.ElementTree as ET
import json
import os
import argparse
import time

def fetch_collection(username):
    url = f"https://boardgamegeek.com/xmlapi2/collection?username={username}&subtype=boardgame&stats=1"
    print(f"Fetching collection for {username}...")
    
    while True:
        r = requests.get(url)
        if r.status_code == 202:
            # BGG ещё формирует коллекцию, ждём
            print("Collection not ready, waiting 5s...")
            time.sleep(5)
        else:
            break

    root = ET.fromstring(r.content)

    own_games = []
    wishlist_games = []

    for item in root.findall('item'):
        status = item.find('status')
        game_data = {
            "id": item.get('objectid'),
            "name": item.find('name').text,
            "minplayers": int(item.find('minplayers').text),
            "maxplayers": int(item.find('maxplayers').text),
            "playingtime": int(item.find('playingtime').text),
            "image": item.find('image').text if item.find('image') is not None else "",
        }

        # рейтинг Average
        stats = item.find('stats')
        rating = 0.0
        if stats is not None:
            ratings = stats.find('ratings')
            if ratings is not None:
                avg = ratings.find('average')
                if avg is not None and avg.get('value') != 'N/A':
                    rating = round(float(avg.get('value')), 1)
        game_data["bgg_rating"] = rating

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

    # сохраняем в один JSON
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump({"own": own, "wishlist": wishlist}, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(own)} owned games and {len(wishlist)} wishlist games to {args.out}")

if __name__ == "__main__":
    main()
