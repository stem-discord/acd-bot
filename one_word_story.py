from replit import db
from classes import bot
from funcs import warn
import re


def validation(s):
    # no multi
    if ('\n' in s):
        return False

    # simple no special character check
    if (not re.match("^[A-Za-z\"\'\-“‟”’]{1,16}$", s)):
        return False

    # the string will allow a 'string or 'string' but not string'
    if (s.startswith("'") - s.endswith("'") < 0):
        return False

    s = re.sub("[\"\'\-“‟”’]", '', s)

    # capitalization
    # removed due to proper nouns such as ToysRUs
    # if (not re.match("[A-Z]?[a-z]*$", s)):
    #     return False
    # if (not re.match("[A-Z]+|[a-z]+", s)):
    #     return False

    # check for obvious spam by measuring constant length
    if (re.match("[^aeiouy]{6,}", s)):
        return False

    return True


async def one_word_story(message):
    global last_person
    
    if message.channel.id != 857913632599572490:
        return

    if message.author.bot:
      return

    if not validation(message.content):
        await warn(message, "please type one word")
        return

    if message.author.id == db['last_person']:
        await warn(message, "please type after one another")
        return
    
    bot.story_list = [x.content for x in await message.channel.history().flatten()][::-1]
    db['last_person'] = message.author.id


async def edit_story(after):
    if after.channel.id != 857913632599572490:
        return
    
    last_message = (await after.channel.history(limit = 1).flatten())[0]
    if after == last_message:
        await last_message.delete()
        await warn(after, "please don't edit messages")
        bot.story_list = [x.content for x in await after.channel.history().flatten()][::-1]
        db['last_person'] = (await after.channel.history(limit = 1).flatten())[0].author.id
        return
    
    await warn(after,
               "please don't edit messages",
               delete = False)
