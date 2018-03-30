import asyncio
import itertools
import json
import logging
import random
import string
from collections import defaultdict, Counter
from typing import DefaultDict

import discord
from discord import Message, Server
from discord.ext import commands
from discord.ext.commands import Context, MemberConverter, BadArgument

log = logging.getLogger(__name__)

WORD_CHARS = string.ascii_lowercase + string.digits + "'’"
SENTENCE_DELIMITER = '.?!;'
NON_STOP_PUNCTUATION = [c for c in string.punctuation if c not in SENTENCE_DELIMITER and c not in WORD_CHARS]
PUNCTUATION = list(SENTENCE_DELIMITER) + NON_STOP_PUNCTUATION

CHANNEL_MSG_LIMIT = 500
MIN_COMPLETENESS = 50
MIN_WORDS = 3


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
            if c in PUNCTUATION:
                tokens.append(c)
    tokens.append(''.join(word_buf))
    return tokens


def untokenize(tokens):
    out_buf = []
    for t in tokens:
        if t in PUNCTUATION:
            out_buf.append(t)
            out_buf.append(' ')
        else:
            if len(out_buf) > 0:
                out_buf.append(' ')
            out_buf.append(t)
    return ''.join(out_buf)


class MarkovChain:

    def __init__(self):
        self.table: DefaultDict[str, Counter] = defaultdict(Counter)
        self.completeness = 0

    def add(self, sentence, stops=SENTENCE_DELIMITER):
        tokens = [None] + tokenize(sentence.lower()) + [None]
        for i in range(len(tokens) - 1):
            token, following = tokens[i], tokens[i + 1]
            self.table[token][following] += 1
            if token is None or token in stops:
                self.table[None][following] += 1
                self.completeness += 0.25
            else:
                self.completeness += 1

    def pick_random_after(self, word, allow_none=True):
        counter = self.table[word].copy()
        if not allow_none:
            del counter[None]
        words = counter.values()
        i = random.randrange(sum(words))
        return next(itertools.islice(counter.elements(), i, None))

    def generate(self, limit=100, stop_at=list('.!?') + [None]):
        word = self.pick_random_after(None, allow_none=False)
        i = 0
        while word not in stop_at and i < limit:
            yield word
            word = self.pick_random_after(word)
            i += 1

    def to_json(self):
        data = {w: {f: n for f, n in k.items()} for w, k in self.table.items()}
        return json.dumps(data)


class MarkovUser:

    def __init__(self):
        self.chain = MarkovChain()

    def add_message(self, msg: Message):
        print(msg.clean_content)
        s = msg.clean_content
        if len(s) > 0 and s[0] in WORD_CHARS:
            log.debug(f'Adding {s}')
            self.chain.add(s)

    def __repr__(self):
        return repr(self.chain.table)


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
                        log.debug(f'Found message in {server}#{channel} from {msg.author.id}')
                        if msg.author.id != self.bot.user.id:
                            self.user_chains[msg.author.id].add_message(msg)
                except discord.Forbidden as e:
                    log.debug(f'Error: cannot read from {channel} because forbidden')
        log.info('Finished building markov chains: %s', {u: c.chain.to_json() for u, c in self.user_chains.items()})

    async def on_message(self, msg: Message):
        if msg.author.id != self.bot.user.id:
            self.user_chains[msg.author.id].add_message(msg)

    @commands.command(pass_context=True)
    async def markov(self, ctx: Context, arg):
        try:
            log.debug('attempting to find mention')
            user = MemberConverter(ctx, arg).convert()
            await self._markov(user)
        except BadArgument:
            log.debug('there was no mention, resorting to search')
            res = await self._find_applicable_user(ctx.message.server, arg)
            if res is not None:
                await self._markov(res)

    async def _find_applicable_user(self, server: Server, name: str):
        log.debug('finding users who start with %s', name)
        users = [m for m in server.members if m.display_name.lower().startswith(name.lower())]
        if len(users) == 0:
            log.debug('no one starts with %s', name)
            msg = await self.bot.say(f'There are no users that start with {name}, please try again')
            await asyncio.sleep(10)
            await self.bot.delete_message(msg)
            return

        if len(users) == 1:
            log.debug('one dude starts with %s', name)
            user = users[0]
        else:
            for u in users:
                if u.display_name == name:
                    log.debug("one dude's name is exactly %s", name)
                    user = u
                    break
            else:
                log.debug('there are multiple users that start with %s', name)
                msg = await self.bot.say(f'There are multiple users that start with {name}, please be more specific')
                await asyncio.sleep(10)
                await self.bot.delete_message(msg)
                return
        return user

    async def _markov(self, user: discord.Member):
        mc = self.user_chains[user.id].chain
        log.debug(f'{user.id} has completeness {mc.completeness}')
        if mc.completeness > MIN_COMPLETENESS:
            tokens = tuple()
            while len(tokens) < MIN_WORDS:
                tokens = list(mc.generate())
            log.debug('made tokens %s', tokens)
            await self.bot.say(f'"{untokenize(tokens)}" --_probably {user.display_name}_')
        else:
            msg = await self.bot.say(f"not enough info on {user.display_name}")
            await asyncio.sleep(10)
            await self.bot.delete_message(msg)

def setup(bot):
    bot.add_cog(MarkovCog(bot))


if __name__ == '__main__':
    mc = MarkovChain()
    mc.add('a b c d e f')
    print(untokenize(mc.generate()))