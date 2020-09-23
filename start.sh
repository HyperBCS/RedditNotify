#!/bin/bash
gunicorn -w 4 --worker-class=gevent --bind 0.0.0.0:8888 wsgi:app --log-file 'logs/server.log' --access-logfile 'logs/access.log' &
python3 bot.py