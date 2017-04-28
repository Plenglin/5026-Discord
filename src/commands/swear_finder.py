import os
import random
import logging

import psycopg2 as pg

import bot_framework

SWEAR_TABLE = 'swears'

SWEAR_WORDS = 'fuck shit cunt asshole'.split()
MESSAGES = [
    'hey hey be nice {mention}',
    'no swears {mention}',
    'censor yourself {mention}',
    'you know {mention}... dont... say... swears',
    'i need to ask you to stop {mention}, that swearing is making people nervous'
]

log = logging.getLogger(__name__)


class SwearJar(bot_framework.Listener):

    def __init__(self, *args, **kwargs):
        super(SwearJar, self).__init__(*args, **kwargs)
        self.connection = pg.connect(os.environ.get('DATABASE_URL'))
        log.info('database connection initialized')

    async def on_message(self, message):

        if any(w in message.content for w in SWEAR_WORDS):
            log.debug('detected a swear')
            await self.client.send_message(message.channel, random.choice(MESSAGES).format(mention=message.author.mention))
            cursor = self.connection.cursor()
            occurences = sum(message.content.count(w) for w in SWEAR_WORDS)
            log.debug('found %s occurences', occurences)
            cursor.execute("SELECT * FROM swears WHERE discord_id = '{}'".format(message.author.id))
            if cursor.fetchone() is None:
                log.debug('No entry found for id %s, creating', message.author.id)
                cursor.execute("INSERT INTO swears (discord_id, times_sweared) VALUES ('{}', 0)".format(message.author.id))
            cursor.execute("UPDATE swears SET times_sweared = times_sweared + {} WHERE discord_id = '{}'".format(occurences, message.author.id))
            self.connection.commit()

        elif self.client.user in message.mentions and 'how many times' in message.content and 'sweared' in message.content:
            try:
                user = next(u for u in message.mentions if u != self.client.user)
            except StopIteration:
                user = message.author
            cursor = self.connection.cursor()
            cursor.execute("SELECT times_sweared FROM swears WHERE discord_id = '{}'".format(user.id))
            data = cursor.fetchone()
            if data in (None, 0):
                await self.client.send_message(message.channel, '{} has not sworn at all.'.format(user.mention))
            else:
                await self.client.send_message(message.channel, '{} has sworn {} times.'.format(user.mention, data[0]))
