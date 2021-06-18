import discord
import os
import asyncio
import requests
import json
from classes import dbThing, bot


def ocr(message):
    formats = ['png', 'jpg', 'jpeg']
    temp = []
    for attachment in message.attachments:
        if any(attachment.filename.endswith(image) for image in formats):
            payload = {"url": attachment.url,
                       "isOverlayRequired": False,
                       "apikey": "cc3f28cc3d88957",
                       "language": "eng"}
            r = requests.post('https://api.ocr.space/parse/image', data = payload)
            try:
                temp.extend(json.loads(r.content.decode())["ParsedResults"][0]["ParsedText"].lower().split())
            except:
                pass
    return temp


async def acd(message):
    await message.channel.send(f"{message.author.mention}, academic dishonesty, such as asking for help on a quiz or test, is not allowed.\nUse `?acd` for more information.\n*this action was perfomed automatically.*")
    #maybe actually don't hard code stuff
    channel = bot.get_guild(493173110799859713).get_channel(854918297505759283)
    files = []
    for attachment in message.attachments:
        await attachment.save(attachment.filename)
        files.append(discord.File(fp = attachment.filename))
        os.remove(attachment.filename)
    await channel.send(f"{message.author.mention} sent in {message.channel.mention}:\n{message.content}",
                       files = files)


async def repost(message):
    for attachment in message.attachments:
        await attachment.save(attachment.filename)
        for file_name in os.listdir("images"):
            is_repost = False
            with open(attachment.filename, "rb") as f1:
                with open(f"images/{file_name}", "rb") as f2:
                    is_repost = f1.read() == f2.read()
            if is_repost:
                await message.channel.send(f"{message.author.mention}, please don't repost questions.\nSee <#625027300920000542> for guidelines on posting questions.\n*this action was perfomed automatically.*")
                os.remove(attachment.filename)
                return
        os.rename(attachment.filename, f"images/{attachment.filename}")
    await asyncio.sleep(300)
    for attachment in message.attachments:
        try:
            os.remove(f"images/{attachment.filename}")
        except:
            pass


async def help_channel(message):
    dbElement = dbThing.get(message.guild.id)
    if message.channel.id not in dbElement.help_channel_ids:
        return

    if message.author.bot:
        return

    ignore = ["practice", "review", "homework", "hw"]

    flags = ["quiz", "quizzes", "test", "tests", "exam", "exams", "assessment", "assessments"]

    temp = message.content.lower().split()
    if "help" in temp:
        for word in ignore + ["not", "aren't"]:
            if word in temp:
                return

        for word in flags:
            if word in temp:
                await acd(message)
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
            await acd(message)
            await repost(message)
            return

    await repost(message)
