from abc import abstractmethod
from collections import deque
from enum import Enum


class GameResult(Enum):
    LOSE = -1,
    NONE = 0,
    WON = 1


class Player:
    def __init__(self, name: str, alphabet: str):
        self._score = 0
        self._name = name
        self._movequeue = deque()
        self._alphabet = alphabet
        self._mask = ''
        self._absletters = set()
        self._result = GameResult.NONE

    @property
    def name(self):
        return self._name

    @property
    def score(self):
        return self._score

    @property
    def alphabet(self):
        return self._alphabet

    @property
    def mask(self):
        return self._mask

    @property
    def absent_words(self):
        return self._absletters

    @property
    def result(self):
        return self._result

    def bankrupt(self):
        self._score = 0

    def add_score(self, gain: int):
        self._score += gain

    def double_score(self):
        self._score *= 2

    def update_move(self, move: str):
        self._movequeue.append(move)

    def update_mask(self, mask: str):
        self._mask = mask

    def update_absent(self, letter: str):
        self._absletters.add(letter)

    def reset(self):
        self._mask = ''
        self._absletters.clear()
        self._score = 0

    def set_result(self, result: GameResult):
        self._result = result

    def reset_result(self):
        self._result = GameResult.NONE

    @abstractmethod
    def move(self):
        pass


class HumanPlayer(Player):
    def __init__(self, name: str, alphabet: str):
        super().__init__(name, alphabet)

    def move(self):
        while len(self._movequeue) == 0:
            pass
        return self._movequeue.popleft()


class CompPlayer(Player):
    def __init__(self, name: str, alphabet: str, dictfile: str, ai):
        super().__init__(name, alphabet)
        self.ai = ai
        self._words = []
        with open(dictfile, 'r') as f:
            while True:
                word = f.readline()
                if word == '':
                    break
                self._words.append(word.upper())

    @property
    def dictionary(self):
        return self._words

    def move(self):
        return self.ai(self)