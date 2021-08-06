from asyncio import sleep
from json import *

dev_ids = {736724275855228930, 444724485594152960, 275322364173221890, 341446613056880641}
role_ids = {536996925581295627, 534923363748151301, 643287653344870400}


async def react_yes(message):
    await message.add_reaction("<a:symbol_right:666800714483236864>")


async def react_no(message):
    await message.add_reaction("<a:symbol_wrong:666800714991009792>")


def has_perms(member):
    return member.id in dev_ids or any(role.id in role_ids for role in member.roles)


async def warn(message, content, delete = True):
    if delete:
        try:
            await message.delete()
        except:
            pass

    message = await message.channel.send(f"{message.author.mention}, {content}!")

    await sleep(3)
    try:
        await message.delete()
    except:
        pass


def get_db():
    with open("db.json") as file:
        data = load(file)
        return data


def save_db(db):
    with open("db.json", "w") as file:
        dump(db, file)
