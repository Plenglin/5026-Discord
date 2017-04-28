import os

import bot_framework
import logging

import commands


logging.basicConfig(level=logging.DEBUG)
client = bot_framework.Client()
client.register_listener(commands.SwearJar)
client.register_listener(bot_framework.util.OnStart, bot_framework.util.HelpCommand)

client.loop.run_until_complete(client.start(os.environ.get('TOKEN')))
