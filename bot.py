import discord

import item_ids
import price_checker
from discord.ext import commands

from utils import get_price_from_line, is_valid_price_definition_line, get_nearest_string_from_list, \
    get_int_from_suffix_number, is_valid_suffixed_number

DISCORD_TOKEN = 'DISCORD_TOKEN_HERE'
DISCORD_GUILD = ''
BOT_CHANNELS = ['bot-testbed', 'corp-buy-back-bot']

bot = commands.Bot(command_prefix='$')


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(bot.guilds)

    channel = discord.utils.get(bot.get_all_channels(), guild__name='Untitled Gaming', name='corp-buy-back-ores')
    async for message in channel.history(limit=10):
        if 'ORE BUYBACK PRICES' in message.content and message.author.discriminator == '8509' and message.author.name == 'RebelKeithy':
            optional = [' Alloy', ' Compound', ' Metals', ' Composite']
            lines = message.content.splitlines()
            for line in lines:
                if is_valid_price_definition_line(line):
                    name, price = get_price_from_line(line)
                    price_checker.update_price(name, price, name)
                    for opt in optional:
                        if opt in name:
                            short_name = name.replace(opt, '')
                            price_checker.update_price(short_name, price, name)

            price_checker.update_price('Ochre', price_checker.get_price('Dark Ochre'), 'Dark Ochre')


@bot.command(name='buybackbeta')
async def test(ctx, *, arg: str):
    if ctx.channel.name not in BOT_CHANNELS:
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
async def test(ctx, *, arg: str):
    if ctx.channel.name not in BOT_CHANNELS:
        print(ctx.channel)
        return
    print(f"[buyback]: {arg}")

    def local_value_function(item):
        matching_item = get_nearest_string_from_list(item, price_checker.all_items())
        price = int(price_checker.get_price(matching_item))
        return price_checker.get_display_name(matching_item), price

    message = calculate_buyback_prices_controller(arg, local_value_function)
    print(message)
    await ctx.send(message)


def process_args_into_item_volume_pairs(args):
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
        raise ValueError(f"No price for item {original_name}.")

    return pairs


def calculate_buyback_prices_controller(arg, price_function):
    arg = arg.replace(",", " ")  # If someone uses comma separated values, we will convert to space separated

    try:
        pairs = process_args_into_item_volume_pairs(arg)
    except ValueError as e:
        print(f"Invalid args: {arg}")
        return f"I don't understand. {e}"

    invalid_items = []
    prices = []
    for item, amount, original in pairs:
        try:
            name, price = price_function(item)
            prices.append((name, price * amount))
        except ValueError as e:
            print(f"Exception: {e}")
            invalid_items.append(original)

    if invalid_items:
        message = ", ".join(invalid_items[:-2] + [" and ".join(invalid_items[-2:])])
        message += " are " if len(invalid_items) > 1 else " is "
        message += "not available in the buy back program   "
    elif len(prices) == 1:
        message = f"Total contract price for {prices[0][0]} is {prices[0][1]:,} isk\n"
    else:
        message = ''.join([f"{p[0]}: {p[1]:,}\n" for p in prices])
        message += f"Total contract price is {sum(p[1] for p in prices):,} isk"

    return message


bot.run(DISCORD_TOKEN)
