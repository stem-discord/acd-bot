import discord
from discord.ext import commands
from replit import db
import asyncio
import typing
import os
import random
import copy
import requests
import json
#import logging

#set up logging
#maybe change this to logging.WARNING if it's too spammy
#logging.basicConfig(level=logging.INFO)

#db format
#db[guild id] = [channel id, webhook id, count, last counter, [ignored roles], [ignored members], {member id: times counted}, [help channel ids]]

bot = commands.Bot(command_prefix = '$',
                   intents = discord.Intents.all(),
                   help_command = None,
                   case_insensitive = True)

dev_ids = [736724275855228930, 444724485594152960, 275322364173221890]

top_messages = {}


class DbElement:
    def __init__(self, channel_id, webhook_id, count, last_counter, ignored_roles, ignored_members, ranking_dict, help_channel_ids):
        self.channel_id = channel_id
        self.webhook_id = webhook_id
        self.count = count
        self.last_counter = last_counter
        self.ignored_roles = list(ignored_roles)
        self.ignored_members = list(ignored_members)
        self.ranking_dict = dict(ranking_dict)
        self.help_channel_ids = list(help_channel_ids)

    @classmethod
    def from_db_element(cls, element):
        return cls(*element)

    def to_db_element(self):
        return (self.channel_id, self.webhook_id, self.count, self.last_counter, self.ignored_roles, self.ignored_members, self.ranking_dict, self.help_channel_ids)


class DbElementWithLock:
    def __init__(self, dbElement):
        self.dbElement = dbElement
        self.lock = asyncio.Lock()


class Something: #idk what to call this
    def __init__(self, db):
        self.db = db
        self._cache = {}

    def __getitem__(self, key):
        if str(key) not in self._cache:
            self._cache[str(key)] = DbElementWithLock(DbElement.from_db_element(self.db[str(key)]))
        return copy.deepcopy(self._cache[str(key)].dbElement)

    def __setitem__(self, key, val):
        if str(key) not in self._cache:
            self._cache[str(key)] = DbElementWithLock(val)
        else:
            self._cache[str(key)].dbElement = copy.deepcopy(val)
        self.db[str(key)] = val.to_db_element()

    def __delitem__(self, key):
        del self._cache[str(key)]
        del self.db[str(key)]

    def get(self, key):
        dbElement = self.db.get(str(key))
        if dbElement is None:
            return None
        if str(key) not in self._cache:
            self._cache[str(key)] = DbElementWithLock(DbElement.from_db_element(dbElement))
        return copy.deepcopy(self._cache[str(key)].dbElement)

    def get_lock(self, key):
        dbElement = self.db.get(str(key))
        if dbElement is None:
            return None
        if str(key) not in self._cache:
            self._cache[str(key)] = DbElementWithLock(DbElement.from_db_element(dbElement))
        return self._cache[str(key)].lock

    def keys(self):
        return self.db.keys()


dbThing = Something(db) #very bad name, must fix


class TopMessagesElement:
    def __init__(self, page, member):
        self.page = page
        self.member = member


async def warn(message, text):
    try:
        await message.delete()
    except discord.errors.NotFound:
        pass

    warning = await message.channel.send(f"{message.author.mention}, {text}!")

    await asyncio.sleep(3)
    try:
        await warning.delete()
    except discord.errors.NotFound:
        pass


async def send(channel, text, **kwargs):
    message = await channel.send(text, **kwargs)

    dbElement = dbThing.get(channel.guild.id)
    if dbElement.channel_id != channel.id:
        return message

    await asyncio.sleep(3)
    try:
        await message.delete()
    except discord.errors.NotFound:
        pass

    return message


async def send_yes(channel, text, **kwargs):
    await send(channel, f"<a:yes:820523959878418452> {text}", **kwargs)


async def send_no(channel, text, **kwargs):
    await send(channel, f"<a:no:820524004594024459> {text}", **kwargs)


def has_ignored_role(message, dbElement):
    return any(role.id in dbElement.ignored_roles for role in message.author.roles)


def top_embed(dbElement, member, page):
    member_ids = list(dbElement.ranking_dict.keys())[10 * (page - 1):10 * page]
    counts = list(dbElement.ranking_dict.values())[10 * (page - 1):10 * page]
    temp = ""
    for i in range(len(member_ids)):
        temp += f"`{(page - 1) * 10 + i + 1}`. <@{member_ids[i]}>: `{counts[i]}`\n"

    embed = discord.Embed(
        title="top counters",
        description=
        f"`{list(dbElement.ranking_dict.values()).index(dbElement.ranking_dict[str(member.id)])+1 if str(member.id) in dbElement.ranking_dict else -1}`. {member.mention}: `{dbElement.ranking_dict[str(member.id)] if str(member.id) in dbElement.ranking_dict else 0}`\n\n{temp}")
    embed.set_footer(text=f"page {page}/{len(dbElement.ranking_dict) // 10 + 1}")
    return embed


def ocr(message):
    formats=['png', 'jpg', 'jpeg']
    temp = []
    for attachment in message.attachments:
      if any(attachment.filename.endswith(image) for image in formats):
        payload = {"url" : attachment.url,
                   "isOverlayRequired": False,
                   "apikey": "cc3f28cc3d88957",
                   "language": "eng"}
        r = requests.post('https://api.ocr.space/parse/image', data = payload)
        try:
            temp.extend(json.loads(r.content.decode())["ParsedResults"][0]["ParsedText"].lower().split())
        except:
            pass
    return temp


@bot.event
async def on_ready():
    print("online")


@bot.event
async def on_guild_join(guild):
    dbThing[guild.id] = DbElement(None, None, 0, None, [], dev_ids, {})


async def counting(message):
    dbElement = dbThing.get(message.guild.id)
    if dbElement.channel_id != message.channel.id:
        return

    if message.webhook_id is not None:
        return

    if message.author.bot:
        if message.author.id not in dbElement.ignored_members:
            try:
                await message.delete()
            except discord.errors.NotFound:
                pass
        return

    if len(message.mentions):
        if message.author.id not in dbElement.ignored_members and not has_ignored_role(
                message, dbElement):
            await warn(
                message,
                "don't think you are sneaky <:thonker:823671837405085706>")
        return

    if not message.content.isdecimal():
        if message.author.id not in dbElement.ignored_members and not has_ignored_role(
                message, dbElement):
            await warn(message, "please count")
        return

    #this should prevent the bot from doing weird stuff if people spam counting
    async with dbThing.get_lock(message.guild.id):
        if message.author.id == dbElement.last_counter:
            await warn(message, "please count after one another")
            return

        if int(message.content) != dbElement.count + 1:
            await warn(message, "please count in order")
            return

        try:
            await message.delete()
        except discord.errors.NotFound:
            pass

        webhook = await bot.fetch_webhook(dbElement.webhook_id)
        await webhook.send(content = message.content,
                           username = message.author.display_name,
                           avatar_url = message.author.avatar_url)

        dbElement.count += 1
        dbElement.last_counter = message.author.id
        if str(message.author.id) in dbElement.ranking_dict:
            dbElement.ranking_dict[str(message.author.id)] += 1
        else:
            dbElement.ranking_dict[str(message.author.id)] = 1
        dbElement.ranking_dict = dict(sorted(dbElement.ranking_dict.items(),
                                             key = lambda item: item[1],
                                             reverse = True))
        dbThing[message.guild.id] = dbElement


async def log_acd(message):
    #maybe actually don't hard code stuff
    channel = message.guild.get_channel(854918297505759283)
    files = []
    for attachment in message.attachments:
        await attachment.save(attachment.filename)
        files.append(discord.File(fp = attachment.filename))
        os.remove(attachment.filename)
    await channel.send(f"{message.author.mention} sent in {message.channel.mention}:\n{message.content}", files = files)


async def repost(message):
    for attachment in message.attachments:
        await attachment.save(attachment.filename)
        for file_name in os.listdir("images"):
            if open(attachment.filename,"rb").read() == open(f"images/{file_name}","rb").read():
                await message.channel.send(f"{message.author.mention}, please don't repost questions\n*this action was perfomed automatically*")
                os.remove(attachment.filename)
                return
        os.rename(attachment.filename, f"images/{attachment.filename}")
    await asyncio.sleep(300)
    for attachment in message.attachments:
        os.remove(f"images/{attachment.filename}")


async def acd(message):
    dbElement = dbThing.get(message.guild.id)
    if message.channel.id not in dbElement.help_channel_ids:
        return

    if message.author.bot:
        return

    ignore = ["practice", "review"]

    flags = ["quiz", "quizzes", "test", "tests", "exam", "exams", "assessment", "assessments"]

    temp = message.content.lower().split()
    if "help" in temp:
        for word in ignore:
            if word in temp:
                return

        for word in flags:
            if word in temp:
                await message.channel.send(f"{message.author.mention}, academic dishonesty, such as asking for help on a quiz or test, is not allowed\n*this action was perfomed automatically*")
                await log_acd(message)
                await repost(message)
                return

    if not len(message.attachments):
        return
    
    temp = ocr(message)

    for word in ignore:
        if word in temp:
            return

    for word in flags:
        if word in temp:
            await message.channel.send(f"{message.author.mention}, academic dishonesty, such as asking for help on a quiz or test, is not allowed\n*this action was perfomed automatically*")
            await log_acd(message)
            await repost(message)
            return

    await repost(message)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await counting(message)
    await acd(message)
    if not message.author.bot:
        await bot.process_commands(message)


@bot.event
async def on_message_edit(before, after):
    if not after.author.bot:
        await bot.process_commands(after)


@bot.event
async def on_reaction_add(reaction, user):
    if reaction.message.id in top_messages and reaction.emoji in "⏪⬅️➡️⏩" and reaction.me and reaction.count == 2:
        id = reaction.message.id
        dbElement = dbThing.get(reaction.message.guild.id)
        if dbElement is None:
            return
        member = top_messages[id].member
        if reaction.emoji == "⏪":
            top_messages[id].page = 1
        elif reaction.emoji == "⬅️":
            top_messages[id].page = max(1, top_messages[id].page - 1)
        elif reaction.emoji == "➡️":
            top_messages[id].page = min(len(dbElement.ranking_dict) // 10 + 1, top_messages[id].page + 1)
        else:
            top_messages[id].page = len(dbElement.ranking_dict) // 10 + 1
        embed = top_embed(dbElement, member, top_messages[id].page)
        await reaction.message.edit(embed=embed)
        await reaction.remove(user)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    else:
        print(error)
        await send_no(ctx.channel, "an error occured")


"""
def close_to_red(color):
    threshold = 0x100  #maybe change this threshold
    red_offset = 0xff - (color >> 16)
    green_offset = (color & 0x00ff00) >> 8
    blue_offset = color & 0x0000ff
    return red_offset**2 + green_offset**2 + blue_offset**2 < threshold
"""


@bot.command()
@commands.guild_only()
async def randomize(ctx):
    if ctx.guild.id == 493173110799859713:
        role = ctx.guild.get_role(851931290776240208)
        if role in ctx.author.roles:
            color = random.randint(0, 0xffffff)
            await role.edit(color=color)
            await send_yes(ctx.channel, "color randomized")
        else:
            await send_no(ctx.channel, "missing permissions")


@bot.command()
@commands.guild_only()
async def top(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    dbElement = dbThing.get(ctx.guild.id)
    if dbElement.channel_id is None:
        await send_no(ctx.channel, "no counting channel")
        return

    embed = top_embed(dbElement, member, 1)
    message = await send(ctx.channel, "", embed=embed)

    await message.add_reaction("⏪")
    await message.add_reaction("⬅️")
    await message.add_reaction("➡️")
    await message.add_reaction("⏩")
    
    top_messages[message.id] = TopMessagesElement(1, member)


@bot.command()
@commands.guild_only()
async def start_count(ctx,
                      channel: typing.Optional[discord.TextChannel] = None,
                      count: int = None):
    if ctx.author.id in dev_ids:
        if channel is None:
            channel = ctx.channel
        dbElement = dbThing.get(ctx.guild.id)

        webhook = await channel.create_webhook(name = channel.name)

        dbElement.channel_id = channel.id
        dbElement.webhook_id = webhook.id
        if count is not None:
            dbElement.count = count
        dbThing[ctx.guild.id] = DbElement

        await send_yes(ctx.channel, f"count started in {channel.mention} at `{count}`")
    else:
        await send_no(ctx.channel, "missing permissions")


@bot.command()
@commands.guild_only()
async def set_count(ctx, count: int):
    if ctx.author.id in dev_ids:
        dbElement = dbThing.get(ctx.guild.id)
        if dbElement.channel_id is None:
            await send_no(ctx.channel, "no counting channel")
            return

        dbElement.count = count
        dbThing[ctx.guild.id] = dbElement

        await send_yes(ctx.channel, f"count set to `{count}`")
    else:
        await send_no(ctx.channel, "missing permissions")


@bot.command()
@commands.guild_only()
async def ignore(ctx,
                 roles: commands.Greedy[discord.Role] = [],
                 members: commands.Greedy[discord.Member] = []):
    if ctx.author.id in dev_ids:
        if len(roles) or len(members):
            dbElement = dbThing.get(ctx.guild.id)
            if dbElement.channel_id is None:
                await send_no(ctx.channel, "no counting channel")
                return

            for role in roles:
                if role.id not in dbElement.ignored_roles:
                    dbElement.ignored_roles.append(role.id)
            for member in members:
                if member.id not in dbElement.ignored_members:
                    dbElement.ignored_members.append(member.id)
            dbThing[ctx.guild.id] = dbElement

            await send_yes(
                ctx.channel,
                f"{' '.join([role.mention for role in roles])} {' '.join([member.mention for member in members])} {'were' if len(roles) + len(members) > 1 else 'was'} ignored", 
                allowed_mentions=discord.AllowedMentions.none())
    else:
        await send_no(ctx.channel, "missing permissions")


@bot.command()
@commands.guild_only()
async def unignore(ctx,
                   roles: commands.Greedy[discord.Role] = [],
                   members: commands.Greedy[discord.Member] = []):
    if ctx.author.id in dev_ids:
        if len(roles) or len(members):
            dbElement = dbThing.get(ctx.guild.id)
            if dbElement.channel_id is None:
                await send_no(ctx.channel, "no counting channel")
                return

            for role in roles:
                if role.id in dbElement.ignored_roles:
                    dbElement.ignored_roles.remove(role.id)
            for member in members:
                if member.id in dbElement.ignored_members:
                    dbElement.ignored_members.remove(member.id)
            dbThing[ctx.guild.id] = dbElement

            await send_yes(
                ctx.channel,
                f"{' '.join([role.mention for role in roles])} {' '.join([member.mention for member in members])} {'were' if len(roles) + len(members) > 1 else 'was'} unignored",
                allowed_mentions=discord.AllowedMentions.none())
    else:
        await send_no(ctx.channel, "missing permissions")


@bot.command()
@commands.guild_only()
async def count_info(ctx):
    if ctx.author.id in dev_ids:
        guild = ctx.guild

        dbElement = dbThing.get(guild.id)
        if dbElement.channel_id is None:
            await send_no(ctx.channel, "no counting channel")
            return
    
        ignored_roles = " ".join([f"<@&{role_id}>" for role_id in dbElement.ignored_roles])
        ignored_members = " ".join([f"<@{member_id}>" for member_id in dbElement.ignored_members])
        embed = discord.Embed(title = "count info", 
                              description = f"channel: <#{dbElement.channel_id}>\n"
                                            f"webhook id: `{dbElement.webhook_id}`\n"
                                            f"count: `{dbElement.count}`\n"
                                            f"last counter: <@{dbElement.last_counter}>\n"
                                            f"ignored roles: {ignored_roles}\n"
                                            f"ignored members: {ignored_members}")

        await send(ctx.channel, "", embed = embed)
    else:
        await send_no(ctx.channel, "missing permissions")


@bot.command()
async def image_to_text(ctx):
    await send(ctx.channel, ' '.join(ocr(ctx.message)))


@bot.command()
async def image_to_text_raw(ctx):
    await send(ctx.channel, f"```{ocr(ctx.message)}```")


@bot.command()
@commands.guild_only()
async def add_help_channel(ctx, channels: commands.Greedy[discord.TextChannel]):
    if ctx.author.id in dev_ids:
        dbElement = dbThing.get(ctx.guild.id)

        for channel in channels:
            if channel.id not in dbElement.help_channel_ids:
                dbElement.help_channel_ids.append(channel.id)
        dbThing[ctx.guild.id] = dbElement

        await send_yes(ctx.channel, f"added {' '.join([channel.mention for channel in channels])}")
    else:
        await send_no(ctx.channel, "missing permissions")


@bot.command()
@commands.guild_only()
async def remove_help_channel(ctx, channels: commands.Greedy[discord.TextChannel]):
    if ctx.author.id in dev_ids:
        dbElement = dbThing.get(ctx.guild.id)

        for channel in channels:
            if channel.id in dbElement.help_channel_ids:
                dbElement.help_channel_ids.remove(channel.id)
        dbThing[ctx.guild.id] = dbElement

        await send_yes(ctx.channel, f"removed {' '.join([channel.mention for channel in channels])}")
    else:
        await send_no(ctx.channel, "missing permissions")


@bot.command()
@commands.guild_only()
async def help_channels(ctx):
    if ctx.author.id in dev_ids:
        dbElement = dbThing.get(ctx.guild.id)
        embed = discord.Embed(title = 'help channels', description = "\n".join([f"<#{id}>" for id in dbElement.help_channel_ids]))
        await send(ctx.channel, "", embed = embed)
    else:
        await send_no(ctx.channel, "missing permissions")


@bot.command(name='eval')
async def _eval(ctx, *, text):
    if ctx.author.id in dev_ids:
        try:
            await send(ctx.channel, f"```py\n{eval(text)}```")
        except Exception as exception:
            await send(ctx.channel, f"```\n{exception}```")
        except:
            #don't log warnings
            pass
    else:
        await send_no(ctx.channel, "missing permissions")


@bot.command(name='exec')
async def _exec(ctx, *, text):
    if ctx.author.id in dev_ids:
        try:
            exec(text)
            await send_yes(ctx.channel, "executed")
        except Exception as exception:
            await send(ctx.channel, f"```\n{exception}```")
        except:
            #don't log warnings
            pass
    else:
        await send_no(ctx.channel, "missing permissions")


bot.run(os.getenv('TOKEN'))
