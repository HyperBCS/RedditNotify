import app.models as models
import redis
import pickle
import requests
import flask_login
import config
from flask import Blueprint, render_template, url_for, redirect, request, flash
from app import LM as login_manager
from flask_login import UserMixin
from datetime import timedelta
from urllib.parse import urlencode
from functools import wraps

login_page = Blueprint('login_page', __name__, template_folder="./views/templates")

logged_in_users = {}

r = redis.Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT, 
    password=config.REDIS_PASSWORD)

class User(UserMixin):
    '''A User model for who will be using the software. Users have different levels of access with different roles
    Current active roles:
        - user
        - admin
    '''
    def __init__(self,id, token, username, avatar):
        self.id = id
        self.username = username
        self.avatar = avatar
        self.token = token
        self.role = 'user'

    def get_id(self):
        return self.id

def exchange_code(code):
  data = {
    'client_id': config.DISCORD_CLIENT_ID,
    'client_secret': config.DISCORD_CLIENT_SECRET,
    'grant_type': 'authorization_code',
    'code': code,
    'redirect_uri': config.OAUTH2_REDIRECT_URL,
    'scope': 'identify email connections'
  }
  headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
  }
  r = requests.post('%s/oauth2/token' % config.DISCORD_API_ENDPOINT, data=data, headers=headers)
  r.raise_for_status()
  return r.json()

def get_discord_user(token):
    url = 'https://discordapp.com/api/users/@me'
    headers = {'Authorization': 'Bearer '+token}
    r = requests.get(url,headers=headers)
    r.raise_for_status()
    return r.json()

@login_manager.user_loader
def user_loader(id):
    '''Loads the user via a DB call
    Args:
        email (str): The email to load
    Returns:
        User: The user object corresponding to the email passed, or None if it doesn't exist
    '''
    user_sess = r.get(id)
    if user_sess != None:
        return pickle.loads(user_sess)
    else:
        return

@login_manager.unauthorized_handler
def unauth():
    '''Function to handle requests to resources that are not authorized or authenticated.'''
    if flask_login.current_user.is_authenticated:
        user = flask_login.current_user
        return render_template('index.html', logged_in=True, DISCORD_CLIENT_ID = config.DISCORD_CLIENT_ID, REDIRECT_URI=urlencode({'redirect_uri': config.OAUTH2_REDIRECT_URL}), data=user), 403
    else:
        return render_template('index.html', DISCORD_CLIENT_ID = config.DISCORD_CLIENT_ID, REDIRECT_URI=urlencode({'redirect_uri': config.OAUTH2_REDIRECT_URL})), 200

def require_login(func):
    '''Wrapper around the login_required wrapper from flask-login
    This allows us to keep the same style and also not have to have multiple imports for
    roles and require_login
    '''
    @wraps(func)
    @flask_login.login_required
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper

def require_role(role,**kwargss):
    '''Decorate a function with this in order to require a specific role(s), to access a view.
    Also decorates a function, so that you must pass the current user's role into it's first
    argument if it's needed.
    By decorating a function with @require_role you are implicity forcing @login_required as well.
    Example:
    .. code-block:: python
        @APP.route('/admin-dashboard')
        @require_role('admin')
        def view_dash():
        # Something here
        @APP.route('/reservationH')
        @require_role('admin','host',getrole=True)
        def view_dash(role):
            ...
    Args:
        role(list or str):  A single role name or list of role names for which users are allowed to access the specified resource
    If a user is not authorized then the flask_login.unauthorized handler is called.
    '''
    def real_wrap(func):
        @wraps(func)
        @flask_login.login_required
        def wrapper(*args, **kwargs):
            user = flask_login.current_user
            kwargs['user'] = user
            if isinstance(role, list) and user.role in role:
                return func(*args, **kwargs)
            elif user.role == role:
                return func(*args, **kwargs)
            else:
                return login_manager.unauthorized()
        return wrapper
    return real_wrap

@login_page.route('/callback',  methods=['GET'])
def callback():
    ''''Callback for oauth'''
    try:
        data = exchange_code(request.args.get('code'))
        user_info = get_discord_user(data['access_token'])
        user = User(user_info['id'],data['access_token'], user_info['username'],user_info['avatar'])
        user_pickle = pickle.dumps(user)
        r.setex(user_info['id'],timedelta(minutes=10080), user_pickle)
        flask_login.login_user(user)
        return redirect(url_for('servers.show'))
    except Exception as e:
        print(e)
        flash(u'Unable to login user', 'danger')
        return render_template('index.html',error='Unable to login user',  DISCORD_CLIENT_ID = config.DISCORD_CLIENT_ID, REDIRECT_URI=urlencode({'redirect_uri': config.OAUTH2_REDIRECT_URL})), 401

@login_page.route('/logout')
def logout():
    ''''Logs a user out and renders the login template with a message'''
    if flask_login.current_user.is_authenticated:
        r.delete(flask_login.current_user.id)
        flask_login.logout_user()
    flash(u'Successfully logged out', 'success')
    return render_template('index.html',  DISCORD_CLIENT_ID = config.DISCORD_CLIENT_ID, REDIRECT_URI=urlencode({'redirect_uri': config.OAUTH2_REDIRECT_URL}))