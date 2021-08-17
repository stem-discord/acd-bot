from discord import *
from discord.ext import commands
from discord_slash import SlashCommand
from discord_slash.context import ComponentContext
from discord_slash.utils.manage_components import *
from random import randint
from os import listdir, remove, getenv
from dotenv import load_dotenv
from count import *
from funcs import *
from help_channel import *

bot = commands.Bot(command_prefix = "$",
                   intents = Intents.all(),
                   help_command = None,
                   case_insensitive = True)
slash = SlashCommand(bot)

@bot.event
async def on_ready():
    print("online")


@bot.event
async def on_message(message):
    await count(message)
    if message.author.bot:
        return

    if message.channel == 839399426643591188:
        pass

    if len(message.attachments):
        await help_channel(bot, slash, message)
    await bot.process_commands(message)


@bot.event
async def on_message_edit(before, after):
    if after.author.bot:
        return

    await edit_count(after)
    await bot.process_commands(after)


@bot.event
async def on_command_error(ctx, error):
    return


#count commands


@bot.command()
@commands.guild_only()
async def top(ctx, member: Member = None):
    if member is None:
        member = ctx.author

    page = 1
    last_page = len(get_db()["leaderboard"]) // 10 + 1
    embed = top_embed(bot, member, page)
    action_row = create_actionrow(create_button(style = 1, emoji = "◀", custom_id = "◀", disabled = True),
                                  create_button(style = 1, emoji = "▶", custom_id = "▶", disabled = True if page == last_page else False))

    await ctx.message.reply(embed = embed, components = [action_row])

    while True:
        button_ctx: ComponentContext = await wait_for_component(bot, components = action_row)

        if button_ctx.custom_id == "◀":
            page -= 1
        else:
            page += 1

        embed = top_embed(bot, member, page)
        action_row = create_actionrow(create_button(style = 1, emoji = "◀", custom_id = "◀", disabled = True if page == 1 else False),
                                      create_button(style = 1, emoji = "▶", custom_id = "▶", disabled = True if page == last_page else False))
        await button_ctx.edit_origin(embed = embed, components = [action_row])


@bot.command()
@commands.guild_only()
async def set_count(ctx, count: int):
    message = ctx.message
    if not has_perms(message.author):
        await react_no(message)
        return

    db = get_db()
    db["count"] = count
    save_db(db)

    await react_yes(message)


#help channel commands


@bot.command()
@commands.guild_only()
async def add_help_channel(ctx, channels: commands.Greedy[TextChannel]):
    message = ctx.message
    if not has_perms(message.author):
        await react_no(message)
        return

    db = get_db()
    for channel in channels:
        if channel.id not in db["help_channel_ids"]:
            db["help_channel_ids"].append(channel.id)
    save_db(db)

    await react_yes(message)


@bot.command()
@commands.guild_only()
async def remove_help_channel(ctx, channels: commands.Greedy[TextChannel]):
    message = ctx.message
    if not has_perms(message.author):
        await react_no(message)
        return

    db = get_db()
    for channel in channels:
        if channel.id in db["help_channel_ids"]:
            db["help_channel_ids"].remove(channel.id)
    save_db(db)

    await react_yes(message)


@bot.command()
@commands.guild_only()
async def help_channels(ctx):
    db = get_db()
    embed = Embed(title = "help channels", description = "\n".join([f"<#{id}>" for id in db["help_channel_ids"]]))
    await ctx.message.reply(embed = embed)


@bot.command()
@commands.guild_only()
async def acd(ctx, state):
    message = ctx.message
    if not has_perms(message.author):
        await react_no(message)
        return

    state = state.lower()
    db = get_db()
    if state == "on":
        db["acd"] = True
    elif state == "off":
        db["acd"] = False
    else:
        await react_no(message)
        return
    save_db(db)

    await react_yes(message)


@bot.command()
@commands.guild_only()
async def repost(ctx, state):
    message = ctx.message
    if not has_perms(message.author):
        await react_no(message)
        return

    state = state.lower()
    db = get_db()
    if state == "on":
        db["repost"] = True
    elif state == "off":
        db["repost"] = False
    else:
        await react_no(message)
        return
    save_db(db)

    await react_yes(message)


#utility commands


@bot.command(aliases = ["randomise"])
@commands.guild_only()
async def randomize(ctx):
    guild = bot.get_guild(493173110799859713)
    author = guild.get_member(ctx.author.id)
    message = ctx.message
    if author is None:
        await react_no(message)
        return

    role = guild.get_role(851931290776240208)
    if role not in author.roles:
        await react_no(message)
        return

    await role.edit(color = randint(0, 0xffffff))
    await react_yes(message)
    return


@bot.command()
async def ping(ctx):
    await ctx.message.reply(f"`{int(bot.latency*1000)}` ms")


#dev commands


@bot.command()
@commands.guild_only()
async def dump(ctx):
    await ctx.message.reply(file = File(fp = "db.json"))


@bot.command(name = "eval")
async def _eval(ctx, *, code):
    message = ctx.message
    if ctx.author.id not in dev_ids:
        await react_no(message)
        return

    try:
        temp = eval(code)
    except:
        await react_no(message)
    else:
        with open("eval.txt", "w") as file:
            file.write(str(temp))
        await ctx.message.reply(file = File(fp = "eval.txt"))
        remove("eval.txt")


@bot.command(name = "exec")
async def _exec(ctx, *, code):
    message = ctx.message
    if ctx.author.id not in dev_ids:
        await react_no(message)
        return

    try:
        exec(code)
        await react_yes(message)
    except:
        await react_no(message)


for file_name in listdir("image_cache"):
    remove(f"image_cache/{file_name}")

load_dotenv()
bot.run(getenv("TOKEN"))
