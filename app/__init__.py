import praw
from peewee import *
from flask import Flask, render_template
from urllib.parse import urlencode
import flask_login
import app.models as models
import config


LM = flask_login.LoginManager()
reddit = praw.Reddit(user_agent="RedditNotify (by /u/" + config.REDDIT_USERNAME + ")",
                 client_id=config.REDDIT_CLIENT_ID, client_secret=config.REDDIT_CLIENT_SECRET)

def create_app():

    # maybe move this somewhere else
    models.Guild.create_table(True)
    models.User.create_table(True)
    models.Subscription.create_table(True)
    models.Whitelist.create_table(True)
    models.Blacklist.create_table(True)

    APP = Flask(__name__, template_folder="views/templates", static_url_path='/static')
    APP.config["SECRET_KEY"] = config.FLASK_SECRET

    LM.init_app(APP)
    import app.auth # register the login and authentication functions

    # registering views
    from app.auth import login_page
    from app.views import index, server_list, dashboard

    APP.register_blueprint(login_page, url_prefix='/auth')
    APP.register_blueprint(index.page, url_prefix='/')
    APP.register_blueprint(server_list.page, url_prefix='/servers')
    APP.register_blueprint(dashboard.page, url_prefix='/dashboard')

    @APP.errorhandler(404)
    def page_not_found(e):
        # note that we set the 404 status explicitly
        if flask_login.current_user.is_authenticated:
            user = flask_login.current_user
            return render_template('index.html', logged_in=True, DISCORD_CLIENT_ID = config.DISCORD_CLIENT_ID, REDIRECT_URI=urlencode({'redirect_uri': config.OAUTH2_REDIRECT_URL}), data=user), 404
        else:
            return render_template('index.html', DISCORD_CLIENT_ID = config.DISCORD_CLIENT_ID, REDIRECT_URI=urlencode({'redirect_uri': config.OAUTH2_REDIRECT_URL})), 404


    return APP