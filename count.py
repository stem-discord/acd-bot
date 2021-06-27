import discord
from classes import dbThing, top_messages
from funcs import warn


def ignored(message, dbElement):
    return message.author.id in dbElement.ignored_members or any(role.id in dbElement.ignored_roles for role in message.author.roles)


async def count(message):
    guild_id = message.guild.id
    dbElement = dbThing.get(guild_id)
    if dbElement.channel_id != message.channel.id:
        return

    author_id = message.author.id
    if message.author.bot:
        if not ignored(message, dbElement):
            try:
                await message.delete()
            except:
                pass
        return

    if len(message.mentions):
        if not ignored(message, dbElement):
            await warn(message, "don't try to be sneaky <:thonker:823671837405085706>")
        return

    content = message.content
    if not content.isdecimal():
        if not ignored(message, dbElement):
            await warn(message, "please count")
        return

    #this should prevent the bot from doing weird stuff if people spam counting
    async with dbThing.get_lock(guild_id):
        if author_id == dbElement.last_counter:
            await warn(message, "please count after one another")
            return

        if int(content) != dbElement.count + 1:
            await warn(message, "please count in order")
            return

        dbElement.count += 1
        dbElement.last_counter = author_id
        if str(author_id) in dbElement.ranking_dict:
            dbElement.ranking_dict[str(author_id)] += 1
        else:
            dbElement.ranking_dict[str(author_id)] = 1
        dbElement.ranking_dict = dict(sorted(dbElement.ranking_dict.items(),
                                             key = lambda item: item[1],
                                             reverse = True))
        dbThing[guild_id] = dbElement


async def edit_count(before):
    guild_id = before.guild.id
    dbElement = dbThing.get(guild_id)
    if dbElement.channel_id != before.channel.id:
        return
    
    content = before.content
    if dbElement.count - int(content) < 3:
        await before.channel.purge(limit = [message.id for message in await before.channel.history().flatten()].index(before.id)+1)
        await warn(before, "please don't edit messages")
        dbElement.count = int(content) - 1
        dbThing[guild_id] = dbElement
        return
    
    await warn(before,
               "please don't edit messages",
               delete = False)


def top_embed(dbElement, member, page):
    member_ids = list(dbElement.ranking_dict.keys())[10 * (page - 1):10 * page]
    counts = list(dbElement.ranking_dict.values())[10 * (page - 1):10 * page]
    text = ""
    for i in range(len(member_ids)):
        temp = "left server" if member.guild.get_member(int(member_ids[i])) is None else f"<@{member_ids[i]}>"
        text += f"`{(page-1) * 10 + i + 1}`. {temp} `{counts[i]}`\n"

    member_id = member.id
    temp = f"`{list(dbElement.ranking_dict.values()).index(dbElement.ranking_dict[str(member_id)]) + 1}`. {member.mention} `{dbElement.ranking_dict[str(member_id)]}`" if str(member_id) in dbElement.ranking_dict else ""

    embed = discord.Embed(title = "top counters",
                          description = f"{temp}\n\n{text}")
    embed.set_footer(text = f"{page}/{len(dbElement.ranking_dict) // 10 + 1}")
    return embed


async def count_reaction(reaction, user):
    if user.bot:
        return
    
    message_id = reaction.message.id
    emoji = reaction.emoji
    if message_id in top_messages and emoji in "⏪◀▶⏩":
        dbElement = dbThing.get(reaction.message.guild.id)
        if dbElement is None:
            return

        last_page = len(dbElement.ranking_dict) // 10 + 1
        if emoji == "⏪":
            top_messages[message_id].page = 1
        elif emoji == "◀":
            top_messages[message_id].page = max(1, top_messages[message_id].page - 1)
        elif emoji == "▶":
            top_messages[message_id].page = min(last_page, top_messages[message_id].page + 1)
        else:
            top_messages[message_id].page = last_page
        embed = top_embed(dbElement, top_messages[message_id].member, top_messages[message_id].page)
        await reaction.message.edit(embed = embed)
        await reaction.remove(user)
