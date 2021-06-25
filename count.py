import discord
from classes import dbThing, top_messages
from funcs import warn


def has_ignored_role(message, dbElement):
    return any(role.id in dbElement.ignored_roles for role in message.author.roles)


async def count(message):
    dbElement = dbThing.get(message.guild.id)
    if dbElement.channel_id != message.channel.id:
        return

    if message.author.bot:
        if message.author.id not in dbElement.ignored_members and not has_ignored_role(message, dbElement):
            try:
                await message.delete()
            except:
                pass
        return

    if len(message.mentions):
        if message.author.id not in dbElement.ignored_members and not has_ignored_role(message, dbElement):
            await warn(message, "don't think you are sneaky <:thonker:823671837405085706>")
        return

    if not message.content.isdecimal():
        if message.author.id not in dbElement.ignored_members and not has_ignored_role(message, dbElement):
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


async def edit_count(before):
    dbElement = dbThing.get(before.guild.id)
    if dbElement.channel_id != before.channel.id:
        return
    
    if dbElement.count - int(before.content) < 3:
        await before.channel.purge(limit = [message.id for message in await before.channel.history().flatten()].index(before.id)+1)
        await warn(before, "please don't edit messages")
        dbElement.count = int(before.content) - 1
        dbThing[before.guild.id] = dbElement
    else:
        await warn(before,
                   "please don't edit messages",
                   delete = False)


def top_embed(dbElement, member, page):
    member_ids = list(dbElement.ranking_dict.keys())[10 * (page-1):10 * page]
    counts = list(dbElement.ranking_dict.values())[10 * (page-1):10 * page]
    text = ""
    for i in range(len(member_ids)):
        temp = "left server" if member.guild.get_member(int(member_ids[i])) is None else f"<@{member_ids[i]}>"
        text += f"`{(page-1) * 10 + i+1}`. {temp} `{counts[i]}`\n"

    temp = f"`{list(dbElement.ranking_dict.values()).index(dbElement.ranking_dict[str(member.id)])+1}`. {member.mention} `{dbElement.ranking_dict[str(member.id)]}`" if str(member.id) in dbElement.ranking_dict else ""

    embed = discord.Embed(title = "top counters",
                          description = f"{temp}\n\n{text}")
    embed.set_footer(text = f"{page}/{len(dbElement.ranking_dict) // 10 + 1}")
    return embed


async def count_reaction(reaction, user):
    if reaction.message.id in top_messages and reaction.emoji in "⏪◀️▶️⏩" and reaction.me and reaction.count == 2:
        id = reaction.message.id
        dbElement = dbThing.get(reaction.message.guild.id)
        if dbElement is None:
            return
        member = top_messages[id].member
        if reaction.emoji == "⏪":
            top_messages[id].page = 1
        elif reaction.emoji == "◀️":
            top_messages[id].page = max(1, top_messages[id].page - 1)
        elif reaction.emoji == "▶️":
            top_messages[id].page = min(len(dbElement.ranking_dict) // 10 + 1, top_messages[id].page + 1)
        else:
            top_messages[id].page = len(dbElement.ranking_dict) // 10 + 1
        embed = top_embed(dbElement, member, top_messages[id].page)
        await reaction.message.edit(embed = embed)
        await reaction.remove(user)
