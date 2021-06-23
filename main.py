import discord
from discord.ext import commands
from replit import db
import asyncio
import typing
import os
import fuckit
from classes import DbElement, TopMessagesElement, dbThing, bot, dev_ids, top_messages
from count import count, top_embed, count_reaction
from funcs import send, send_yes, send_no, has_perms
from help_channel import ocr, help_channel


@bot.event
async def on_ready():
    print("online")


@bot.event
async def on_guild_join(guild):
    dbThing[guild.id] = DbElement(None, None, 0, None, [], dev_ids, {}, [], False, False)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await count(message)
    await help_channel(message)
    if not message.author.bot:
        await bot.process_commands(message)


@bot.event
async def on_message_edit(before, after):
    if not after.author.bot:
        await bot.process_commands(after)


@bot.event
async def on_reaction_add(reaction, user):
    await count_reaction(reaction, user)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    else:
        print(error)
        await send_no(ctx.channel, "an error occured")


#count commands


@bot.command()
@commands.guild_only()
async def top(ctx,
              member: discord.Member = None):
    if member is None:
        member = ctx.author

    dbElement = dbThing.get(ctx.guild.id)
    if dbElement.channel_id is None:
        await send_no(ctx.channel, "no counting channel")
        return

    embed = top_embed(dbElement, member, 1)
    message = await send(ctx.channel,
                         "",
                         embed = embed)

    await message.add_reaction("⏪")
    await message.add_reaction("◀️")
    await message.add_reaction("▶️")
    await message.add_reaction("⏩")

    top_messages[message.id] = TopMessagesElement(1, member)

    await asyncio.sleep(3000)

    await message.clear_reaction("⏪")
    await message.clear_reaction("◀️")
    await message.clear_reaction("▶️")
    await message.clear_reaction("⏩")

    del top_messages[message.id]


@bot.command()
@commands.guild_only()
async def start_count(ctx,
                      channel: typing.Optional[discord.TextChannel] = None,
                      count: int = None):
    dbElement = dbThing.get(ctx.guild.id)
    if not has_perms(ctx.message, dbElement) and ctx.author.id not in dev_ids:
        await send_no(ctx.channel, "missing permissions")
        return

    if channel is None:
        channel = ctx.channel

    dbElement = dbThing.get(ctx.guild.id)
    dbElement.channel_id = channel.id
    dbElement.webhook_id = (await channel.create_webhook(name = channel.name)).id
    if count is not None:
        dbElement.count = count
    dbThing[ctx.guild.id] = DbElement

    await send_yes(ctx.channel, f"count started in {channel.mention} at `{count}`")


@bot.command()
@commands.guild_only()
async def set_count(ctx,
                    count: int):
    dbElement = dbThing.get(ctx.guild.id)
    if not has_perms(ctx.message, dbElement) and ctx.author.id not in dev_ids:
        await send_no(ctx.channel, "missing permissions")
        return

    dbElement = dbThing.get(ctx.guild.id)
    if dbElement.channel_id is None:
        await send_no(ctx.channel, "no counting channel")
        return

    dbElement.count = count
    dbThing[ctx.guild.id] = dbElement

    await send_yes(ctx.channel, f"count set to `{count}`")


@bot.command()
@commands.guild_only()
async def ignore(ctx,
                 roles: commands.Greedy[discord.Role] = [],
                 members: commands.Greedy[discord.Member] = []):
    if ctx.author.id not in dev_ids:
        await send_no(ctx.channel, "missing permissions")
        return

    if not len(roles) and not len(members):
        return

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

    await send_yes(ctx.channel,
                   f"{' '.join([role.mention for role in roles])} {' '.join([member.mention for member in members])} {'were' if len(roles) + len(members) > 1 else 'was'} ignored",
                   allowed_mentions = discord.AllowedMentions.none())


@bot.command()
@commands.guild_only()
async def unignore(ctx,
                   roles: commands.Greedy[discord.Role] = [],
                   members: commands.Greedy[discord.Member] = []):
    if ctx.author.id not in dev_ids:
        await send_no(ctx.channel, "missing permissions")
        return

    if not len(roles) and not len(members):
        return

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

    await send_yes(ctx.channel,
                   f"{' '.join([role.mention for role in roles])} {' '.join([member.mention for member in members])} {'were' if len(roles) + len(members) > 1 else 'was'} unignored",
                   allowed_mentions = discord.AllowedMentions.none())


@bot.command()
@commands.guild_only()
async def count_info(ctx):
    dbElement = dbThing.get(ctx.guild.id)
    if not has_perms(ctx.message, dbElement) and ctx.author.id not in dev_ids:
        await send_no(ctx.channel, "missing permissions")
        return

    dbElement = dbThing.get(ctx.guild.id)
    if dbElement.channel_id is None:
        await send_no(ctx.channel, "no counting channel")
        return

    ignored_roles = " ".join([f"<@&{role_id}>" for role_id in dbElement.ignored_roles])
    ignored_members = " ".join([f"<@{member_id}>" for member_id in dbElement.ignored_members])
    embed = discord.Embed(title = "count info")
    embed.add_field(name = "channel",
                    value = f"<#{dbElement.channel_id}>\n",
                    inline = False)
    embed.add_field(name = "webhook id",
                    value = f"`{dbElement.webhook_id}`",
                    inline = False)
    embed.add_field(name = "count",
                    value = f"`{dbElement.count}`",
                    inline = False)
    embed.add_field(name = "last counter",
                    value = f"<@{dbElement.last_counter}>\n",
                    inline = False)
    embed.add_field(name = "ignored roles",
                    value = ignored_roles,
                    inline = False)
    embed.add_field(name = "ignored members",
                    value = ignored_members,
                    inline = False)

    await send(ctx.channel,
               "",
               embed = embed)


#help channel commands


@bot.command()
@commands.guild_only()
async def add_help_channel(ctx,
                           channels: commands.Greedy[discord.TextChannel]):
    dbElement = dbThing.get(ctx.guild.id)
    if not has_perms(ctx.message, dbElement) and ctx.author.id not in dev_ids:
        await send_no(ctx.channel, "missing permissions")
        return

    dbElement = dbThing.get(ctx.guild.id)
    for channel in channels:
        if channel.id not in dbElement.help_channel_ids:
            dbElement.help_channel_ids.append(channel.id)
    dbThing[ctx.guild.id] = dbElement

    await send_yes(ctx.channel, f"added {' '.join([channel.mention for channel in channels])}")


@bot.command()
@commands.guild_only()
async def remove_help_channel(ctx,
                              channels: commands.Greedy[discord.TextChannel]):
    dbElement = dbThing.get(ctx.guild.id)
    if not has_perms(ctx.message, dbElement) and ctx.author.id not in dev_ids:
        await send_no(ctx.channel, "missing permissions")
        return

    dbElement = dbThing.get(ctx.guild.id)
    for channel in channels:
        if channel.id in dbElement.help_channel_ids:
            dbElement.help_channel_ids.remove(channel.id)
    dbThing[ctx.guild.id] = dbElement

    await send_yes(ctx.channel, f"removed {' '.join([channel.mention for channel in channels])}")


@bot.command()
@commands.guild_only()
async def help_channels(ctx):
    dbElement = dbThing.get(ctx.guild.id)
    if not has_perms(ctx.message, dbElement) and ctx.author.id not in dev_ids:
        await send_no(ctx.channel, "missing permissions")
        return

    dbElement = dbThing.get(ctx.guild.id)
    embed = discord.Embed(title = "help channels",
                          description = "\n".join([f"<#{id}>" for id in dbElement.help_channel_ids]))

    await send(ctx.channel,
               "",
               embed = embed)


@bot.command()
@commands.guild_only()
async def acd(ctx,
              text = None):
    dbElement = dbThing.get(ctx.guild.id)
    if not has_perms(ctx.message, dbElement) and ctx.author.id not in dev_ids:
        await send_no(ctx.channel, "missing permissions")
        return
    
    dbElement = dbThing.get(ctx.guild.id)
    if text == None:
        dbElement.acd = not dbElement.acd
    else:
        text = text.lower()
        if text == "enable":
            dbElement.acd = True
        elif text == "disable":
            dbElement.acd = False
        else:
            return
    dbThing[ctx.guild.id] = dbElement

    await send_yes(ctx.channel, f"acd {'enabled' if dbElement.acd else 'disabled'}")


@bot.command()
@commands.guild_only()
async def repost(ctx,
                 text = None):
    dbElement = dbThing.get(ctx.guild.id)
    if not has_perms(ctx.message, dbElement) and ctx.author.id not in dev_ids:
        await send_no(ctx.channel, "missing permissions")
        return
    
    dbElement = dbThing.get(ctx.guild.id)
    if text == None:
        dbElement.repost = not dbElement.repost
    else:
        text = text.lower()
        if text == "enable":
            dbElement.repost = True
        elif text == "disable":
            dbElement.repost = False
        else:
            return
    dbThing[ctx.guild.id] = dbElement

    await send_yes(ctx.channel, f"repost {'enabled' if dbElement.acd else 'disabled'}")


#moderation commands


@bot.command()
@commands.guild_only()
async def hide_channel(ctx,
                       channels: commands.Greedy[discord.TextChannel] = [],
                       roles: commands.Greedy[discord.Role] = [],
                       members: commands.Greedy[discord.Member] = []):
    dbElement = dbThing.get(ctx.guild.id)
    if not has_perms(ctx.message, dbElement) and ctx.author.id not in dev_ids:
        await send_no(ctx.channel, "missing permissions")
        return
    
    if not len(channels):
        channels = [ctx.channel]
    if not len(roles) and not len(members):
        roles = [ctx.guild.default_role]

    for channel in channels:
        overwrites = channel.overwrites
        if len(roles):
            for role in roles:
                overwrite = channel.overwrites_for(role)
                overwrite.view_channel = False
                overwrites[role] = overwrite
        if len(members):
            for member in members:
                overwrite = channel.overwrites_for(member)
                overwrite.view_channel = False
                overwrites[member] = overwrite
        await channel.edit(overwrites = overwrites)

    await send_yes(ctx.channel,
                   f"{' '.join([channel.mention for channel in channels])} {'was' if len(channels) == 1 else 'were'} hidden from {' '.join([role.mention for role in roles])} {' '.join([member.mention for member in members]) if len(members) else ''}",
                   allowed_mentions = discord.AllowedMentions.none())


@bot.command()
@commands.guild_only()
async def purge(ctx,
                channels: commands.Greedy[discord.TextChannel] = [],
                members: commands.Greedy[discord.Member] = [],
                num: int = None):
    if num == None:
        return
    if not len(channels):
        channels = [ctx.channel]

    try:
        await ctx.message.delete()
    except:
        pass

    if len(members):
        for channel in channels:
            for member in members:
                await channel.purge(limit = num,
                                    check = lambda message: message.author == member)
        return

    for channel in channels:
        await channel.purge(limit = num)


#utility commands


@bot.command()
async def image_to_text(ctx):
    await send(ctx.channel, " ".join(ocr(ctx.message)))


@bot.command()
@commands.guild_only()
async def members(ctx,
                  role: discord.Role):
    dbElement = dbThing.get(ctx.guild.id)
    if not has_perms(ctx.message, dbElement) and ctx.authorctx.author.id not in dev_ids:
        await send_no(ctx.channel, "missing permissions")
        return

    temp = "\n".join([member.mention for member in role.members])
    await send(ctx.channel,
               f"members in {role.mention}\n{temp}",
               allowed_mentions = discord.AllowedMentions.none())


#dev commands


@bot.command()
@commands.guild_only()
async def perms(ctx,
                roles: commands.Greedy[discord.Role]):
    if ctx.author.id not in dev_ids:
        await send_no(ctx.channel, "missing permissions")
        return

    if not len(roles):
        return

    dbElement = dbThing.get(ctx.guild.id)
    for role in roles:
        if role.id not in dbElement.perms_roles:
            dbElement.perms_roles.append(role.id)
    dbThing[ctx.guild.id] = dbElement

    await send_yes(ctx.channel,
                   f"{' '.join([role.mention for role in roles])} {'were' if len(roles) > 1 else 'was'} given perms",
                   allowed_mentions = discord.AllowedMentions.none())


@bot.command()
@commands.guild_only()
async def remove_perms(ctx,
                       roles: commands.Greedy[discord.Role]):
    if ctx.author.id not in dev_ids:
        await send_no(ctx.channel, "missing permissions")
        return

    if not len(roles):
        return

    dbElement = dbThing.get(ctx.guild.id)
    for role in roles:
        if role.id not in dbElement.perms_roles:
            dbElement.perms_roles.remove(role.id)
    dbThing[ctx.guild.id] = dbElement

    await send_yes(ctx.channel,
                   f"removed perms from {' '.join([role.mention for role in roles])}",
                   allowed_mentions = discord.AllowedMentions.none())


@bot.command(name="eval")
async def _eval(ctx, *, text):
    if ctx.author.id not in dev_ids:
        await send_no(ctx.channel, "missing permissions")
        return

    try:
        await send(ctx.channel, f"```py\n{eval(text)}```")
    except Exception as exception:
        await send(ctx.channel, f"```\n{exception}```")


@bot.command(name="exec")
async def _exec(ctx, *, text):
    if ctx.author.id not in dev_ids:
        await send_no(ctx.channel, "missing permissions")
        return

    try:
        exec(text)
        await send_yes(ctx.channel, "executed")
    except Exception as exception:
        await send(ctx.channel, f"```\n{exception}```")


#clear image_cache before running
for file_name in os.listdir("image_cache"):
	os.remove(f"image_cache/{file_name}")

bot.run(os.getenv("TOKEN"))
