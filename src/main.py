import logging
import os

from discord.ext.commands import Bot

bot = Bot(description='Ghost of Jank Memes', command_prefix='>', pm_help=True)

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


@bot.event
async def on_ready():
    log.info(f'Logged in as {bot.user.name} with ID {bot.user.id}')


bot.load_extension('swear_finder')
bot.load_extension('cancer_finder')
bot.load_extension('markovcog')
bot.load_extension('anim_emoji')
bot.run(os.environ.get('TOKEN'))
