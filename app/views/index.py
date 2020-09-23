from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound
from app.auth import require_role
import config

page = Blueprint('index', __name__, template_folder='templates')

@page.route('/')
@require_role('user')
def show(*args, **kwargs):
    '''Render Homepage'''
    user = kwargs['user']
    try:
        return render_template('index.html',logged_in=True,data=user, DISCORD_CLIENT_ID = config.DISCORD_CLIENT_ID)
    except TemplateNotFound:
        abort(404)