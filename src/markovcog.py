import itertools
import logging
import random
import string
from collections import defaultdict, Counter
from typing import Dict, DefaultDict

import discord
from discord.ext import commands
from discord import Message

log = logging.getLogger(__name__)

WORD_CHARS = string.ascii_lowercase + string.digits + "'’"
DELIMITER = string.whitespace + string.punctuation.replace("'", '')
PUNCTUABLE = string.punctuation.replace("'", '')


CHANNEL_MSG_LIMIT = 500
MIN_COMPLETENESS = 200
MIN_WORDS_IN_MSG = 5


def tokenize(text):
    tokens = []
    word_buf = []
    for c in text.lower():
        if c in WORD_CHARS:
            word_buf.append(c)
        else:
            if len(word_buf) > 0:
                tokens.append(''.join(word_buf))
            word_buf.clear()
            if c in PUNCTUABLE:
                tokens.append(c)
    return tokens


def untokenize(tokens):
    out_buf = []
    for t in tokens:
        if t in PUNCTUABLE:
            out_buf.append(t)
        else:
            if len(out_buf) > 0:
                out_buf.append(' ')
            out_buf.append(t)
    return ''.join(out_buf)


class MarkovChain:

    def __init__(self):
        self.table: DefaultDict[str, Counter] = defaultdict(Counter)
        self.completeness = 0

    def add(self, sentence, stops='.?!'):
        tokens = tokenize(sentence.lower())
        for i in range(len(tokens) - 1):
            token, following = tokens[i], tokens[i + 1]
            self.table[token][following] += 1
            if token in stops:
                self.table[None][following] += 1
                self.completeness += 0.25
            else:
                self.completeness += 1

    def pick_random_after(self, word, allow_none=True):
        counter = self.table[word]
        if not allow_none:
            del counter[None]
        words = counter.values()
        i = random.randrange(sum(words))
        return next(itertools.islice(counter.elements(), i, None))

    def generate_indefinite(self, stop_at='.!?'):
        word = self.pick_random_after(None, allow_none=False)
        while word not in stop_at:
            yield word
            word = self.pick_random_after(word)


class MarkovUser:

    def __init__(self):
        self.chain = MarkovChain()

    def add_message(self, msg: Message):
        if msg.content.count(' ') < MIN_WORDS_IN_MSG - 1:
            self.chain.add(msg.content)


class MarkovCog:

    def __init__(self, bot):
        self.bot = bot
        self.user_chains: DefaultDict[str, MarkovUser] = defaultdict(MarkovUser)

    async def on_ready(self):
        log.info('Building markov chains...')
        self.user_chains.clear()
        for server in self.bot.servers:
            log.debug(f'Finding channels in {server}')
            for channel in server.channels:
                log.debug(f'Finding messages in {channel}')
                try:
                    async for msg in self.bot.logs_from(channel, limit=CHANNEL_MSG_LIMIT):
                        log.debug(f'Found message in {channel}')
                        self.user_chains[msg.author.id].add_message(msg)
                except discord.Forbidden as e:
                    log.debug(f'Error: cannot read from {channel} because forbidden')
        log.info('Finished building markov chains!')

    async def on_message(self, msg: Message):
        self.user_chains[msg.author.id].add_message(msg)

    @commands.command()
    async def markov(self, user: discord.Member):
        mc = self.user_chains[user.id].chain
        if mc.completeness > MIN_COMPLETENESS:
            tokens = mc.generate_indefinite()
            await self.bot.say(untokenize(tokens))
        else:
            await self.bot.say(f"not enough info on {user.mention}")


def setup(bot):
    bot.add_cog(MarkovCog(bot))


if __name__ == '__main__':
    corpus = 'What the fuck did you just fucking say about me, you little bitch? I’ll have you know I graduated top ' \
             'of my class in the Navy Seals, and I’ve been involved in numerous secret raids on Al-Quaeda, ' \
             'and I have over 300 confirmed kills. I am trained in gorilla warfare and I’m the top sniper in the ' \
             'entire US armed forces. You are nothing to me but just another target. I will wipe you the fuck out ' \
             'with precision the likes of which has never been seen before on this Earth, mark my fucking words. You ' \
             'think you can get away with saying that shit to me over the Internet? Think again, fucker. As we speak ' \
             'I am contacting my secret network of spies across the USA and your IP is being traced right now so you ' \
             'better prepare for the storm, maggot. The storm that wipes out the pathetic little thing you call your ' \
             'life. You’re fucking dead, kid. I can be anywhere, anytime, and I can kill you in over seven hundred ' \
             'ways, and that’s just with my bare hands. Not only am I extensively trained in unarmed combat, ' \
             'but I have access to the entire arsenal of the United States Marine Corps and I will use it to its full ' \
             'extent to wipe your miserable ass off the face of the continent, you little shit. If only you could ' \
             'have known what unholy retribution your little “clever” comment was about to bring down upon you, ' \
             'maybe you would have held your fucking tongue. But you couldn’t, you didn’t, and now you’re paying the ' \
             'price, you goddamn idiot. I will shit fury all over you and you will drown in it. You’re fucking dead, ' \
             'kiddo. '.lower()
    mc = MarkovChain()

    mc.add(corpus)
    print(mc.completeness)
    for i in range(10):
        print(untokenize(mc.generate_indefinite()))
