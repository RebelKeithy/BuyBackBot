from multiprocessing.pool import Pool

import price_checker

from item_ids import item_ids

ORES = ['Veldspar', 'Scordite', 'Plagioclase', 'Omber', 'Kernite', 'Jaspet', 'Hemorphite', 'Hedbergite', 'Spodumain', 'Dark Ochre', 'Gneiss', 'Bistot', 'Arkonor', 'Mercoxit']
if __name__ == '__main__':
    ore_ids = [item_ids[ore] for ore in ORES]
    p = Pool(processes=3)
    prices = p.map(price_checker.get_price_online, ore_ids)
    p.close()
    p.join()
    print("test")
    print(prices)