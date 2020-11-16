from random import random, choice

import jellyfish

from cache import Cache

valid_suffixes = {
    'k': 1000,
    'm': 1000000
}

uuids = Cache('utils-uuids')
uuids.data['set'] = uuids.data.get('set', set())


def is_valid_price_definition_line(line):
    words = line.split()
    print(words)
    if len(words) <= 1:
        return False
    if not words[-1].replace(".", "").isdigit():
        return False
    if not all(word.isalpha() for word in words[:-1]):
        return False
    return True


def get_price_from_line(line):
    words = line.split()
    price = float(words[-1])
    name = " ".join(words[:-1])
    return name, price


def is_valid_suffixed_number(string):
    string = string.replace(",", "")
    string = string.replace(".", "")
    if len(string) == 1:
        return string.isdigit()
    else:
        return string[:-1].isdigit() and (string[-1].isdigit() or string[-1] in valid_suffixes.keys())


def get_int_from_suffix_number(string):
    multiplier = 1
    if string[-1] in valid_suffixes.keys():
        multiplier = valid_suffixes[string[-1]]
        string = string[:-1]
    decimal_places = 0
    if '.' in string:
        decimal_places = len(string) - string.index(".") - 1
    string = string.replace(",", "")
    string = string.replace(".", "")
    base_number = int(string)
    return int(base_number * multiplier / pow(10, decimal_places))


def get_nearest_string_from_list(string, string_list, threshold=0.75):
    matching_item = None
    closest_dist = threshold
    for list_item in string_list:
        dist = jellyfish.jaro_winkler_similarity(string.lower(), list_item.lower())
        if dist > closest_dist:
            matching_item = list_item
            closest_dist = dist
        print(f"    {string} {list_item} {dist}")

    if matching_item is None:
        print("No Match Found.")
        raise ValueError()
    print(f"Match: {string} {matching_item} {closest_dist}")
    return matching_item, closest_dist


def valid_uuid(uuid):
    uuid_set = uuids.data.get('set', set())
    if uuid in uuid_set:
        return False

    filtered = ['SEX', 'GAY']
    if any(uuid.startswith(word) for word in filtered):
        return False
    return True


def generate_uuid():
    vowels = ['A', 'E', 'I', 'O', 'U']
    consonants = ['B', 'C', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'X', 'Y', 'Z']
    uuid = f"{choice(consonants)}{choice(vowels)}{choice(consonants)}-{int(random() * 1000)}"
    while not valid_uuid(uuid):
        uuid = f"{choice(consonants)}{choice(vowels)}{choice(consonants)}-{int(random() * 1000)}"
    uuids.data.get('set', set()).add(uuid)
    uuids.save()
    file = ''
    file += 'a'

    return uuid

def get_discord_name(ctx):
    return f"{ctx.author.name}#{ctx.author.discriminator}"