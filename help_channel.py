import discord
import asyncio
import os
import requests
import json
from classes import dbThing, bot


def ocr(message):
    formats = ['png', 'jpg', 'jpeg']
    temp = []
    for attachment in message.attachments:
        if any(attachment.filename.endswith(format) for format in formats):
            payload = {"url": attachment.url, "apikey": os.getenv("OCR_KEY")}
            r = requests.post('https://api.ocr.space/parse/image',
                              data = payload)
            
            try:
                temp.extend(json.loads(r.content.decode())["ParsedResults"][0]["ParsedText"].lower().split())
            except:
                pass
    return temp


async def log(message, title):
    channel = bot.get_guild(493173110799859713).get_channel(854918297505759283)

    embed = discord.Embed(title = title, url = message.jump_url)
    embed.add_field(name = "author",
                    value = message.author.mention,
                    inline = False)
    embed.add_field(name = "channel",
                    value = message.channel.mention,
                    inline = False)
    content = message.content
    if len(content):
        embed.add_field(name = "content",
                        value = content,
                        inline = False)
    await channel.send(embed = embed)

    files = []
    for attachment in message.attachments:
        file_name = attachment.filename
        await attachment.save(file_name)
        files.append(discord.File(fp = file_name))
        os.remove(file_name)
    await channel.send(files = files)


async def acd(message):
    dbElement = dbThing.get(message.guild.id)
    if dbElement.acd:
        await message.channel.send(f"{message.author.mention}, academic dishonesty, such as asking for help on a quiz or test, is not allowed.\nUse `?acd` for more information.\n*This action was performed automatically.*")
    
    await log(message, "acd")


async def repost(message):
    dbElement = dbThing.get(message.guild.id)
    for attachment in message.attachments:
        if dbElement.repost: 
            file_name = attachment.filename
            await attachment.save(f"temp/{file_name}")
            for image_name in os.listdir("image_cache"):
                temp = False
                with open(f"temp/{file_name}", "rb") as file1:
                    with open(f"image_cache/{image_name}", "rb") as file2:
                        temp = file1.read() == file2.read()
                if temp:
                    await message.channel.send(f"{message.author.mention}, please don't repost questions.\nSee <#625027300920000542> for guidelines on asking questions.\n*This action was performed automatically.*")
                    os.remove(f"temp/{file_name}")
                    await log(message, "repost")
                    return
            os.rename(f"temp/{file_name}", f"image_cache/{file_name}")
        else:
            await attachment.save(f"image_cache/{file_name}")
    
    await asyncio.sleep(300)

    for attachment in message.attachments:
        try:
            os.remove(f"image_cache/{attachment.filename}")
        except:
            pass


#improve algorithm
def is_acd(message):
    ignore = ["practice", "review", "homework", "hw"]
    flags = ["quiz", "quizzes", "test", "tests", "exam", "exams", "assessment", "assessments"]

    temp = ocr(message)
    return not any(word in temp for word in ignore) and any(word in temp for word in flags)


async def help_channel(message):
    dbElement = dbThing.get(message.guild.id)
    if message.channel.id not in dbElement.help_channel_ids:
        return

    if not len(message.attachments):
        return
    
    if is_acd(message):
        await acd(message)

    await repost(message)
