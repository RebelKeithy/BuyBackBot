import json
import time

import requests

SECOND = 1
MINUTE = 60 * SECOND
HOUR = 60 * MINUTE

cache = {}
items = {}


def all_items():
    return list(items.keys())


def add_invalid_item(name, display_name):
    update_price(name, -1, display_name)


def update_price(name, price, display_name):
    global items
    items[name] = (price, display_name)


def get_price(name):
    if items[name][0] == -1:
        raise ValueError(f'{name} is invalid')
    return items[name][0]


def get_display_name(name):
    return items[name][1]


def get_price_online(item_id):
    global cache
    if item_id in cache.keys():
        if time.time() < cache[item_id]["expires"]:
            return cache[item_id]["price"]

    print(f"Getting online price for {item_id}")
    response = requests.get(f'https://api.eve-echoes-market.com/market-stats/{item_id}')
    print(response.content)
    data = json.loads(response.content.decode('utf-8'))
    price = float(data[-1]['highest_buy'])
    cache[item_id] = {
        "price": price,
        "expires": time.time() + 6 * HOUR
    }
    return price
