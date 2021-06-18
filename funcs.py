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
    except:
        pass

    return message


async def send_yes(channel, text, **kwargs):
    await send(channel, f"<a:yes:820523959878418452> {text}", **kwargs)


async def send_no(channel, text, **kwargs):
    await send(channel, f"<a:no:820524004594024459> {text}", **kwargs)