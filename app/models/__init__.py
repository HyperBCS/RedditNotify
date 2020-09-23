from peewee import *

db = SqliteDatabase('rnbot.db', pragmas={'foreign_keys': 1})

class BaseModel(Model):
    class Meta:
        database = db

class Guild(BaseModel):
    guild_id = TextField(unique=True)

class User(BaseModel):
    user_id = TextField()
    role = TextField()
    guild = ForeignKeyField(Guild)

class Subscription(BaseModel):
    guild_id = TextField(null = True)
    channel_id = TextField(null = True)
    subreddit = TextField()
    entry_author = TextField()
    nsfw = TextField()

class Whitelist(BaseModel):
    keyword = TextField()
    keyword_type = TextField()
    subscription = ForeignKeyField(Subscription)
    regex = IntegerField()
    required = IntegerField()

class Blacklist(BaseModel):
    keyword = TextField()
    keyword_type = TextField()
    subscription = ForeignKeyField(Subscription)
    regex = IntegerField()
    required = IntegerField()