import itertools
import logging
import random
import string
from collections import defaultdict, Counter
from typing import Dict

log = logging.getLogger(__name__)

WORD_CHARS = string.ascii_lowercase + string.digits + "'’"
DELIMITER = string.whitespace + string.punctuation.replace("'", '')
PUNCTUABLE = string.punctuation.replace("'", '')


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
        self.table: Dict[str, Counter] = defaultdict(lambda: Counter())

    def add_sentence(self, sentence, stops='.?!'):
        words = tokenize(sentence.lower())
        print(words)
        for i in range(len(words) - 1):
            word, following = words[i], words[i + 1]
            self.table[word][following] += 1
            if word in stops:
                self.table[None][following] += 1

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


class MarkovCog:

    def __init__(self, bot):
        self.bot = bot
        self.table = defaultdict(lambda _: Counter())

    async def on_ready(self):
        log.info('Building markov chain...')
        #self.table


def setup(bot):
    bot.add_cog(MarkovCog(bot))


if __name__ == '__main__':
    corpus = ''
    mc = MarkovChain()

    mc.add_sentence(corpus)
    for i in range(10):
        print(untokenize(mc.generate_indefinite()))
