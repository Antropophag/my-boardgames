#!/usr/bin/env python3
import time, argparse, requests, xml.etree.ElementTree as ET, json

def fetch_collection(username, retries=12, delay=5):
    url = f"https://boardgamegeek.com/xmlapi2/collection?username={username}&own=1&subtype=boardgame&stats=1"
    for i in range(retries):
        r = requests.get(url, timeout=30)
        text = r.text
        if "<message" not in text:
            return ET.fromstring(text)
        time.sleep(delay)
    raise RuntimeError("collection not ready")

def fetch_thing(id_):
    url = f"https://boardgamegeek.com/xmlapi2/thing?id={id_}&stats=1"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return ET.fromstring(r.text)

def parse_collection(xmlroot):
    items = []
    for item in xmlroot.findall('item'):
        oid = item.get('objectid')
        name_el = item.find('name')
        name = name_el.get('value') if name_el is not None else ''
        image = item.findtext('image', default='')
        stats = item.find('stats')
        minp = stats.get('minplayers') if stats is not None else '?'
        maxp = stats.get('maxplayers') if stats is not None else '?'
        playt = stats.get('playingtime') if stats is not None else '?'
        items.append({'id': oid, 'name': name, 'image': image, 'minPlayers': minp, 'maxPlayers': maxp, 'playingTime': playt})
    return items

def parse_thing_stats(xmlroot):
    avg = None
    weight = None
    avg_node = xmlroot.find('.//statistics/ratings/average')
    weight_node = xmlroot.find('.//statistics/ratings/averageweight')
    if avg_node is not None and 'value' in avg_node.attrib:
        try: avg = float(avg_node.attrib['value'])
        except: avg = None
    if weight_node is not None and 'value' in weight_node.attrib:
        try: weight = float(weight_node.attrib['value'])
        except: weight = None
    item = xmlroot.find('item')
    name = None
    image = None
    if item is not None:
        n = item.find('name')
        if n is not None and 'value' in n.attrib: name = n.get('value')
        image = item.findtext('image')
    return {'average': avg, 'weight': weight, 'thingName': name, 'thingImage': image}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--username', required=True)
    p.add_argument('--out', required=True)
    args = p.parse_args()

    col = fetch_collection(args.username)
    base = parse_collection(col)

    out = []
    for i, g in enumerate(base, 1):
        try:
            t = fetch_thing(g['id'])
            stats = parse_thing_stats(t)
            image = g['image'] or stats.get('thingImage') or ''
            name = g['name'] or stats.get('thingName') or ''
            out.append({
                'id': g['id'],
                'name': name,
                'image': image,
                'minPlayers': g['minPlayers'],
                'maxPlayers': g['maxPlayers'],
                'playingTime': g['playingTime'],
                'average': stats.get('average'),
                'weight': stats.get('weight')
            })
        except Exception as e:
            print(f"Warning: failed thing {g['id']}: {e}")
            out.append({
                'id': g['id'],
                'name': g['name'],
                'image': g['image'],
                'minPlayers': g['minPlayers'],
                'maxPlayers': g['maxPlayers'],
                'playingTime': g['playingTime'],
                'average': None,
                'weight': None
            })
        time.sleep(0.12)

    # write JSON
import os
import json

# Создаём папку, если её нет
os.makedirs(os.path.dirname(args.out), exist_ok=True)

# Сохраняем данные в JSON
with open(args.out, 'w', encoding='utf-8') as f:
    json.dump(all_games, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
