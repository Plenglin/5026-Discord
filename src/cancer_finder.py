import logging
import re

from discord import Message

CANCER_REGEX = r'[ck]\w*n\w*[ck]\w*r'
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
            await self.bot.send_message(message.channel, 'ur cancer')


def setup(bot):
    bot.add_cog(CancerFinder(bot))


if __name__ == '__main__':
    print(find_cancer('cancer'))