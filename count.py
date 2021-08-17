from discord import *
from funcs import *


async def count(message):
    channel = message.channel
    if channel.id != 638690281910173697:
        return

    author = message.author
    if author.bot:
        if has_perms(author):
            return

        try:
            await message.delete()
        except:
            pass
        return

    content = message.content
    if not content.isdecimal():
        if has_perms(author):
            return

        await warn(message, "please count")
        return

    db = get_db()
    if author.id == db["last_counter_id"]:
        await warn(message, "please count after one another")
        return

    if int(content) != db["count"] + 1:
        await warn(message, "please count in order")
        return

    db["count"] += 1
    db["last_counter_id"] = author.id
    if str(author.id) in db["leaderboard"]:
        db["leaderboard"][str(author.id)] += 1
    else:
        db["leaderboard"][str(author.id)] = 1
    db["leaderboard"] = dict(sorted(db["leaderboard"].items(), key = lambda temp: temp[1], reverse = True))
    save_db(db)


async def edit_count(after):
    if after.channel.id != 638690281910173697:
        return

    await warn(after, "please don't edit messages", delete = False)


def top_embed(bot, member, page):
    db = get_db()
    member_ids = list(db["leaderboard"].keys())[10 * (page - 1):10 * page]
    counts = list(db["leaderboard"].values())[10 * (page - 1):10 * page]
    guild = bot.get_guild(493173110799859713)
    leaderboard = ""
    for i in range(len(member_ids)):
        temp = "left server" if guild.get_member(int(member_ids[i])) is None else f"<@{member_ids[i]}>"
        leaderboard += f"`{(page-1) * 10 + i + 1}`. {temp} `{counts[i]}`\n"

    temp = f"`{list(db['leaderboard'].values()).index(db['leaderboard'][str(member.id)]) + 1}`. {member.mention} \
             `{db['leaderboard'][str(member.id)]}`" if str(member.id) in db["leaderboard"] else ""

    embed = Embed(title = "top counters", description = f"{temp}\n\n{leaderboard}")
    embed.set_footer(text = f"{page}/{len(db['leaderboard']) // 10 + 1}")
    return embed
