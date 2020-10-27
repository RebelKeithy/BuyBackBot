import json
import time

import requests

SECOND = 1
MINUTE = 60 * SECOND
HOUR = 60 * MINUTE


class PriceChecker:
    def __init__(self):
        self.cache = {}
        self.items = {}
        self.aliases = {}

    def all_items(self):
        return list(self.items.keys()) + list(self.aliases.keys())

    def add_alias(self, alias, name):
        if name not in self.items.keys():
            raise ValueError()
        self.aliases[alias] = name

    def add_invalid_item(self, name, display_name):
        self.update_price(name, -1, display_name)

    def update_price(self, name, price, display_name):
        self.items[name] = (price, display_name)

    def get_price(self, name):
        if name in self.aliases.keys():
            name = self.aliases[name]

        if self.items[name][0] == -1:
            raise ValueError(f'{name} is invalid')
        return self.items[name][0]

    def get_display_name(self, name):
        if name in self.aliases.keys():
            name = self.aliases[name]

        return self.items[name][1]

    def get_price_online(self, item_id):
        if item_id in self.cache.keys():
            if time.time() < self.cache[item_id]["expires"]:
                return self.cache[item_id]["price"]

        print(f"Getting online price for {item_id}")
        response = requests.get(f'https://api.eve-echoes-market.com/market-stats/{item_id}')
        print(response.content)
        data = json.loads(response.content.decode('utf-8'))
        price = float(data[-1]['highest_buy'])
        self.cache[item_id] = {
            "price": price,
            "expires": time.time() + 6 * HOUR
        }
        return price
