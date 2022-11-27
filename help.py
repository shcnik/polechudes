help = {
    'basics': '''\n
    Добро пожаловать в игру "Поле чудес"! Здесь вам предстоит отгадывать слова и получать за это очки.\n
    Список доступных команд:\n
    /help - выводит эту справку.
    /stats - выводит вашу статистику по играм.
    /top - выводит рейтинг игроков.
    /diff - устанавливает сложность игры.
    /play - запускает игру.
    /stop - останавливает игру.\n
    Для того, чтобы просмотреть справку по команде, наберите /help [команда]
    Для того, чтобы просмотреть правила игры, наберите /help game
    ''',
    'game': '''\n
    В начале игры ведущий загадывает слово и показывает вам, сколько в нём букв.\n
    По очереди ходите вы и компьютер (другой, не тот, что загадывает слово).\n
    В начале хода ведущий сообщает, сколько вам выпало очков, либо какой особый сектор вам выпал.\n
    Если вам выпали очки, далее игрок называет букву или слово.
    Если игрок назвал букву, ведущий отвечает, есть ли такая буква. Если есть - то ходит снова игрок, иначе ход переходит к другому.
    Если игрок назвал слово, то в случае правильного ответа игрок побеждает, иначе проигрывает.\n
    Помимо очков, игроку могут выпасть два особых сектора:\n
    Пропуск хода - игрок пропускает ход, не получая очков.
    Банкрот - игрок пропускает ход, все его очки сгорают.\n
    Игра продолжается, пока кто-то не угадает слово. Тот, кто угадал слово, выигрывает, проигравший теряет все свои очки.
    '''
}