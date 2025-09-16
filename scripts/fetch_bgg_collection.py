import requests
import xml.etree.ElementTree as ET
import json
import argparse
import os
import time

BGG_API_COLLECTION = "https://boardgamegeek.com/xmlapi2/collection"
BGG_API_THING = "https://boardgamegeek.com/xmlapi2/thing"

def fetch_collection(username):
    print(f"Fetching collection for {username}...")
    url = f"{BGG_API_COLLECTION}?username={username}&own=1&subtype=boardgame&stats=1"
    response = requests.get(url)
    response.raise_for_status()
    root = ET.fromstring(response.content)
    game_ids = [item.get('objectid') for item in root.findall('item')]
    return game_ids

def fetch_game_details(game_ids, batch_size=10, delay=1):
    games = []
    print(f"Fetching {len(game_ids)} game details...")
    for i in range(0, len(game_ids), batch_size):
        batch = game_ids[i:i+batch_size]
        ids = ','.join(batch)
        url = f"{BGG_API_THING}?id={ids}&stats=1"
        response = requests.get(url)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        for item in root.findall('item'):
            game_id = item.get('id')
            name_elem = item.find("name[@type='primary']")
            name = name_elem.get('value') if name_elem is not None else "Unknown"
            image_elem = item.find('image')
            image = image_elem.text if image_elem is not None else ""
            stats = item.find('statistics/ratings')
            rating_elem = stats.find('average') if stats is not None else None
            rating = float(rating_elem.get('value')) if rating_elem is not None else 0.0
            # Игроки и время
            min_players_elem = item.find('minplayers')
            max_players_elem = item.find('maxplayers')
            playingtime_elem = item.find('playingtime')
            min_players = int(min_players_elem.get('value', 0)) if min_players_elem is not None else 0
            max_players = int(max_players_elem.get('value', 0)) if max_players_elem is not None else 0
            playing_time = int(playingtime_elem.get('value', 0)) if playingtime_elem is not None else 0

            games.append({
                "id": game_id,
                "name": name,
                "image": image,
                "minplayers": min_players,
                "maxplayers": max_players,
                "playingtime": playing_time,
                "bgg_rating": round(rating, 1)
            })
        time.sleep(delay)
    return games

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', required=True, help='BGG username')
    parser.add_argument('--out', required=True, help='Output JSON file')
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    game_ids = fetch_collection(args.username)
    games = fetch_game_details(game_ids)
    
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(games, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(games)} games to {args.out}")

if __name__ == "__main__":
    main()
