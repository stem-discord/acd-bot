from discord import *
from discord_slash import SlashCommand
from discord_slash.context import ComponentContext
from discord_slash.utils.manage_components import *
from asyncio import sleep
from os import remove, listdir, rename
import requests
from json import loads
from funcs import *


def ocr(message):
    formats = ("png", "jpg", "jpeg")
    temp = []
    for attachment in message.attachments:
        if any(attachment.filename.endswith(format) for format in formats):
            payload = {"url": attachment.url, "apikey": "429cfbc1f588957"}
            r = requests.post("https://api.ocr.space/parse/image", data = payload)

            try:
                temp.extend(loads(r.content.decode())["ParsedResults"][0]["ParsedText"].lower().split())
            except:
                pass
    return temp


async def log(bot, message, title):
    channel = bot.get_guild(493173110799859713).get_channel(854918297505759283)

    embed = Embed(title = title, url = message.jump_url)
    embed.add_field(name = "author", value = message.author.mention, inline = False)
    embed.add_field(name = "channel", value = message.channel.mention, inline = False)
    content = message.content
    if len(content):
        embed.add_field(name = "content", value = content, inline = False)
    temp = await channel.send(embed = embed)

    files = []
    for attachment in message.attachments:
        file_name = attachment.filename
        await attachment.save(file_name)
        files.append(File(fp = file_name))
        remove(file_name)
    await channel.send(files = files)

    return temp, embed


async def acd(bot, slash, message):
    emoji = await bot.get_guild(493173110799859713).fetch_emoji(666800714991009792)
    action_row = create_actionrow(create_button(style = 4, emoji = emoji))
    content = (f"{message.author.mention}, academic dishonesty, such as asking for help on a quiz or test, is not allowed.\n"
               "Use `?acd` for more information.\n"
               "*This action was performed automatically.*")
    await message.channel.send(content, components = [action_row])

    temp, embed = await log(bot, message, "acd")

    button_ctx: ComponentContext = await wait_for_component(bot, components = action_row)

    await button_ctx.edit_origin(components = None)

    embed.color = 0xe74c3c
    await temp.edit(embed = embed)


async def repost(bot, message):
    attachments = message.attachments
    author = message.author
    channel = message.channel
    for attachment in attachments:
        file_name = attachment.filename
        await attachment.save(f"temp/{file_name}")
        for image_name in listdir("image_cache"):
            image_author_id, image_channel_id, temp = image_name.split()
            if author.id == int(image_author_id) and channel.id != int(image_channel_id):
                if open(f"temp/{file_name}", "rb").read() == open(f"image_cache/{image_name}", "rb").read():
                    try:
                        await message.delete()
                    except:
                        pass

                    await channel.send(f"{author.mention}, please don't repost questions.\n"
                                        "See <#625027300920000542> for guidelines on asking questions.\n"
                                        "*This action was performed automatically.*")

                    await log(bot, message, "repost")
                    return
        rename(f"temp/{file_name}", f"image_cache/{author.id} {channel.id} {file_name}")

    await sleep(60)

    for attachment in attachments:
        try:
            remove(f"image_cache/{author.id} {channel.id} {attachment.filename}")
        except:
            pass


def is_acd(message):
    ignore = ("practice", "review", "homework", "hw", "ap")
    flags = ("quiz", "quizzes", "exam", "exams", "assessment", "assessments")

    temp = ocr(message)
    return not any(ignored in temp for ignored in ignore) and any(flag in temp for flag in flags)


async def help_channel(bot, slash, message):
    db = get_db()
    if message.channel.id not in db["help_channel_ids"]:
        return

    if db["acd"] and is_acd(message):
        await acd(bot, slash, message)

    if db["repost"]:
        await repost(bot, message)
