from collections import namedtuple
from multiprocessing.pool import Pool

import discord
import typing

import item_ids
import price_checker
from discord.ext import commands

from template_matcher import process_image
from utils import get_price_from_line, is_valid_price_definition_line, get_nearest_string_from_list, \
    get_int_from_suffix_number, is_valid_suffixed_number

DISCORD_TOKEN = 'DISCORD_TOKEN_HERE'
DISCORD_GUILD = ''
BOT_CHANNELS_WHITELIST = ['bot-testbed', 'corp-buy-back-bot']
PRICE_MESSAGE_SERVER = 'Untitled Gaming'
PRICE_MESSAGE_CHANNEL = 'corp-buy-back-materials'

NameValue = namedtuple('NameValue', ['name', 'value'])
bot = commands.Bot(command_prefix='$', help_command=None)

INVALID_ITEMS = []
MINERALS = ['Tritanium', 'Pyerite', 'Mexallon', 'Isogen', 'Nocxium', 'Zydrine', 'Megacyte', 'Morphite']
ORES = ['Veldspar', 'Scordite', "Pyroxeres", 'Plagioclase', 'Omber', 'Kernite', 'Jaspet', 'Hemorphite', 'Hedbergite', 'Spodumain', 'Dark Ochre', 'Gneiss', 'Crokite', 'Bistot', 'Arkonor', 'Mercoxit']
PLANETARY = ["Lustering Alloy", "Sheen Compound", "Gleaming Alloy", "Condensed Alloy", "Precious Alloy", "Motley Compound", "Fiber Composite", "Lucent Compound", "Opulent Compound", "Glossy Compound", "Crystal Compound", "Dark Compound", "Base Metals", "Heavy Metals", "Reactive Metals", "Noble Metals", "Toxic Metals", "Reactive Gas", "Noble Gas", "Industrial Fibers", "Supertensile Plastics", "Polyaramids", "Coolant", "Condensates", "Construction Blocks", "Nanites", "Silicate Glass", "Smartfab Units", "Heavy Water", "Suspended Plasma", "Liquid Ozone", "Ionic Solutions", "Oxygen Isotopes", "Plasmoids"]

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(bot.guilds)

    channel = discord.utils.get(bot.get_all_channels(), guild__name=PRICE_MESSAGE_SERVER, name=PRICE_MESSAGE_CHANNEL)
    async for message in channel.history(limit=100):
        if 'ORE BUYBACK PRICES' in message.content and message.author.discriminator == '8509' and message.author.name == 'RebelKeithy':
            optional = [' Alloy', ' Compound', ' Metals', ' Composite']
            lines = message.content.splitlines()
            for line in lines:
                line = line.replace(",", "")
                if is_valid_price_definition_line(line):
                    name, price = get_price_from_line(line)
                    price_checker.update_price(name, price, name)
                    for opt in optional:
                        if opt in name:
                            short_name = name.replace(opt, '')
                            price_checker.add_alias(short_name, name)

            price_checker.add_alias('Ochre', 'Dark Ochre')
            price_checker.add_alias("spod", "Spodumain")
            price_checker.add_alias('mex', 'Mexallon')
            for invalid_item in INVALID_ITEMS:
                price_checker.add_invalid_item(invalid_item, invalid_item)

@bot.command(name='help')
async def help(ctx):
    message = "```Buyback Bot Commands\n\n"
    message += "$buyback item amount ...\n"
    message += "   Calculates the buyback price for the items listed\n\n"
    message += "$buybackprices [ore|planetary]\n"
    message += "   Lists the current buyback prices for all items or the specified items\n\n"
    message += "$marketcheck [ore|planetary]\n"
    message += "   Checks the market prices for all items or the specified items.\n"
    message += "   Note: the prices fetched are not guaranteed to be accurate\n"
    message += "   Note: currently only works for ores```"
    await ctx.send(message)

@bot.command(name='updatecheck')
async def update_check(ctx, item_type: typing.Optional[str] = ""):
    if item_type != "planetary":
        prices = []
        for ore in ORES:
            price = price_checker.get_price_online(item_ids.item_ids[ore])
            prices.append((ore, int(price * 0.8 + 0.5)))
        message = '\n'.join(f"{name} {price}" for name, price in prices)
        await ctx.send(f"```{message}```")
    else:
        await ctx.send("Market prices for planetary items is not supported at this time")

@bot.command(name='marketcheck')
async def market_prices(ctx, item_type: typing.Optional[str] = ""):
    if item_type != "planetary":
        prices = []
        for ore in ORES:
            price = price_checker.get_price_online(item_ids.item_ids[ore])
            prices.append((ore, int(price)))
        message = '\n'.join(f"{name} {price}" for name, price in prices)
        await ctx.send(f"```{message}```")
    else:
        await ctx.send("Market prices for planetary items is not supported at this time")


@bot.command(name='syncprices')
async def sync_prices(ctx):
    if ctx.author.discriminator == '8509' and ctx.author.name == 'RebelKeithy':
        for ore in ORES:
            price = price_checker.get_price_online(item_ids.item_ids[ore])
            price_checker.update_price(ore, int(price * 0.8), ore)
    await ctx.send("Prices have been updated to market value")


@bot.command(name='buybackprices')
async def buyback_prices(ctx, item_type: typing.Optional[str] = ""):
    if item_type not in ["ore", "planetary", "mineral", ""]:
        await ctx.send("Only ore, mineral and planetary are available.")
        return

    message = ""
    if item_type == "ore" or item_type == "":
        prices = []
        for ore in ORES:
            price = price_checker.get_price(ore)
            prices.append((ore, int(price)))
        ore_message = '\n'.join(f"{name} {price}" for name, price in prices)
        message += f"ORE PRICES\n```{ore_message}```\n"

    if item_type != "planetary" or item_type == "":
        prices = []
        for planetary in PLANETARY:
            price = price_checker.get_price(planetary)
            prices.append((planetary, int(price)))
        planetary_message = '\n'.join(f"{name} {price}" for name, price in prices)
        message += f"PLANETARY PRICES\n```{planetary_message}```\n"

    if item_type != "mineral" or item_type == "":
        prices = []
        for mineral in MINERALS:
            price = price_checker.get_price(mineral)
            prices.append((mineral, float(price)))
        mineral_message = '\n'.join(f"{name} {price}" for name, price in prices)
        message += f"MINERAL PRICES\n```{mineral_message}```\n"

    await ctx.send(message)


@bot.command(name='buybackbeta')
async def test(ctx, *, arg: str):
    if ctx.channel.name not in BOT_CHANNELS_WHITELIST:
        print(ctx.channel)
        return
    print(f"[buybackbeta]: {arg}")

    def online_value_function(item):
        matching_item = get_nearest_string_from_list(item, item_ids.item_ids.keys())
        matching_id = item_ids.item_ids[matching_item]
        price = int(price_checker.get_price_online(matching_id) * 0.8)
        return matching_item, price

    message = calculate_buyback_prices_controller(arg, online_value_function)
    print(message)
    await ctx.send(message)


@bot.command(name='buyback')
async def test(ctx, *, arg: typing.Optional[str] = ""):
    if ctx.channel.name not in BOT_CHANNELS_WHITELIST:
        print(ctx.channel)
        return
    print(f"[buyback]: {arg}")

    if ctx.message.attachments:
        image_url = ctx.message.attachments[0]
        print(image_url)
        await ctx.message.attachments[0].save("download.png")
        amounts = process_image("download.png")
        message = '\n'.join(f"{ore} {amount}" for ore, amount in amounts)
        await ctx.send(f"```{message}```")
        arg = " ".join(f"{ore} {amount}" for ore, amount in amounts)

    def local_value_function(item):
        matching_item = get_nearest_string_from_list(item, price_checker.all_items())
        price = price_checker.get_price(matching_item)
        return price_checker.get_display_name(matching_item), price

    message = calculate_buyback_prices_controller(arg, local_value_function)
    print(message)
    await ctx.send(message)


def process_args_into_item_volume_pairs(args):
    for i in range(2, len(args) - 3):
        if args[i-2:i+1].isalpha() and args[i+1:i+4].isdigit():
            args = args[:i+1] + ' ' + args[i+1:]

    args = args.split()
    pairs = []
    name = ""
    original_name = ""
    for arg in args:
        if arg.isalpha():
            name += arg.lower()
            original_name += arg + " "
        elif is_valid_suffixed_number(arg):
            amount = get_int_from_suffix_number(arg)
            pairs.append((name, amount, original_name.strip()))
            name = ""
            original_name = ""
        else:
            raise ValueError(f"{arg} is not a name or number.")

    if name != "":
        raise ValueError(f"No amount for item {original_name}.")

    return pairs


def calculate_buyback_prices_controller(arg, price_function):
    arg = arg.replace(", ", "")  # If someone uses comma separated values, we will convert to space separated
    arg = arg.replace(",", "")  # If someone uses comma separated values, we will convert to space separated

    try:
        pairs = process_args_into_item_volume_pairs(arg)
    except ValueError as e:
        print(f"Invalid args: {arg}")
        return f"I don't understand. {e}"

    invalid_items = []
    prices = []
    for item, amount, original in pairs:
        try:
            name, value = (price_function(item))
            prices.append(NameValue(name, value * amount))
        except ValueError as e:
            print(f"Exception: {e}")
            invalid_items.append(original)

    if invalid_items:
        message = ", ".join(invalid_items[:-2] + [" and ".join(invalid_items[-2:])])
        message += " are " if len(invalid_items) > 1 else " is "
        message += "not available in the buy back program."
    elif len(prices) == 1:
        message = f"Total contract price for {prices[0].name} is {prices[0].value:,} isk\n"
    else:
        message = ''.join([f"{p.name}: {p.value:,}\n" for p in prices])
        message += f"Total contract price is {sum(p.value for p in prices):,} isk"

    return message


bot.run(DISCORD_TOKEN)
