import logging
import re
import os
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='logs/discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

import sys, traceback
import config
import discord
import praw
import time
import threading
import asyncio
import app.models as models
from html import unescape
from concurrent import futures
from datetime import datetime, timezone
from playhouse.shortcuts import model_to_dict, dict_to_model
from multiprocessing import Process, Queue
from peewee import *


client = discord.Client()
update_queue = Queue()
logger.info("Starting reddit client")
reddit = praw.Reddit(user_agent="RedditNotify (by /u/" + config.REDDIT_USERNAME + ")",
                 client_id=config.REDDIT_CLIENT_ID, client_secret=config.REDDIT_CLIENT_SECRET)
logger.info("Reddit client started")

def delete_channels(entry_id):
        try:
            models.Whitelist.delete().where(models.Whitelist.subscription_id == entry_id).execute()
            models.Blacklist.delete().where(models.Blacklist.subscription_id == entry_id).execute()
            models.Subscription.delete().where(models.Subscription.id == entry_id).execute()
        except Exception as e:
            logger.error(traceback.format_exc())

async def send_message(submission, guild_id, channel_id, entry_id, author):
    try:
        prefix = "/r/" + submission.subreddit.display_name + " - "
        message = discord.Embed(title = prefix + submission.title[:256-len(prefix)], url = "https://reddit.com" + submission.permalink, colour=0x0099ff)
        if hasattr(submission, 'preview') == True:
            if 'images' in submission.preview:
                preview_image_link = unescape(submission.preview['images'][0]['source']['url'])
                message.set_thumbnail(url=preview_image_link)
        elif hasattr(submission, 'thumbnail') == True:
            if submission.thumbnail_height == None:
                message.set_thumbnail(url="https://bcs.dev/static/self.png")
            else:
                message.set_thumbnail(url=submission.thumbnail)
        message.set_author(name='RedditNotify', icon_url='https://www.redditinc.com/assets/images/site/reddit-logo.png')
        message.add_field(name="Author", value=submission.author.name)
        message.add_field(name="Subreddit", value=submission.subreddit.display_name)
        if hasattr(submission, 'link_flair_text') == True and submission.link_flair_text != None:
            message.add_field(name="Flair", value=submission.link_flair_text)
        message.add_field(name="Submission Date", value=datetime.fromtimestamp(submission.created_utc).astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'))
        if guild_id == None:
            user = client.get_user(int(author))
            await user.send(embed=message)
        else:
            guild = client.get_guild(int(guild_id))
            channel = guild.get_channel(int(channel_id))
            if channel == None:
                delete_channels(entry_id)
                return
            await channel.send(embed=message)
    except Exception as e:
        logger.error(traceback.format_exc())

def filter(fil, submission, regex):
    term = fil.keyword_type
    if hasattr(submission, term) == True:
        if regex:
            try:
                if ((term == 'title' and re.search(fil.keyword.lower(), submission.title.lower())) or \
                (term == 'author' and re.search(fil.keyword.lower(), submission.author.name.lower())) or \
                (type(getattr(submission,term)) == str and re.search(fil.keyword.lower(), getattr(submission,term).lower()))):
                    return True
            except:
                logger.error("REGEX ERROR: " + fil.keyword + "|" + submission.title)
        else:
            if ((term == 'title' and fil.keyword.lower() in submission.title.lower()) or \
                (term == 'author' and fil.keyword.lower() == submission.author.name.lower()) or \
                (type(getattr(submission,term)) == str and fil.keyword.lower() in getattr(submission,term).lower())):
                return True
    return False

def check_submission(submission):
    try:
        subreddit_name = submission.subreddit.display_name.lower()
        for guild_sub in models.Subscription.select().where(models.Subscription.subreddit == subreddit_name):
            whitelist_true = False
            blacklist_true = False
            filter_count = 0
            blacklist_count = 0
            whitelist_count = 0
            # whitelist
            for wl in models.Whitelist.select().where(models.Whitelist.subscription_id == guild_sub.id):
                whitelist_count += 1
                filter_count += 1
                whitelist_true_tmp = filter(wl, submission, wl.regex)
                whitelist_true = whitelist_true_tmp | whitelist_true
                if wl.required and not whitelist_true_tmp:
                    whitelist_true = False
                    break
            # blacklist
            for bl in models.Blacklist.select().where(models.Blacklist.subscription_id == guild_sub.id):
                blacklist_count += 1
                filter_count += 1
                blacklist_true = filter(bl, submission, wl.regex)
                if blacklist_true:
                    break
            nsfw = guild_sub.nsfw
            nsfw_allow = True
            if nsfw == 'block' and submission.over_18 == True:
                nsfw_allow = False
            elif nsfw == 'only' and submission.over_18 == False:
                nsfw_allow = False
            if (filter_count == 0 or (whitelist_true and not blacklist_true)) or (blacklist_count > 0 and (not blacklist_true and (whitelist_true or whitelist_count == 0))) and nsfw_allow:
                asyncio.run_coroutine_threadsafe(send_message(submission, guild_sub.guild_id, guild_sub.channel_id, guild_sub.id, guild_sub.entry_author), client.loop)
    except Exception as e:
        logger.error(traceback.format_exc())

def get_subreddit_list():
    subreddit_list = ""
    for guild_sub in models.Subscription.select(models.Subscription.subreddit).distinct():
        if(len(subreddit_list)):
            subreddit_list += '+'+guild_sub.subreddit
        else:
            subreddit_list += guild_sub.subreddit
    return subreddit_list

def reddit_do(update_queue):
    subreddit_list = ""
    last_modified = None
    while(True):
        init_time = start_time = time.time()
        try:
            if not len(subreddit_list):
                subreddit_list = "all"
            subreddit = reddit.subreddit(subreddit_list)
            start_time = time.time()
            for submission in subreddit.stream.submissions(pause_after=0):
                last_modified_new = os.path.getmtime('rnbot.db')
                if last_modified_new != last_modified:
                    subreddit_list = get_subreddit_list()
                    last_modified = last_modified_new
                    break
                if submission is not None:
                    if submission.created_utc < start_time:
                        continue
                    t = threading.Thread(target=check_submission, args = (submission,))
                    t.start()
        except Exception as e:
            logger.error(traceback.format_exc())
            


@client.event
async def on_ready():
    logger.info('We have logged in as {0.user}'.format(client))

if __name__ == '__main__':
    models.Guild.create_table(True)
    models.User.create_table(True)
    models.Subscription.create_table(True)
    models.Whitelist.create_table(True)
    models.Blacklist.create_table(True)
    try:
        t = threading.Thread(target=reddit_do, args = (update_queue,))
        t.start()
        client.run(config.DISCORD_BOT_TOKEN)
    except Exception as e:
        logger.critical(traceback.format_exc())