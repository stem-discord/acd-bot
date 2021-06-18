import discord
from discord.ext import commands
import asyncio
import copy
from replit import db

dev_ids = [736724275855228930, 444724485594152960, 275322364173221890]
top_messages = {}


class DbElement:
    def __init__(self, channel_id, webhook_id, count, last_counter, ignored_roles, ignored_members, ranking_dict, help_channel_ids):
        self.channel_id = channel_id
        self.webhook_id = webhook_id
        self.count = count
        self.last_counter = last_counter
        self.ignored_roles = list(ignored_roles)
        self.ignored_members = list(ignored_members)
        self.ranking_dict = dict(ranking_dict)
        self.help_channel_ids = list(help_channel_ids)

    @classmethod
    def from_db_element(cls, element):
        return cls(*element)

    def to_db_element(self):
        return (self.channel_id, self.webhook_id, self.count, self.last_counter, self.ignored_roles, self.ignored_members, self.ranking_dict, self.help_channel_ids)


class DbElementWithLock:
    def __init__(self, dbElement):
        self.dbElement = dbElement
        self.lock = asyncio.Lock()


class Something:  #idk what to call this
    def __init__(self, db):
        self.db = db
        self._cache = {}

    def __getitem__(self, key):
        if str(key) not in self._cache:
            self._cache[str(key)] = DbElementWithLock(DbElement.from_db_element(self.db[str(key)]))
        return copy.deepcopy(self._cache[str(key)].dbElement)

    def __setitem__(self, key, val):
        if str(key) not in self._cache:
            self._cache[str(key)] = DbElementWithLock(val)
        else:
            self._cache[str(key)].dbElement = copy.deepcopy(val)
        self.db[str(key)] = val.to_db_element()

    def __delitem__(self, key):
        del self._cache[str(key)]
        del self.db[str(key)]

    def get(self, key):
        dbElement = self.db.get(str(key))
        if dbElement is None:
            return None
        if str(key) not in self._cache:
            self._cache[str(key)] = DbElementWithLock(DbElement.from_db_element(dbElement))
        return copy.deepcopy(self._cache[str(key)].dbElement)

    def get_lock(self, key):
        dbElement = self.db.get(str(key))
        if dbElement is None:
            return None
        if str(key) not in self._cache:
            self._cache[str(key)] = DbElementWithLock(DbElement.from_db_element(dbElement))
        return self._cache[str(key)].lock

    def keys(self):
        return self.db.keys()


class TopMessagesElement:
    def __init__(self, page, member):
        self.page = page
        self.member = member


dbThing = Something(db) #very bad name, must fix

bot = commands.Bot(command_prefix = '$',
                   intents = discord.Intents.all(),
                   help_command = None,
                   case_insensitive = True)