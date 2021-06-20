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
    await send(channel, f"<a:symbol_right:666800714483236864> {text}", **kwargs)


async def send_no(channel, text, **kwargs):
    await send(channel, f"<a:symbol_wrong:666800714991009792> {text}", **kwargs)