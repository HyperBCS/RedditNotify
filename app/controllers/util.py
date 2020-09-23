import sys,traceback
import requests, re
import config
import app.models as models
from playhouse.shortcuts import model_to_dict, dict_to_model
from app import reddit

def sub_exists(sub):
    exists = True
    try:
        reddit.subreddit(sub).subreddit_type
    except:
        exists = False
    return exists

def get_guild_channels(guild_id):
    url = 'https://discordapp.com/api/v6/guilds/' + guild_id + '/channels'
    headers = {'Authorization': 'Bot '+ config.DISCORD_BOT_TOKEN}
    r = requests.get(url,headers=headers)
    r.raise_for_status()
    return r.json()

def get_guild(guild_id):
    url = 'https://discordapp.com/api/v6/guilds/' + guild_id
    headers = {'Authorization': 'Bot '+ config.DISCORD_BOT_TOKEN}
    r = requests.get(url,headers=headers)
    r.raise_for_status()
    return r.json()

def get_user(user_id):
    url = 'https://discordapp.com/api/v6/users/' + user_id
    headers = {'Authorization': 'Bot '+ config.DISCORD_BOT_TOKEN}
    r = requests.get(url,headers=headers)
    r.raise_for_status()
    return r.json()

def get_user_guilds(token):
    url = 'https://discordapp.com/api/users/@me/guilds'
    headers = {'Authorization': 'Bearer '+token}
    r = requests.get(url,headers=headers)
    r.raise_for_status()
    return r.json()

def get_bot_guilds():
    url = 'https://discordapp.com/api/users/@me/guilds'
    headers = {'Authorization': 'Bot '+ config.DISCORD_BOT_TOKEN}
    r = requests.get(url,headers=headers)
    r.raise_for_status()
    return r.json()

def gen_initials(name):
    final = ""
    past_letter = False
    loop_pass = 0
    for ind, n in enumerate(name):
        if loop_pass > 0:
            loop_pass -= 1
            continue
        if n.isalnum() and not past_letter:
            final += n
            past_letter = True
        elif not n.isalnum():
            if n != " " and n != "'":
                final += n
            elif n == "'" and ind < len(name) - 2:
                name[ind]
                if name[ind+1].isalpha() and name[ind+2] == " ":
                    loop_pass = 2
                else:
                    final += n
            elif n == "'" and ind >= len(name) - 2:
                final += name[ind:]
                break
            past_letter = False
    return final

def filter_owned_guilds(guilds):
	guild_dict = {}
	for g in guilds:
		if g['owner'] == True or (g['permissions'] & 0x20 or g['permissions'] & 0x8):
			guild_dict[g['id']] = g
			guild_dict[g['id']]['enabled'] = False
			guild_dict[g['id']]['initials'] = gen_initials(g['name'])
	return guild_dict

def gen_keywords(keywords, sub):
    if len(keywords) > 0:
        for key in keywords:
            if 'keyword' in key and len(key['keyword']) > 0 and len(key['keyword']) <= 50:
                try:
                    if(int(key['regex'])):
                        re.compile(key['keyword'])
                except:
                    continue
                if 'toggle' in key and key['toggle'] == 'whitelist':
                        models.Whitelist.create(keyword=key['keyword'], keyword_type = key['type'][:50], subscription = sub.id, regex = int(key['regex']), required=key['required'])
                elif 'toggle' in key and key['toggle'] == 'blacklist':
                        models.Blacklist.create(keyword=key['keyword'], keyword_type = key['type'][:50], subscription = sub.id, regex = int(key['regex']), required=key['required'])


def check_subreddit(request):
    if 'subreddit' in request.form and len(request.form['subreddit']) > 1 and len(request.form['subreddit']) <= 20:
        subreddit = request.form['subreddit'].strip()
        subreddit = re.sub(r'[^A-Za-z0-9_]', '',subreddit)
        if len(subreddit) < 1 or not sub_exists(subreddit):
            raise
    else:
        raise
    return subreddit.lower()



def check_guild_access(token, guild_id):
    user_owned_guilds = filter_owned_guilds(get_user_guilds(token))
    return user_owned_guilds[guild_id]

def get_entries(entry_list):
    entries = {}
    for entry in entry_list:
        if entry.subreddit not in entries:
            entries[entry.subreddit] = []
        entry_tmp = model_to_dict(entry)
        entry_tmp['keywords'] = []
        for keyword in models.Whitelist.select().where(models.Whitelist.subscription_id == entry.id):
            entry_tmp['keywords'].append(model_to_dict(keyword))
        entry_tmp['blacklist'] = [] 
        for blacklist in models.Blacklist.select().where(models.Blacklist.subscription_id == entry.id):
            entry_tmp['blacklist'].append(model_to_dict(blacklist))
        entries[entry.subreddit].append(entry_tmp)
    return entries