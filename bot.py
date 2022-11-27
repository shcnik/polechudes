from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Command
from aiogram.utils import executor
import help
from game import Game, TestResult
import ai
import asyncio
from enum import Enum
import players
import csv
import datetime
import pandas

class InputMode(Enum):
    NONE = 0,
    ANSWER = 1,
    DIFF = 2

TOKEN = "5890292286:AAGjgLfnoE0WPqq_sXxl2j8CjL_wNhjAz90"
ALPHABET = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
games: dict[str, Game] = {}

input_mode = InputMode.NONE


def handle_correct_letter(message: types.Message):
    message.answer("Откройте букву ")


@dp.message_handler(commands=['start'])
async def process_start(message: types.Message):
    await message.answer("Добро пожаловать в игру 'Поле чудес'! "
                         "Для того, чтобы начать игру, введите /play. "
                         "Чтобы получить справку, введите /help."
                         "Для прекращения работы введите /exit.\n")
    games[message.from_user.username] = Game('words.txt')
    games[message.from_user.username].players.append(players.HumanPlayer(message.from_user.username, ALPHABET))
    games[message.from_user.username].players.append(players.CompPlayer('Компьютер', ALPHABET, 'words.txt', ai.easy_level))
    await bot.set_my_commands([
        types.BotCommand('play', 'Начать игру'),
        types.BotCommand('stats', 'Просмотреть свою статистику'),
        types.BotCommand('top', 'Просмотреть рейтинг игроков'),
        types.BotCommand('diff', 'Установить уровень сложности'),
        types.BotCommand('help', 'Запросить справку'),
        types.BotCommand('exit', 'Остановить бота')
    ])
    input_mode = InputMode.NONE


@dp.message_handler(commands=['exit', 'quit'])
async def process_exit(message: types.Message):
    await message.answer("До следующей встречи!")
    del games[message.from_user.username]


@dp.message_handler(commands=['help'])
async def process_help(message: types.Message, command: Command.CommandObj):
    if command.args is None:
        await message.answer(help.help['basics'])
    else:
        await message.answer(help.help[command.args])


@dp.message_handler(commands=['stats'])
async def process_stats(message: types.Message):
    dataset = pandas.read_csv('games.csv')
    dataset = dataset[['date', 'score']][dataset['player'] == message.from_user.username]
    await message.answer('`' + str(dataset[['score']].rename_axis('Дата')
                                   .rename(index=dataset['date'], columns={'score': 'Очки'})) + '`',
                         parse_mode=types.ParseMode.MARKDOWN)
    await message.answer('Всего вы набрали %d очков' % dataset['score'].sum())


@dp.message_handler(commands=['diff'])
async def process_setdiff(message: types.Message, command: Command.CommandObj):
    global input_mode
    if (command.args == '1') or (command.args == 'easy'):
        games[message.from_user.username].players[1].ai = ai.easy_level
        await message.answer("Установлен низкий уровень сложности.")
    elif (command.args == '2') or (command.args == 'medium'):
        games[message.from_user.username].players[1].ai = ai.mid_level
        await message.answer("Установлен средний уровень сложности.")
    elif (command.args == '3') or (command.args == 'hard'):
        games[message.from_user.username].players[1].ai = ai.hard_level
        await message.answer("Установлен высокий уровень сложности.")
    elif (command.args == None):
        await message.answer("Какой уровень сложности хотите (низкий, средний, высокий)?")
        input_mode = InputMode.DIFF
    else:
        await message.answer("Нет такого уровня сложности!")


@dp.message_handler(commands=['top'])
async def process_top(message: types.Message, command: Command.CommandObj):
    dataset = pandas.read_csv('games.csv')[['player', 'score']]
    dataset = dataset.groupby('player')[['score']]\
        .agg(sum)\
        .sort_values('score')
    if command.args != 'all':
        try:
            dataset = dataset.head(int(command.args) if command.args is not None else 10)
        except ValueError:
            await message.answer("Я не понимаю, сколько игроков вы хотите увидеть, выведу всех.")
    dataset['player'] = dataset.index
    dataset['number'] = list(range(1, dataset.count()['player'] + 1))
    await message.answer('`' + str(dataset.rename(index=dataset['number']).rename_axis(None)[['player', 'score']]
                                          .rename(columns={'player': 'Игрок', 'score': 'Очки'})) + '`',
                         parse_mode=types.ParseMode.MARKDOWN)


@dp.message_handler(commands=['play'])
async def process_play(message: types.Message):
    global input_mode
    await bot.set_my_commands([
        types.BotCommand('stop', 'Прекратить игру'),
        types.BotCommand('help', 'Запросить справку')
    ])
    input_mode = InputMode.ANSWER
    cur_game = games[message.from_user.username]
    cur_game.start()
    await message.answer('Загадано слово!')
    await message.answer(cur_game.mask)
    while cur_game.is_playing:
        await message.answer("%s, крутите барабан!" % cur_game.current_player.name)
        await asyncio.to_thread(cur_game.wheel_stop.wait)
        if cur_game.score == 'B':
            await message.answer("Поздравляю, вы банкрот!")
            cur_game.wheel_stop.clear()
            continue
        elif cur_game.score == 0:
            await message.answer("Увы, вы пропускаете ход!")
            cur_game.wheel_stop.clear()
            continue
        elif cur_game.score == 'x2':
            await message.answer("Удвоение очков! Буква?")
        elif cur_game.score == '+':
            await message.answer("Откройте какую-нибудь букву немедленно!")
            await message.answer(cur_game.mask)
            cur_game.wheel_stop.clear()
            continue
        else:
            await message.answer("%d очков. Буква?" % cur_game.score)
        cur_game.wheel_stop.clear()
        await asyncio.to_thread(cur_game.test_done.wait)
        if isinstance(cur_game.current_player, players.HumanPlayer):
            await message.answer(cur_game.last_move)
        test_res = cur_game.test_result
        if test_res == TestResult.LETTER_CORRECT:
            await message.answer("Откройте букву %s!" % cur_game.last_move)
            await message.answer(cur_game.mask)
        elif test_res == TestResult.LETTER_INCORRECT:
            await message.answer("Нет такой буквы!")
        elif test_res == TestResult.WORD_CORRECT:
            await message.answer("Поздравляем, вы угадали слово %s!" % cur_game.last_move)
        elif test_res == TestResult.WORD_INCORRECT:
            await message.answer("К сожалению, вы не угадали слово...")
        elif test_res == TestResult.REPEAT:
            await message.answer("Называли уже такую букву!")
        else:
            await message.answer("Я вас не понимаю, попробуйте ещё раз...")
        cur_game.test_done.clear()
    await message.answer("Игра окончена! Вы получили за неё %d очков" % cur_game.players[0].score)
    with open('games.csv', 'a') as f:
        writer = csv.DictWriter(f, fieldnames=['player', 'date', 'score'])
        writer.writerow({'player': cur_game.players[0].name,
                         'date': datetime.datetime.now().isoformat(sep=' ', timespec='minutes'),
                         'score': cur_game.players[0].score})
    await bot.set_my_commands([
        types.BotCommand('play', 'Начать игру'),
        types.BotCommand('stats', 'Просмотреть свою статистику'),
        types.BotCommand('top', 'Просмотреть рейтинг игроков'),
        types.BotCommand('diff', 'Установить уровень сложности'),
        types.BotCommand('help', 'Запросить справку'),
        types.BotCommand('exit', 'Остановить бота')
    ])
    input_mode = InputMode.NONE


@dp.message_handler(commands=['stop'])
async def process_stop(message: types.Message):
    global input_mode
    games[message.from_user.username].stop()
    await message.answer("Игрок нас покинул, увы!")
    await bot.set_my_commands([
        types.BotCommand('play', 'Начать игру'),
        types.BotCommand('stats', 'Просмотреть свою статистику'),
        types.BotCommand('top', 'Просмотреть рейтинг игроков'),
        types.BotCommand('diff', 'Установить уровень сложности'),
        types.BotCommand('help', 'Запросить справку'),
        types.BotCommand('exit', 'Остановить бота')
    ])
    input_mode = InputMode.NONE


@dp.message_handler()
async def process_answer(message: types.Message):
    global input_mode
    try:
        if input_mode == InputMode.ANSWER:
            cur_game = games[message.from_user.username]
            cur_game.announce_move(message.text)
        elif input_mode == InputMode.DIFF:
            if (message.text.lower() == 'легкий') or (message.text.lower() == 'лёгкий') or (message.text.lower() == 'низкий'):
                games[message.from_user.username].players[1].ai = ai.easy_level
                await message.answer("Установлен низкий уровень сложности.")
                input_mode = InputMode.NONE
            elif message.text.lower() == 'средний':
                games[message.from_user.username].players[1].ai = ai.mid_level
                await message.answer("Установлен средний уровень сложности.")
                input_mode = InputMode.NONE
            elif message.text.lower() == 'высокий':
                games[message.from_user.username].players[1].ai = ai.hard_level
                await message.answer("Установлен высокий уровень сложности.")
                input_mode = InputMode.NONE
            else:
                await message.answer("Нет такого уровня сложности! Попробуйте снова")
        else:
            await message.answer("Чтобы я с вами поговорил - начните игру!")
    except KeyError:
        await message.answer("Вы не начали игру!")


executor.start_polling(dp)
