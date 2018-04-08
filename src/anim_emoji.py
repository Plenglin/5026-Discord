import logging
import os
import re

import discord
import psycopg2 as pg

from discord import Client, Message
from discord.ext import commands
from discord.ext.commands import Bot
from psycopg2._psycopg import IntegrityError

log = logging.getLogger(__name__)


class AnimEmoji:
    def __init__(self, bot: Client):
        self.bot: Client = bot
        self.connection = pg.connect(os.environ.get('DATABASE_URL'))

    async def on_ready(self):
        log.info("Creating database if it doesn't exist")
        self.connection.cursor().execute("CREATE TABLE IF NOT EXISTS animated_emojis("
                                         "emoji text NOT NULL,"
                                         "id text NOT NULL,"
                                         "server text NOT NULL,"
                                         "primary key (emoji, server)"
                                         ")")

    @commands.command(pass_context=True)
    async def addanimatedemoji(self, ctx, emoji):
        log.info('%s wants to add %s', ctx.message.author.name, emoji)
        url = discord.utils.find(lambda e: e.name == emoji, ctx.message.server.emojis).url
        emoji_id = re.search(r'api/emojis/(\d+).png', url).group(1)
        try:
            self.connection.cursor().execute("INSERT INTO animated_emojis (emoji, id, server) VALUES (%s, %s, %s)",
                                             (emoji, emoji_id, ctx.message.server.id))
            self.connection.commit()
            await self.bot.send_message(ctx.message.channel,
                                        "_Successfully added animated emoji :%s: with id %s_" % (emoji, emoji_id))
        except IntegrityError as e:
            log.error(e)
            self.connection.rollback()
            await self.bot.send_message(ctx.message.channel, '**Error:** %s already registered on this server' % emoji)

    @commands.command(pass_context=True)
    async def removeanimatedemoji(self, ctx, emoji):
        log.info('%s wants to remove %s', ctx.message.author.name, emoji)
        self.connection.cursor().execute("DELETE FROM animated_emojis WHERE emoji = %s and server = %s",
                                         (emoji, ctx.message.server.id))
        self.connection.commit()
        await self.bot.send_message(ctx.message.channel, "_Successfully removed animated emoji (if it was ever registered) :%s:_" % emoji)

    async def on_message(self, msg: Message):
        if msg.author.id == self.bot.user.id: return
        if msg.content.startswith('>'): return
        if msg.server is None: return

        cur = self.connection.cursor()
        cur.execute("SELECT emoji, id FROM animated_emojis WHERE server = %s", (msg.server.id,))
        emojis = [(a, b) for a, b in cur.fetchall()]
        if any((':%s:' % emoji) in msg.content for emoji, _ in emojis):
            log.info('Found animated emoji in: %s', msg.content)
            await self.bot.delete_message(msg)

            log_channel = discord.utils.get(msg.server.channels, name='admin-logs')
            if log_channel is not None:
                log.debug('We can log our action!')
                await self.bot.send_message(
                    log_channel,
                    f"**Removed message from {msg.author.name} in #{msg.channel.name}:** "
                    f"{msg.content}\n**Reason:** replacing with animated emoji"
                )

            out = msg.content
            for emoji, emoji_id in emojis:
                out = out.replace(':%s:' % emoji, '<a:%s:%s>' % (emoji, emoji_id))

            await self.bot.send_message(msg.channel, '%s\: %s' % (msg.author.mention, out))
        else:
            log.debug('No animated emoji in: %s', msg.content)


def setup(bot):
    bot.add_cog(AnimEmoji(bot))
