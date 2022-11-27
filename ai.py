from random import Random
from players import CompPlayer
from functools import reduce
import re


def easy_level(player: CompPlayer):
    r = Random()
    return player.alphabet[r.randint(0, len(player.alphabet))]


def mid_level(player: CompPlayer):
    dictionary = list(filter(lambda word: len(word) == len(player.mask), player.dictionary))
    freq: dict[str, int] = {}
    for letter in player.alphabet:
        freq[letter] = len(list(filter(lambda word: letter in word, dictionary)))
    ans = sorted(list(freq.items()), reverse=True, key=lambda pair: pair[1])
    for pair in ans:
        if (pair[0] not in player.absent_words) and (pair[0] not in player.mask):
            return pair[0]


def hard_level(player: CompPlayer):
    regex = re.compile(player.mask)
    dictionary = list(filter(lambda word: regex.fullmatch(word) and (set(word).intersection(player.absent_words) == {}), player.dictionary))
    freq: dict[str, int] = {}
    for letter in player.alphabet:
        freq[letter] = len(list(filter(lambda word: letter in word, dictionary)))
    ans = sorted(list(freq.items()), reverse=True, key=lambda pair: pair[1])
    for pair in ans:
        if (pair[0] not in player.absent_words) and (pair[0] not in player.mask):
            return pair[0]