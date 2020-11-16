from datetime import datetime

import gspread

from Contract import Contract
from price_checker import PriceChecker

key = '1_td9spLwMZEIBZ2_fdwA2zuYcjvTOCy4ZHati0w0Y0c'
gc = gspread.service_account()
sh = gc.open_by_key(key)

price_sheet = sh.worksheet('BuybackPrices')
ship_price_sheet = sh.worksheet('Ship Prices')
log_sheet = sh.worksheet('Buyback Log')


def is_number(s):
    try:
        float(s)
        return True
    except:
        return False


def load_ship_prices(price_checker, market_price_checker):
    values = ship_price_sheet.get_all_values()
    values = list(map(list, zip(*values)))
    for col in range(0, 8 * 4, 4):
        for row in range(4, len(values[col])):
            name = values[col][row]
            price = values[col+1][row]
            market_price = values[col+2][row]
            if not is_number(price):
                continue
            print(f"{name} {price} {market_price}")
            try:
                float(price)
                float(market_price)
                price_checker.update_price(name, float(price), name)
                market_price_checker.update_price(name, float(market_price), name)
            except ValueError:
                pass

    # for i in range(6):
    #     items = ship_price_sheet.col_values(i*4+1)
    #     prices = ship_price_sheet.col_values(i*4+2)
    #     market_prices = ship_price_sheet.col_values(i*4+3)
    #     print(items)
    #
    #     for item, price, market_price in zip(items, prices, market_prices):
    #         if not is_number(price):
    #             continue
    #         print(f"{item}, {price}, {market_price}")
    #         price_checker.update_price(item, float(price), item)
    #         market_price_checker.update_price(item, float(market_price), item)


def load_prices(price_checker):
    values = price_sheet.get_all_values()
    values = list(map(list, zip(*values)))
    for col in range(1, 6 * 2, 2):
        for row in range(1, len(values[col])):
            name = values[col][row]
            price = values[col+1][row]
            if not is_number(price):
                continue
            print(f"{name} {price}")
            price_checker.update_price(name, float(price), name)

    # for i in range(6):
    #     items = price_sheet.col_values(i*2+2)
    #     prices = price_sheet.col_values(i*2+3)
    #     print(items)
    #
    #     for item, price in zip(items, prices):
    #         if not is_number(price):
    #             continue
    #
    #         price_checker.update_price(item, float(price), item)


def save_contract(contract, payee, notes):
    items, prices, amounts, item_prices = zip(*contract.items)
    total = sum(prices)
    col_values = log_sheet.col_values(1)
    print(col_values)
    row = len(col_values) + 1

    log_sheet.update(f'A{row}:G', [[contract.player, contract.sent, payee, str(datetime.now()), 'N', total, notes]])

if __name__ == '__main__':
    # values = ship_price_sheet.get_all_values()
    # values = list(map(list, zip(*values)))
    # for col in range(0, 8 * 4 + 1, 4):
    #     print((values[col]))
    #     for row in range(4, len(values[col])):
    #         print('Value: ' + values[col][row])
    # print(values)
    # load_prices(PriceChecker())
    pass