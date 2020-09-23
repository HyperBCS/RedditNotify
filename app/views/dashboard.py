import sys, traceback
import json
import app.models as models
import app.controllers.util as util
from flask import Blueprint, render_template, abort, request
from app.auth import require_role
from playhouse.shortcuts import model_to_dict, dict_to_model

page = Blueprint('dashboard', __name__, template_folder='templates')

@page.route('/guild/<guild_id>/')
@require_role('user')
def show_dash(*args, **kwargs):
    # check user has access to guild_id
    user = kwargs['user']
    guild_id = kwargs['guild_id']
    try:
        guild_search = util.get_guild(guild_id)
        guild_channels = util.get_guild_channels(guild_id)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        abort(404)
    try:
        util.check_guild_access(user.token, guild_id)
    except:
        abort(404)
    guild_name = guild_search['name']
    text_channels = {}
    for ch in guild_channels:
        if ch['type'] == 0:
            text_channels[ch['id']] = ch
    entries = util.get_entries(models.Subscription.select().where(models.Subscription.guild_id == guild_id))
    return render_template('dashboard.html',logged_in=True,data=user, channels=text_channels, entries = entries, guild_name = guild_name, dash_type = "guild")

@page.route('/self/')
@require_role('user')
def show_dash_self(*args, **kwargs):
    user = kwargs['user']
    user_search = util.get_user(user.id)
    if user_search == None:
        return "Invalid keywords", 400
    entries = util.get_entries(models.Subscription.select().where((models.Subscription.entry_author == user.id) & (models.Subscription.guild_id == None)))
    return render_template('dashboard.html',logged_in=True,data=user, entries = entries, guild_name = user_search['username'], dash_type = "self")

@page.route('/self/add_entry',methods=['POST'])
@require_role('user')
def add_entry_self(*args, **kwargs):
    # check guildID is authorized, and subreddit doesn't already exist for specific guild
    user = kwargs['user']
    keywords = json.loads(request.form['keywords'])
    try:
        subreddit = util.check_subreddit(request)
    except Exception as e:
        return "Invalid subreddit name", 400
    if 'nsfw' in request.form and (request.form['nsfw'] == 'block' or request.form['nsfw'] == 'only'):
        nsfw = request.form['nsfw']
    else:
        nsfw = 'allow'
    try:
        entry = models.Subscription.create(subreddit = subreddit, entry_author = user.id, nsfw = nsfw)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return "Server has encountered an error", 400
    try:
        util.gen_keywords(keywords, entry)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return "Invalid keywords", 400
    return str(entry.id)

@page.route('/guild/<guild_id>/add_entry',methods=['POST'])
@require_role('user')
def add_entry(*args, **kwargs):
    # check guildID is authorized, and subreddit doesn't already exist for specific guild
    user = kwargs['user']
    guild_id = kwargs['guild_id']
    try:
        util.check_guild_access(user.token, guild_id)
    except:
        return "Access Denied", 400
    keywords = json.loads(request.form['keywords'])
    try:
        subreddit = util.check_subreddit(request)
    except Exception as e:
        return "Invalid subreddit name", 400
    if 'channel' in request.form and request.form['channel'].isnumeric():
        channel = request.form['channel']
    else:
        return "Invalid channel", 400
    if 'nsfw' in request.form and (request.form['nsfw'] == 'block' or request.form['nsfw'] == 'only'):
        nsfw = request.form['nsfw']
    else:
        nsfw = 'allow'
    try:
        entry = models.Subscription.create(guild_id = guild_id, channel_id = channel, subreddit = subreddit, entry_author = user.id, nsfw = nsfw)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return "Server has encountered an error", 400
    try:
        util.gen_keywords(keywords, entry)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return "Invalid keywords", 400
    return str(entry.id)

@page.route('/self/update_entry',methods=['POST'])
@require_role('user')
def update_entry_self(*args, **kwargs):
    # check guildID is authorized, and subreddit doesn't already exist for specific guild
    user = kwargs['user']
    keywords = json.loads(request.form['keywords'])
    try:
        subreddit = util.check_subreddit(request)
    except Exception as e:
        return "Invalid subreddit name", 400
    if 'nsfw' in request.form and (request.form['nsfw'] == 'block' or request.form['nsfw'] == 'only'):
        nsfw = request.form['nsfw']
    else:
        nsfw = 'allow'
    try:
        id = request.form['id']
        sub = models.Subscription.get(models.Subscription.id == id)
        models.Whitelist.delete().where(models.Whitelist.subscription_id == id).execute()
        models.Blacklist.delete().where(models.Blacklist.subscription_id == id).execute()
        query = models.Subscription.update(subreddit = subreddit,nsfw=nsfw).where(models.Subscription.id == id)
        query.execute()
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return "Server has encountered an error", 400
    try:
        util.gen_keywords(keywords, sub)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return "Invalid keywords", 400
    return "Success"

@page.route('/guild/<guild_id>/update_entry',methods=['POST'])
@require_role('user')
def update_entry(*args, **kwargs):
    # check guildID is authorized, and subreddit doesn't already exist for specific guild
    user = kwargs['user']
    guild_id = kwargs['guild_id']
    try:
        util.check_guild_access(user.token, guild_id)
    except:
        return "Access Denied", 400
    keywords = json.loads(request.form['keywords'])
    try:
        subreddit = util.check_subreddit(request)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return "Invalid subreddit name", 400
    if 'channel' in request.form and request.form['channel'].isnumeric():
        channel = request.form['channel']
    else:
        return "Invald channel", 400
    if 'nsfw' in request.form and (request.form['nsfw'] == 'block' or request.form['nsfw'] == 'only'):
        nsfw = request.form['nsfw']
    else:
        nsfw = 'allow'
    try:
        id = request.form['id']
        sub = models.Subscription.get(models.Subscription.id == id)
        models.Whitelist.delete().where(models.Whitelist.subscription_id == id).execute()
        models.Blacklist.delete().where(models.Blacklist.subscription_id == id).execute()
        query = models.Subscription.update(subreddit = subreddit, channel_id = channel, nsfw=nsfw).where(models.Subscription.id == id)
        query.execute()
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return "Server has encountered an error", 500
    try:
        util.gen_keywords(keywords, sub)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return "Invalid keywords", 400
    return "Success"

@page.route('/guild/<guild_id>/delete_entry',methods=['POST'])
@page.route('/self/delete_entry',methods=['POST'])
@require_role('user')
def delete_entry(*args, **kwargs):
    user = kwargs['user']
    if 'guild_id' in kwargs:
        guild_id = kwargs['guild_id']
        try:
            util.check_guild_access(user.token, guild_id)
        except:
            return "Access Denied", 400
    if 'id' in request.form:
        id = request.form['id']
    else:
        return "Server has encountered an error", 500
    try:
        models.Whitelist.delete().where(models.Whitelist.subscription_id == id).execute()
        models.Blacklist.delete().where(models.Blacklist.subscription_id == id).execute()
        models.Subscription.delete().where(models.Subscription.id == id).execute()
    except Exception as e:
        print(e)
        return "Server has encountered an error", 500
    return "Success"