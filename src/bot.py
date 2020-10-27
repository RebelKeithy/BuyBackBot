import asyncio
import time
from collections import namedtuple, Counter
import os

import typing

import google_sheets
from Contract import Contract
from cache import Cache
from constants import DISCORD_API_KEY_ENV, ORES, MINERALS, BOT_CHANNELS_WHITELIST, PLANETARY, OFFICERS, \
    MINERAL_THRESHOLDS
from price_checker import PriceChecker
import item_ids
from discord.ext import commands

from src.template_matcher import process_image
from src.utils import get_nearest_string_from_list, get_int_from_suffix_number, is_valid_suffixed_number, generate_uuid, \
    get_discord_name

try:
    import dotenv
    dotenv.load_dotenv()
except Exception as e:
    print(f"Could not load dotevn {e}")

bot = commands.Bot(command_prefix='$', help_command=None)
NameValue = namedtuple('NameValue', ['name', 'value', 'amount', 'price'])

price_checker = PriceChecker()
ship_prices = PriceChecker()
ship_market_price = PriceChecker()
last_update = 0

contracts = Cache('bot-contracts')
accepted_contracts = Cache('bot-accepted-contracts')
price_overrides = Cache('bot-price-overrides')

def run():
    bot.run(os.environ[DISCORD_API_KEY_ENV])

    update_prices()
    price_checker.add_alias('ochre', 'Dark Ochre')
    price_checker.add_alias("spod", "Spodumain")
    price_checker.add_alias('mex', 'Mexallon')

    items = price_checker.all_items()
    for name in items:
        if name.startswith('Datacore - '):
            alias = name.replace('Datacore - ', '')
            price_checker.add_alias(alias, name)


def update_if_expired():
    global last_update
    if time.time() > last_update + 6 * 60 * 60:
        update_prices()


def update_prices():
    global last_update
    google_sheets.load_prices(price_checker)
    google_sheets.load_ship_prices(ship_prices, ship_market_price)
    last_update = time.time()

    #price_checker.update_price("Reactive Gas", 300, "Reactive Gas")

    print(f"Overrides: {price_overrides.data}")
    for item, price in price_overrides.data.items():
        price_checker.update_price(item, price, item)

    message = ""
    for item, value in MINERAL_THRESHOLDS.items():
        if price_checker.get_price(item) > value:
            message = f'overpriced {item} {price_checker.get_price(item)}\n'

    if message:
        for guild in bot.guilds:
            for channel in guild.channels:
                if channel.name in BOT_CHANNELS_WHITELIST:
                    asyncio.ensure_future(channel.send("<@263603997108076546>\n" + message))


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(bot.guilds)


@bot.command(name='help')
async def help(ctx):
    message = "```Buyback Bot Commands\n\n"
    message += "$buyback item amount ...\n"
    message += "   Alias: bb\n"
    message += "   Calculates the buyback price for the items listed\n\n"
    message += "$buybackprices [(item)|ore|mineral|planetary]\n"
    message += "   Alias: bbp\n"
    message += "   Lists the current buyback prices for all items or the specified items\n\n"
    message += "$pricecheck ship\n"
    message += "   Alias: pc\n"
    message += "   Get the price that UTD will sell ships to alliance members.\n\n"
    message += "```"
    await ctx.send(message)


@bot.command(name='priceoverride')
async def priceoverride(ctx, *, arg: typing.Optional[str] = ""):
    if ctx.channel.name not in BOT_CHANNELS_WHITELIST:
        print(ctx.channel)
        return
    user = get_discord_name(ctx)
    if user not in OFFICERS:
        return
    print(f"[priceoverride]: {arg}")

    pairs = process_args_into_item_volume_pairs(arg)
    for name, amount, original in pairs:
        price_overrides.data[original] = amount
    price_overrides.save()
    update_prices()


@bot.command(name='removeoverride')
async def removeoverride(ctx, *, arg: typing.Optional[str] = ""):
    if ctx.channel.name not in BOT_CHANNELS_WHITELIST:
        print(ctx.channel)
        return
    user = get_discord_name(ctx)
    if user not in OFFICERS:
        return
    print(f"[priceoverride]: {arg}")

    if arg in price_overrides.data.keys():
        del price_overrides.data[arg]
    price_overrides.save()
    update_prices()


@bot.command(name='buybackprices', aliases=['bbp'])
async def buyback_prices(ctx, item_type: typing.Optional[str] = ""):
    update_if_expired()

    try:
        matching_item, certainty = get_nearest_string_from_list(item_type, price_checker.all_items())
        price = int(price_checker.get_price(matching_item))
        message = f"{matching_item} is {price:,} isk"
        await ctx.send(message)
        return
    except ValueError:
        pass

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

    if item_type == "planetary" or item_type == "":
        prices = []
        for planetary in PLANETARY:
            price = price_checker.get_price(planetary)
            prices.append((planetary, int(price)))
        planetary_message = '\n'.join(f"{name} {price}" for name, price in prices)
        message += f"PLANETARY PRICES\n```{planetary_message}```\n"

    if item_type == "mineral" or item_type == "":
        prices = []
        for mineral in MINERALS:
            price = price_checker.get_price(mineral)
            prices.append((mineral, float(price)))
        mineral_message = '\n'.join(f"{name} {price}" for name, price in prices)
        message += f"MINERAL PRICES\n```{mineral_message}```\n"

    await ctx.send(message)


@bot.command(name='pricecheck', aliases=['pc'])
async def pricecheck(ctx, *, arg: typing.Optional[str] = ""):
    if ctx.channel.name not in BOT_CHANNELS_WHITELIST:
        print(ctx.channel)
        return
    print(f"[buyback]: {arg}")

    update_if_expired()

    if 'prostitutes' in arg.lower():
        user = get_discord_name(ctx)
        if user == 'NavyBomber#4895':
            message = 'Do you really need more?'
        else:
            message = "Invalid item Prostitutes. Sorry this item is only available for Frank Lai."
        await ctx.send(message)
        return

    try:
        matching_item, certainty = get_nearest_string_from_list(arg, ship_prices.all_items(), 0)
        invalid_item, invalid_certainty = get_nearest_string_from_list(arg, price_checker.all_items(), 0)
        if invalid_certainty > certainty:
            message = f"The pricecheck command is used to check the price UTD will sell ships to alliance members."
            await ctx.send(message)
            return
    except ValueError:
        pass

    price = ship_prices.get_price(matching_item)
    market_price = ship_market_price.get_price(matching_item)
    message = f"{matching_item} is {int(price):,} isk. Price is {'above' if market_price < price else 'below'} market price"
    await ctx.send(message)


@bot.command(name='accept')
async def accept(ctx, *, arg):
    if ctx.channel.name not in BOT_CHANNELS_WHITELIST:
        print(ctx.channel)
        return
    user = get_discord_name(ctx)
    if user not in OFFICERS:
        return
    print(f"[buyback]: {arg}")

    if arg not in contracts.data.keys():
        message = f"Not a valid contract id"
        await ctx.send(message)
        return
    if arg in accepted_contracts.data.keys():
        message = f"Contract has already been accepted"
        await ctx.send(message)
        return


    discord_user = get_discord_name(ctx)
    contract = contracts.data[arg]
    google_sheets.save_contract(contract, discord_user, arg)
    accepted_contracts.data[arg] = contract
    accepted_contracts.save()
    del contracts.data[arg]
    contracts.save()

    message = f"Contract Accepted"
    await ctx.send(message)
    return


@bot.command(name='stats')
async def stats(ctx, *, arg: typing.Optional[str] = ""):
    if ctx.channel.name not in BOT_CHANNELS_WHITELIST:
        print(ctx.channel)
        return
    print(f"[stats]: {arg}")

    totals = Counter()
    sum = 0
    for id, contract in accepted_contracts.data.items():
        for item in contract.items:
            name, price, amount, value = item
            sum += price
            if name in ORES:
                totals[name] += amount
    message = "Total amount of ore sold through buyback"
    message += '```'
    for item, amount in totals.items():
        message += f"{item:<12} {amount:>12,}\n"
    message += '```'
    message += f'Total isk given through buyback: {int(sum):,}'
    await ctx.send(message)


@bot.command(name='buyback', aliases=['bb'])
async def buyback(ctx, *, arg: typing.Optional[str] = ""):
    if ctx.channel.name not in BOT_CHANNELS_WHITELIST:
        print(ctx.channel)
        return
    print(f"[buyback]: {arg}")

    if ctx.guild.name == 'Untitled Gaming':
        user = get_discord_name(ctx)
        if user not in OFFICERS or True:
            message = "Please use the bot channel in the alliance discord. Check the #eve-announcements channel for more info."
            await ctx.send(message)
            return


    update_if_expired()

    if 'prostitutes' in arg.lower():
        user = get_discord_name(ctx)
        if user == 'NavyBomber#4895':
            message = 'Do you really need more?'
        else:
            message = "Invalid item Prostitutes. Sorry this item is only available for Frank Lai."
        await ctx.send(message)
        return

    if ctx.message.attachments:
        await ctx.message.attachments[0].save("download.png")
        amounts = process_image("download.png")
        image_message = '\n'.join(f"{ore} {amount}" for ore, amount in amounts)
        await ctx.send(f"```{image_message}```")
        arg = " ".join(f"{ore} {amount}" for ore, amount in amounts)

    player = get_discord_name(ctx)
    message = buyback_controller(player, arg)
    await ctx.send(message)


def buyback_controller(player, arg):
    def local_value_function(item):
        matching_item, certainty = get_nearest_string_from_list(item, price_checker.all_items())
        price = price_checker.get_price(matching_item)
        return price_checker.get_display_name(matching_item), price

    message = calculate_buyback_prices_controller(player, arg, local_value_function)
    print(message)
    return message


def custom_is_alpha(s):
    s = s.lower()
    s = s.replace('.', '')
    if s.isalpha(): return True
    if s == '-': return True
    if s.lower().startswith('mk') and len(s) == 3: return True
    if s.lower().startswith('lv'): return True
    if s.lower().startswith('lvl'): return True


def process_args_into_item_volume_pairs(args):
    for i in range(2, len(args) - 3):
        if args[i-2:i+1].isalpha() and args[i+1:i+4].isdigit():
            args = args[:i+1] + ' ' + args[i+1:]

    args = args.split()
    pairs = []
    name = ""
    original_name = ""
    for arg in args:
        if custom_is_alpha(arg):
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


def calculate_buyback_prices_controller(player, arg, price_function):
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
            prices.append(NameValue(name, value * amount, amount, value))
        except ValueError as e:
            print(f"Exception: {e}")
            invalid_items.append(original)

    message = ""
    if not invalid_items:
        uuid = generate_uuid()
        message += f"Contract ID: {uuid}\n"
        contracts.data[uuid] = Contract(player, prices)
        contracts.save()

    if invalid_items:
        message += ", ".join(invalid_items[:-2] + [" and ".join(invalid_items[-2:])])
        message += " are " if len(invalid_items) > 1 else " is "
        message += "not available in the buy back program."
    elif len(prices) == -1:
        message += f"Total contract price for {prices[0].name} is {prices[0].value:,} isk\n"
    else:
        names, values, amounts, item_prices = zip(*prices)
        values = [f"{int(v):,}" for v in values]
        amounts = [f"{int(v):,}" for v in amounts]
        item_prices = [f"{int(v):,}" for v in item_prices]

        names = [s.ljust(max([len(t) for t in names])) for s in names]
        values = [s.rjust(max([len(t) for t in values])) for s in values]
        amounts = [s.rjust(max([len(t) for t in amounts])) for s in amounts]
        item_prices = [s.rjust(max([len(t) for t in item_prices])) for s in item_prices]

        message += "```"
        message += ''.join([f"{name} {amount} * {price} isk: {value}\n" for name, value, amount, price in zip(names, values, amounts, item_prices)])
        message += "```"
        message += f"Total contract price is {sum(p.value for p in prices):,} isk\n"

    return message


def price_update_cron():
    print('cron')
