import types
from statistics import median

import cv2 as cv
import numpy as np

from src.ocr_text import OCRText, OCRChar

threshold = 200
scale = 1.0
image_rgb = None
image_bw = None


def load_image(filename, is_text=False):
    global image_rgb
    global image_bw
    image_orig = cv.imread(filename)

    width = int(image_orig.shape[1] * scale)
    height = int(image_orig.shape[0] * scale)

    s = 1920 / width
    width = int(width * s)
    height = int(height * s)
    dim = (width, height)
    dim_double = (2 * width, 2 * height)
    dim_half = (width // 2, height // 2)

    image_rgb = cv.resize(image_orig, dim_double, interpolation=cv.INTER_AREA)

    image_bw = cv.cvtColor(image_orig, cv.COLOR_BGR2GRAY)
    image_bw = cv.resize(image_bw, dim_double, interpolation=cv.INTER_AREA)


def get_locs(template_filename, threshold, merge_dist=4*20, bw=False):
    image = image_bw if bw else image_rgb
    template = cv.imread(template_filename)

    w = int(template.shape[1] * 2)
    h = int(template.shape[0] * 2)
    # if bw:
    #     w *= 2
    #     h *= 2
    # else:
    #     w = w // 2
    #     h = h // 2
    dim = (w, h)
    template = cv.resize(template, dim, interpolation=cv.INTER_AREA)

    if bw:
        template = cv.cvtColor(template, cv.COLOR_BGR2GRAY)
    res = cv.matchTemplate(image, template, cv.TM_CCOEFF_NORMED)

    loc = np.where(res >= threshold)
    loc = [(pt[0], pt[1], res[pt[1]][pt[0]]) for pt in zip(*loc[::-1])]
    loc = merge_nearby(loc, merge_dist)

    for i, pt in enumerate(loc):
        cv.rectangle(image_rgb, (pt[0], pt[1]), (pt[0] + w, pt[1] + h), (0, 0, 255), 2)
        pass
    cv.imwrite('res.png', image_rgb)
    #cv.imwrite(f'temp_{template_filename.split("/")[-1]}', template)
    #cv.imwrite('window_processed.png', image)
    return loc


def merge_nearby(positions, merge_dist):
    buckets = []
    for p in positions:
        found = False
        for i in range(len(buckets)):
            q = buckets[i]
            if max(abs(p[0] - q[0]), abs(p[1] - q[1])) < merge_dist:
                found = True
                if p[2] > q[2]:
                    buckets[i] = p
        if not found:
            buckets.append(p)

    return buckets


def filter_by_position(p, item, xoff, yoff):
    return item[0] - p[0] < xoff and p[1] - item[1] < yoff and p[0] < item[0] + 2*100 and p[1] > item[1] + 2*110


def find_scale():
    global scale
    best_scale = 1
    best_scale_certainty = 0
    for s in range(2, 300, 2):
        scale = s / 100
        print(scale)
        try:
            locs = get_locs("../resources/Inventory.PNG", 0.9)
            certainty = max([c for x, y, c in locs] + [0])
            if certainty > best_scale_certainty:
                best_scale = s
                best_scale_certainty = certainty
            print(certainty)
        except:
            pass
    scale = best_scale


def process_image(screenshot):
    ORES = ['Veldspar', 'Scordite', "Pyroxeres", 'Plagioclase', 'Omber', 'Kernite', 'Jaspet', 'Hemorphite', 'Hedbergite', 'Spodumain', 'Dark Ochre', 'Gneiss', 'Crokite', 'Bistot', 'Arkonor', 'Mercoxit']
    CHARS = [str(i) for i in range(10)] + ['-', 'k', 'm']
    load_image(screenshot)

    text_items = {}
    for i in CHARS:
        filename = f'resources/chars/{i}.png'
        item = cv.imread(filename, 0)
        w, h = item.shape[::-1]
        text_item = types.SimpleNamespace()
        text_item.char = i
        text_item.width = w
        text_item.locations = get_locs(filename, 0.7, 2*10, bw=True)
        text_items[i] = text_item
    text_items['-'].char = '.'
    for i in CHARS:
        print(f"{i}: {text_items[i]}")

    ores = []
    for ore in ORES:
        ore_locations = get_locs(f'resources/ore/{ore.lower()}.PNG', 0.7)
        print(ore_locations)
        for ore_location in ore_locations:
            text = OCRText()
            chars = []
            digits = {}
            for i in CHARS:
                text_item = text_items[i]
                chars.extend([(loc, text_item) for loc in text_item.locations if filter_by_position((loc[0], loc[1]), ore_location, 2*120, 2*160)])

            if not chars:
                continue

            med = median([t[0][1] for t in chars])
            print(f"Median: {med}")
            chars = [t for t in chars if abs(t[0][1] - med) < 4]

            for char in chars:
                x, y, certainty = char[0]
                ocr_char = OCRChar(char[1].char, char[1].width, certainty, x)
                text.add_char(ocr_char)

            text.debug_print()
            text.remove_overlapping()
            text.debug_print()

            amount = str(text)
            if not amount:
                amount = '0'
            if amount[0] == '.':
                amount = amount[1:]
            if amount[-1] == '.':
                amount = amount[:-1]
            print(f"{ore}: {amount}")
            print(digits)

            ores.append((ore, amount))
    return ores

def test():
    locs = process_image('resources/window.PNG')
    print(locs)
    assert locs == [('Pyroxeres', '4991'), ('Spodumain', '3294'), ('Gneiss', '2985')]

    locs = process_image('resources/window2.PNG')
    print(locs)
    assert locs == [('Veldspar', '17.4k'), ('Scordite', '15.61k'), ('Pyroxeres', '3953'), ('Kernite', '243'), ('Spodumain', '1983'), ('Dark Ochre', '2467'), ('Gneiss', '1776')]

    locs = process_image('resources/window3.PNG')
    print(locs)
    assert locs == [('Veldspar', '17.4k'), ('Scordite', '15.61k'), ('Pyroxeres', '3953'), ('Kernite', '243'), ('Spodumain', '1983'), ('Dark Ochre', '2467'), ('Gneiss', '1776')]

    locs = process_image('resources/window4.PNG')
    print(locs)
    assert locs == [('Pyroxeres', '6593'), ('Spodumain', '1292'), ('Dark Ochre', '1969'), ('Gneiss', '4912')]

    locs = process_image('resources/window6.PNG')
    print(locs)
    assert locs == [('Veldspar', '0.46m'), ('Scordite', '0.35m'), ('Pyroxeres', '0.1m'), ('Kernite', '17.09k'), ('Spodumain', '50.3k'), ('Dark Ochre', '71.21k'), ('Gneiss', '71.38k')]

def test2():
    locs = process_image('resources/window6.PNG')
    print(locs)
    assert locs == [('Veldspar', '0.46m'), ('Scordite', '0.35m'), ('Pyroxeres', '0.1m'), ('Kernite', '17.09k'), ('Spodumain', '50.3k'), ('Dark Ochre', '71.21k'), ('Gneiss', '71.38k')]

#print(process_image('resources/window.PNG'))
#test()
#test2()