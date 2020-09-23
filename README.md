# RedditNotify
RedditNotify is a simple discord bot that was made to provide live filtered feeds for specific subreddits. The bot is completely managed by a web interface that allows easy customization per server or self.

## Features
- Add subscriptions to a server or @self
- Whitelist or blacklist enabled filters
- Currently supported filters
    - Title(partial match)
    - Author(Exact match)
    - Flair(Exact match)
    - 18+(Block, allow, only allow)

## Installation Guide

All commands below should work in the bash command line with a Debian distribution of GNU/Linux.

**Installing Dependencies**

**Pre-Requisites**:

- OS
	- CentOS 8+
	- Ubuntu 14.04+

- Packages
	- python 3.6+
	- pip3
	- Redis 

Once the dependencies are installed run the following to download the repository.

    git clone https://github.com/HyperBCS/RedditNotify.git

`cd` into the directory

    cd RedditNotify/

Next We'll need to use `virtualenv` to locally install the python packages to this directory.

    virtualenv -p python3 venv
    source venv/bin/activate

To verify we are in the virtual enviornment, the terminal prompt should have the prefix `(venv)`.

Finally we just install our python packages.

    pip install -r requirements.txt

## Starting the Server

Before the server can be started a config file needs to be created with the name `config.py` in the root project directory. An example file can be found with the name `config.py.example`.


To run the server, first make sure the virtual enviornment is activated. Then run the script `start.sh`.

	source venv/bin/activate
    ./start.sh

The start script will launch the web server process, then the discord bot. Both need to be running to ensure normal operation.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](https://choosealicense.com/licenses/mit/)