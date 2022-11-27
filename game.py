from random import Random
from threading import Event
from enum import Enum
from players import Player, GameResult
from threading import Thread
import threading


class TestResult(Enum):
    NONE = -1,
    LETTER_CORRECT = 1,
    LETTER_INCORRECT = 0,
    WORD_CORRECT = 3,
    WORD_INCORRECT = 2,
    INVALID = -2,
    REPEAT = -3


class InvalidQueryException(Exception):
    def __init__(self, type: str):
        super().__init__()
        self.type = type

    @property
    def type(self):
        return self.type


class Game:
    WHEEL = [350, 400, 'x2', 600, 500, 1000, 600, 350, 300, 200, 500, 600, 400, 'B', 500, 350, 600, 400, 450, 500, 350, 600, '+', 400, 700, 600, 'x2', 600, 500, 400, 650, 450, 0, 1000, 500, 350, 550, 750, 600, 500]
    FILLER = '.'

    def __init__(self, dictfile: str):
        self.__words = []
        with open(dictfile, 'r') as f:
            while True:
                word = f.readline()
                if word == '':
                    break
                self.__words.append(word.upper().split('\n')[0])
        self.__playing = False
        self.__curword = ""
        self.__gen = Random()
        self.__mask = ""
        self.players = []
        self.test_done = Event()
        self.wheel_stop = Event()
        self.__test_res = TestResult.NONE
        self.__score = None
        self.__play_thread = None
        self.__last_move = ''
        self.__moves_done = set()
        self.__cur_player = None

    def start(self):
        self.test_done.clear()
        self.__curword = self.__words[self.__gen.randint(0, len(self.__words) - 1)]
        self.__mask = Game.FILLER * len(self.__curword)
        self.__moves_done.clear()
        print(self.__curword)
        self.__playing = True
        for player in self.players:
            player.reset()
            player.update_mask(self.__mask)
        self.__play_thread = Thread(target=self.__play)
        self.__play_thread.start()

    def stop(self):
        self.__playing = False

    @property
    def is_playing(self):
        return self.__playing

    @property
    def mask(self):
        return self.__mask

    @property
    def test_result(self):
        return self.__test_res

    @property
    def score(self):
        return self.__score

    @property
    def last_move(self):
        return self.__last_move

    @property
    def current_player(self):
        return self.__cur_player

    def announce_move(self, move: str):
        for player in self.players:
            player.update_move(move)

    def __test_letter(self, letter: str):
        if len(letter) != 1:
            raise InvalidQueryException('test_letter')
        letter = letter.upper()
        if not letter.isalpha():
            return TestResult.INVALID
        if letter not in self.__curword:
            return TestResult.LETTER_INCORRECT
        for i in range(len(self.__curword)):
            if self.__curword[i] == letter:
                self.__mask = self.__mask[:i] + self.__curword[i] + self.__mask[(i + 1):]
        return TestResult.LETTER_CORRECT

    def __test_word(self, word: str):
        if self.__curword != word.upper():
            return TestResult.WORD_INCORRECT
        self.__mask = word.upper()
        return TestResult.WORD_CORRECT

    def __player_loop(self):
        cur = 0
        while True:
            yield self.players[cur]
            cur = (cur + 1) % len(self.players)

    def __wheel_turns(self):
        while True:
            yield Game.WHEEL[self.__gen.randint(0, len(Game.WHEEL) - 1)]

    def __open_letter(self):
        pos = self.__gen.randint(0, len(self.__mask) - 1)
        self.__mask = self.__mask[:pos] + self.__curword[pos] + self.__mask[(pos + 1):]

    def __announce_mask(self):
        for player in self.players:
            player.update_mask(self.__mask)

    def __announce_letter_invalid(self, letter: str):
        for player in self.players:
            player.update_absent(letter)

    def __play(self):
        player_loop = self.__player_loop()
        self.__cur_player = next(player_loop)
        wheel_turns = self.__wheel_turns()
        set_next = False
        while True:
            if not self.__playing:
                break
            set_next = False
            self.__score = next(wheel_turns)
            if self.__score == '+':
                self.__open_letter()
                continue
            if self.__score in {'B', 0}:
                if self.__score == 'B':
                    self.__cur_player.bankrupt()
                self.__cur_player = next(player_loop)
                self.wheel_stop.set()
                while self.wheel_stop.is_set():
                    pass
                continue
            self.wheel_stop.set()
            while self.wheel_stop.is_set():
                pass
            self.__last_move = self.__cur_player.move().upper()
            if self.__last_move in self.__moves_done:
                self.__test_res = TestResult.REPEAT
                self.test_done.set()
                while self.test_done.is_set():
                    pass
                continue
            elif len(self.__last_move) == 1:
                self.__test_res = self.__test_letter(self.__last_move)
            else:
                self.__test_res = self.__test_word(self.__last_move)
                if self.__test_res == TestResult.WORD_INCORRECT:
                    self.__playing = False
                    self.__cur_player.set_result(GameResult.LOSE)
                    for another in self.players:
                        if self.__cur_player == another:
                            continue
                        another.set_result(GameResult.WON)
                    break
            self.__moves_done.add(self.__last_move)
            if self.__test_res == TestResult.LETTER_INCORRECT:
                self.__announce_letter_invalid(self.__last_move)
                set_next = True
            if self.__test_res in {TestResult.WORD_CORRECT, TestResult.LETTER_CORRECT}:
                if self.__score == 'x2':
                    self.__cur_player.double_score()
                else:
                    self.__cur_player.add_score(self.__score)
                if (self.__test_res == TestResult.WORD_CORRECT) or (self.__mask == self.__curword):
                    self.__playing = False
                    self.__cur_player.set_result(GameResult.WON)
                    for another in self.players:
                        if self.__cur_player == another:
                            continue
                        another.set_result(GameResult.LOSE)
            self.__announce_mask()
            self.test_done.set()
            if set_next:
                self.__cur_player = next(player_loop)
            while self.test_done.is_set():
                pass
        for player in self.players:
            if player.result == GameResult.LOSE:
                player.bankrupt()

