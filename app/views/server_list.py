from flask import Blueprint, render_template, abort, flash
from app.auth import require_role
import sys, traceback
import config
import app.controllers.util as util

page = Blueprint('servers', __name__, template_folder='templates')

@page.route('/')
@require_role('user')
def show(*args, **kwargs):
    '''Render Homepage'''
    user = kwargs['user']
    try:
        guild_dict = util.filter_owned_guilds(util.get_user_guilds(user.token))
        for g in util.get_bot_guilds():
        	g_id = str(g['id'])
        	if g_id in guild_dict:
        		guild_dict[g_id]['enabled'] = True
        return render_template('servers.html',logged_in=True,data=user, guilds=guild_dict, DISCORD_CLIENT_ID = config.DISCORD_CLIENT_ID)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        flash("An error has occured",'danger')
        return render_template('index.html',logged_in=True,data=user, DISCORD_CLIENT_ID = config.DISCORD_CLIENT_ID)