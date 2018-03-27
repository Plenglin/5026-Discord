import logging
import os
import random

import discord
import psycopg2 as pg
from discord.ext import commands
from discord.ext.commands import Context

SWEAR_TABLE = 'swears'

SWEAR_WORDS = 'fuck shit cunt asshole fuk shite'.split()
MESSAGES = [
    'hey hey be nice {mention}',
    'no swears {mention}',
    'censor yourself {mention}',
    "you know {mention}... don't... say... swears",
    'i need to ask you to stop {mention}, that swearing is making people nervous',
    "{mention} it's time to stop"
]

log = logging.getLogger(__name__)


def is_swear(text: str):
    return any(w in text.lower() for w in SWEAR_WORDS)


class SwearJar:
    def __init__(self, bot):
        self.bot = bot
        self.connection = pg.connect(os.environ.get('DATABASE_URL'))

    async def on_message(self, message):
        if is_swear(message.content):
            log.info('Detected a swear from %s', message.author.name)
            await self.bot.send_message(message.channel, random.choice(MESSAGES).format(mention=message.author.mention))
            cursor = self.connection.cursor()
            occurences = sum(message.content.count(w) for w in SWEAR_WORDS)
            log.debug('found %s occurences', occurences)
            cursor.execute("SELECT * FROM swears WHERE discord_id = '{}'".format(message.author.id))
            if cursor.fetchone() is None:
                log.debug('No entry found for id %s, creating', message.author.id)
                cursor.execute(
                    "INSERT INTO swears (discord_id, times_sweared) VALUES ('{}', 0)".format(message.author.id))
            cursor.execute(
                "UPDATE swears SET times_sweared = times_sweared + {} WHERE discord_id = '{}'".format(occurences,
                                                                                                      message.author.id))
            self.connection.commit()

    @commands.command()
    async def swearcount(self, user: discord.User):
        """
        Find out how much a certain person has sweared: >swears @user

        :param user: the user
        :return:
        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT times_sweared FROM swears WHERE discord_id = '{}'".format(user.id))
        data = cursor.fetchone()
        if data in (None, 0):
            await self.bot.say('{} has not sworn at all.'.format(user.mention))
        else:
            await self.bot.say('{} has sworn {} times.'.format(user.mention, data[0]))

    @commands.command(pass_context=True)
    async def swears(self, ctx: Context):
        """Ranks people by how much they have sweared.
        """
        log.info('%s wants a leaderboard', ctx.message.author.name)
        server = ctx.message.channel.server
        cursor = self.connection.cursor()
        cursor.execute('SELECT discord_id, times_sweared FROM swears ORDER BY times_sweared DESC;')
        size = min(5, len(server.members))
        server_ids = [u.id for u in server.members]
        data_in_server = ((server.get_member(i), t) for i, t in cursor if i in server_ids)
        result = [next(data_in_server, None) for _ in range(0, size)]
        output = ''
        for rank, p in enumerate(result):
            if p is None:
                break
            user, times = p
            output += '#{rank}: {name}, with {times} swears\n'.format(rank=rank + 1, name=user.display_name,
                                                                      times=times)
        await self.bot.say(output)


def setup(bot):
    log.debug(f'Adding to {bot}')
    bot.add_cog(SwearJar(bot))
