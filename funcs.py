import discord
import asyncio
from classes import dbThing


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
    await send(channel, f"<a:symbol_right:666800714483236864> {text}", **kwargs)


async def send_no(channel, text, **kwargs):
    await send(channel, f"<a:symbol_wrong:666800714991009792> {text}", **kwargs)


def has_perms(message, dbElement):
    return any(role.id in dbElement.perms_roles for role in message.author.roles)


async def warn(message, text):
    try:
        await message.delete()
    except:
        pass

    warning = await message.channel.send(f"{message.author.mention}, {text}!")
    await asyncio.sleep(3)

    try:
        await warning.delete()
    except:
        pass
