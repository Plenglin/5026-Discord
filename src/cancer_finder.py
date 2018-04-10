import asyncio
import logging
import re

import discord
from discord import Message

CANCER_REGEX = r'([ck]\w*n\w*[ck]\w*r)[ .?!]'
log = logging.getLogger(__name__)


def find_cancer(text):
    return re.search(CANCER_REGEX, text, re.IGNORECASE)


class CancerFinder:

    def __init__(self, bot):
        self.bot = bot

    async def on_message(self, message: Message):
        result = find_cancer(message.content)
        if message.author.id != self.bot.user.id and result:
            log.info('Cancer detected from %s: %s', message.author, message.content)
            role = discord.utils.get(message.server.roles, name='Muted')
            if role is not None:
                log.info('We can mute!')
                mute_msg = await self.bot.send_message(message.channel, f'ur {result.group(1)}, pls quiet')
                await self.bot.delete_message(message)
                await self.bot.add_roles(message.author, role)

                log_channel = discord.utils.get(message.server.channels, name='admin-logs')
                if log_channel is not None:
                    log.info('We can log our action!')
                    await self.bot.send_message(
                        log_channel,
                        f"**Removed message from {message.author.name} in #{message.channel.name}:** {message.content}\n**Reason:** it's cancer"
                    )
                await asyncio.sleep(30)
                await self.bot.remove_roles(message.author, role)
                await self.bot.delete_message(mute_msg)


def setup(bot):
    log.debug(f'Adding to {bot}')
    bot.add_cog(CancerFinder(bot))


if __name__ == '__main__':
    print(find_cancer('cancer'))
