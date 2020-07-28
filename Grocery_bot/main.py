"""
Телеграм бот для составления списка покупок
"""

from telebot import *
import os
import traceback

waiting_notification = False
pass_to_add = False
pass_to_keyword = False
cur_id = 0
login = 'Family'

bot = TeleBot('992012864:AAGWBqVjYfSIUAlhljxWmk2c9ZpRfeZk-Ew', threaded=False)
authenticated = False





def coma_to_dot(txt: str):
    """
    преобразование всех запятых в тексте в точки
    :param txt:
    :return:
    """
    res = ''
    for i in txt:
        if i == ',':
            res += '.'
        else:
            res += i
    return res


def notify(do, product):
    """
    уведомление всех участников семьи о покупке или добавлении в список
    срочного продукта
    :param do:
    :param product:
    """
    print('GOT TO NOTIFY')
    access_file = open('Family;participants.csv', encoding='UTF-8')
    for x in access_file:
        for i in x.split(','):
            print(i)
            if not i[0].isdigit():
                continue
            bot.send_message(int(i),
                             f'{product.capitalize()} {"куплен(a)" * int(do == "del") + "необходимо купить❗️" * int(do == "add")}')
    access_file.close()


def check(text: str):
    """
    проверка на наличие 'срочно' в тексте
    :param text:
    :return:
    """
    text = text.lower()
    return 'срочно' in text


def append_tuple(a: tuple, b: str):
    """
    добавление элемента в кортеж
    :param a:
    :param b:
    :return:
    """
    temp = []
    for i in a:
        temp.append(i)
    temp.append(b)
    return tuple(temp)


def append_file(filename: str, category: str, keyword: str):
    """
    добавление значения в файл
    :param filename: имя файла
    :param category: категория в которую надо добавить элемент
    :param keyword: элемент
    """
    dummyfile = filename + '.bak'
    with open(filename, encoding='UTF-8') as orig_file, open(dummyfile, 'w',
                                                                    encoding='UTF-8') as temp_file:
        for line in orig_file:
            if line.split(';')[0] == category:
                temp_file.write(line[:-1] + ',' + keyword + '\n')
            else:
                temp_file.write(line)
    os.remove(filename)
    os.rename(dummyfile, filename)


def delete_line(original_file, line_number):
    """ Delete a line from a file at the given line number """
    is_skipped = False
    current_index = 0
    dummy_file = original_file + '.bak'
    # Open original file in read only mode and dummy file in write mode
    with open(original_file, encoding='UTF-8') as read_obj, open(dummy_file, 'w',
                                                                        encoding='UTF-8') as write_obj:
        # Line by line copy data from original file to dummy file
        for line in read_obj:
            # If current line number matches the given line number then skip copying
            if current_index != line_number:
                write_obj.write(line)
            else:
                is_skipped = True
            current_index += 1

    # If any line is skipped then rename dummy file as original file
    if is_skipped:
        os.remove(original_file)
        os.rename(dummy_file, original_file)
    else:
        os.remove(dummy_file)


def UA(user):
    """
    проверка на авторизацию
    :param user:
    :return:bool
    """
    print(user)
    access_file = open('Family;participants.csv', encoding='UTF-8')
    for i in access_file:
        print(i.split(','))
        if str(user) in i.split(','):
            access_file.close()
            return True
    bot.send_message(354640082, f'{user}/Пытался получить доступ')
    access_file.close()
    return False


with open('Category_product.csv', encoding='UTF-8') as file:
    category_product = {}
    a = True
    for line in file:
        if a:
            a = False
            continue
        temp = []
        for i in line.split(';')[1].split(','):
            temp.append(i)
        category_product[line.split(';')[0]] = tuple(temp[:-1])


@bot.message_handler(commands=['help'])
def helper(msg):
    """
    Вывод сообщения помощи
    :param msg:
    """
    bot.send_message(msg.chat.id,
                     'Бот, созданный для помощи в составлении списка покупок семьям.\n\n\n'
                     '/start - команда начинающая ваше взаимодействие с ботом, в случае, если у вас появятся проблемы с авторизацией - пропишите её\n\n'
                     '/list - показывает список покупок и позволяет вычёркивать купленные продукты, в случае, если продуктов больше 10 - показывает категории, по нажатию на которые, вы увидите продукты в данной категории\n\n'
                     '/add_keyword - если вы заметили, что определённый продукт оказывается в категории "Другое", но его можно определить в одну из существующих категорий нажмите на эту команду и следуйте инструкциям\n\n\n'
                     'Чтобы добавить продукт просто напишите его в этот чат, помимо самого продукта можно писать необходимое количество, комментарии и всё что вашей душе угодно\n\n'
                     '/help - выведет это сообщение\n\n\n'
                     'Created by: @artem_pas')


@bot.message_handler(commands=['start'])
def start_message(message):
    """
    Запуск бота
    """
    print(message.chat.username)
    if UA(message.chat.id):
        global login
        login = 'Family'
        print('found', login)
        bot.send_message(message.chat.id, f'Пользователь найден\nВы подключены к семье')
        global authenticated
        authenticated = True
    else:
        bot.send_message(message.chat.id,
                         f'Пользователь не найден. Обратитесь к @artem_pas для получения доступа к боту.\nКод, который необходимо предоставить:\n{message.chat.id}')


@bot.message_handler(commands=['list'])
def show_list(msg):
    """
    отображение списка продуктов
    :param msg:
    """
    global list
    global file
    if UA(msg.chat.id):
        with open(login + '.csv', encoding='UTF-8') as file:
            list = {}
            cnt = 0
            for i in file:
                print(i)
                if i == 'Category,Product\n':
                    continue
                else:
                    if i.split(',')[0] in list:
                        list[i.split(',')[0]].append(i.split(',')[1])
                        cnt += 1
                    else:
                        list[i.split(',')[0]] = [i.split(',')[1]]
                        cnt += 1
                    print(list, cnt)

        message = 'Список покупок:\n'
        for i in list:
            message += '\n'+i + ':\n'
            for x in list[i]:
                message += f'{list[i].index(x) + 1}) {x}'
        ans = types.InlineKeyboardMarkup(row_width=2)
        if cnt >= 10:
            for i in list:
                ans.add(types.InlineKeyboardButton(i, callback_data=f'c,{i}'))
        else:
            for i in list:
                for x in list[i]:
                    if x[1].isupper():
                        ans.add(types.InlineKeyboardButton('✅❗️' + x + '❗️', callback_data=f'p,{x}'))
                    else:
                        ans.add(types.InlineKeyboardButton('✅' + x, callback_data=f'p,{x}'))
        bot.send_message(msg.chat.id, message, reply_markup=ans)
    else:
        bot.send_message(msg.chat.id, 'Для получания доступа к боту обратитесь к @artem_pas')


@bot.callback_query_handler(func=lambda msg: 'c' in msg.data.split(','))
def show_products_in_category(msg):
    """
    отображение продуктов в категории если продуктов больше 10-ти
    :param msg:
    """
    if UA(msg.message.chat.id):
        global list
        print(((len(list[msg.data.split(',')[1]])-1)//10)+1)
        keyboard = types.InlineKeyboardMarkup(row_width=((len(list[msg.data.split(',')[1]])-1)//10)+1)
        for i in list[msg.data.split(',')[1]]:
            if i[1].isupper():
                keyboard.add(types.InlineKeyboardButton('✅❗️' + i + '❗️', callback_data=f'p,{i}'))
            else:
                keyboard.add(types.InlineKeyboardButton('✅' + i, callback_data=f'p,{i}'))
        bot.edit_message_reply_markup(message_id=msg.message.message_id, chat_id=msg.message.chat.id,
                                      reply_markup=keyboard)
    else:
        bot.send_message(msg.chat.id, 'Для получания доступа к боту обратитесь к @artem_pas')


@bot.callback_query_handler(func=lambda msg: 'p' in msg.data.split(','))
def remove_product(msg):
    """
    удаление продукта
    :param msg:
    """
    print('!!!!', msg.message.chat.id)
    found = False
    if UA(msg.message.chat.id):
        with open(login + '.csv', encoding='UTF-8') as f:
            cnt = -1
            for line in f:
                cnt += 1
                if msg.data.split(',')[1] in line:
                    found = True
                    break
                else:
                    continue
            if not found:
                bot.send_message(msg.message.chat.id, 'Возникла ошибка попробуйте отправить /list заново')
                return
        delete_line(login + '.csv', cnt)
        bot.send_message(msg.message.chat.id, f'{msg.data.split(",")[1]} успешно вычеркнут(а) из списка')
        with open(login + '.csv', encoding='UTF-8') as file:
            list = {}
            cnt = 0
            for i in file:
                print(i)
                if i == 'Category,Product\n':
                    continue
                else:
                    if i.split(',')[0] in list:
                        list[i.split(',')[0]].append(i.split(',')[1])
                        cnt += 1
                    else:
                        list[i.split(',')[0]] = [i.split(',')[1]]
                        cnt += 1
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        if cnt >= 10:
            for i in list:
                keyboard.add(types.InlineKeyboardButton(i, callback_data=f'c,{i}'))
        else:
            for i in list:
                for x in list[i]:
                    if x[1].isupper():
                        keyboard.add(types.InlineKeyboardButton('✅❗️' + x + '❗️', callback_data=f'p,{x}'))
                    else:
                        keyboard.add(types.InlineKeyboardButton('✅' + x, callback_data=f'p,{x}'))
        message = 'Список покупок:\n'
        for i in list:
            message += '\n' + i + ':\n'
            for x in list[i]:
                message += f'{list[i].index(x) + 1}) {x}'
        bot.edit_message_text(message_id=msg.message.message_id, chat_id=msg.message.chat.id, text=message,
                              reply_markup=keyboard)
        if msg.data.split(',')[1].isupper():
            notify('del', msg.data.split(',')[1])
    else:
        bot.send_message(msg.chat.id, 'Для получания доступа к боту обратитесь к @artem_pas')


@bot.message_handler(commands=['add_keyword'])
def choose_category(msg):
    """
    начало добавления ключевого слова
    запрос категории
    :param msg:
    """
    if UA(msg.chat.id):
        global keyboard
        keyboard = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
        for i in category_product:
            keyboard.add(types.KeyboardButton(i))
        bot.send_message(msg.chat.id, 'Выберите категорию в которую вы хотите добавить ключевое слово',
                         reply_markup=keyboard)
        global cur_id
        global pass_to_keyword
        cur_id = msg.chat.id
        pass_to_keyword = True
    else:
        bot.send_message(msg.chat.id, 'Для получания доступа к боту обратитесь к @artem_pas')


@bot.message_handler(func=lambda msg: msg.chat.id == cur_id and pass_to_keyword)
def add_keyword(msg):
    """
    запрос ключевого слова
    :param msg:
    """
    global category
    global pass_to_keyword
    global pass_to_add
    category = msg.text
    bot.send_message(msg.chat.id, 'Введите ключевое слово:', reply_markup=types.ReplyKeyboardRemove())
    pass_to_keyword = False
    pass_to_add = True


@bot.message_handler(func=lambda msg: cur_id == msg.chat.id and pass_to_add)
def adding_keyword(msg):
    """
    добавление полученного ключевого слова
    :param msg:
    """
    global pass_to_add
    global cur_id
    pass_to_add = False
    cur_id = 0
    category_product[category] = append_tuple(category_product[category], msg.text)
    append_file('Category_product.csv', category, msg.text)
    bot.send_message(msg.chat.id, f'{msg.text} добавлен(а) в список ключевых слов')


@bot.message_handler(func=lambda msg: '/add' in msg.text.split())
def add_person(msg):
    """
    добавление человека в семью
    :param msg:
    """
    if msg.chat.username == 'artem_pas':
        if len(msg.text.split()) == 1:
            bot.send_message(msg.chat.id, 'Пример команды добавления\n/add 703247892\n/add id:int')
        else:
            with open('Family;participants.csv', 'a', encoding='UTF-8') as writer:
                writer.write(f',{msg.text.split()[1]}')
            bot.send_message(msg.chat.id, f'{msg.text.split()[1]} добавлен(а) в семью')
            bot.send_message(msg.text.split()[1], '@artem_pas пригласил вас в семью')
    else:
        bot.send_message(msg.chat.id, '❌У вас нет доступа к этой команде❌')


@bot.message_handler(commands=['clear_list'])
def clear_list(msg):
    if UA(msg.chat.id):
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton('✅ Да, удалить!', callback_data=str(msg.chat.id)+'&clear&yes'))
        keyboard.add(types.InlineKeyboardButton('❌ Нет, не удалять', callback_data=str(msg.chat.id)+'&clear&no'))
        bot.send_message(msg.chat.id, 'Вы уверены, что хотите полностью очистить список?\n❗️ЭТО ДЕЙСТВИЕ БУДЕТ НЕВОЗМОЖНО ОТМЕНИТЬ❗️', reply_markup=keyboard)
    else:
        bot.send_message(msg.chat.id, 'Для получания доступа к боту обратитесь к @artem_pas')


@bot.callback_query_handler(func=lambda msg: msg.data.split('&')[1] == 'clear')
def clear_confirmed(msg):
    if UA(msg.message.chat.id):
        msg.data = [str(i) for i in msg.data.split('&')]
        if msg.data[2] == 'yes':
            with open(login + '.csv', 'w', encoding='UTF-8') as file:
                file.write('Category;Product\n')
            bot.edit_message_text('Список успешно очищен', chat_id=msg.message.chat.id, message_id=msg.message.message_id)
        else:
            bot.edit_message_text('Очистка отменена', chat_id=msg.message.chat.id, message_id=msg.message.message_id)
    else:
        bot.send_message(msg.chat.id, 'СОВСЕМ ОБНАГЛЕЛ?')


@bot.message_handler(func=lambda msg: waiting_notification)
def notification(msg):
    global waiting_notification
    waiting_notification = False
    access_file = open('Family;participants.csv', encoding='UTF-8')
    for x in access_file:
        for i in x.split(','):
            print(i)
            if not i[0].isdigit():
                continue
            bot.send_message(i, msg.text)
    access_file.close()


@bot.message_handler(commands=['notify'])
def notify(msg):
    if UA(msg.chat.id):
        bot.send_message(msg.chat.id, 'Enter notification text:')
        global waiting_notification
        waiting_notification = True
    else:
        pass


@bot.message_handler(content_types=['text'])
def add_product(msg):
    """
    добавление продукта в список
    :param msg:
    """
    global file
    category = "Другое"
    if UA(msg.chat.id):
        if len(msg.text) > 62:
            msg.text = msg.text[0:63]
        text = [str(i).lower() for i in coma_to_dot(msg.text).split()]
        found = False
        for i in text:
            if found:
                break
            elif i[0].isdigit():
                continue
            else:
                for x in category_product:
                    if i in category_product[x]:
                        category = x
                        found = True
        if 'срочно' in msg.text.lower():
            txt = ''
            for i in coma_to_dot(msg.text).split():
                if i.lower() == 'срочно':
                    continue
                else:
                    txt += i.upper() + ' '
            with open(login + '.csv', 'a', encoding='UTF-8') as file:
                file.write(category + ',' + txt + '\n')
            bot.send_message(msg.chat.id, txt + ' успешно добавлен(а) в список, как срочный продукт')
            notify('add', txt)
        else:
            with open(login + '.csv', 'a', encoding='UTF-8') as file:
                file.write(category + ',' + coma_to_dot(msg.text).capitalize() + '\n')
            bot.send_message(msg.chat.id, coma_to_dot(msg.text) + ' успешно добавлен(а) в список')
    else:
        bot.send_message(msg.chat.id, 'Для получания доступа к боту обратитесь к @artem_pas')


while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        traceback.print_exc()
        bot.send_message(354640082, 'ОШИБКА!!!\n' * 3 + str(e))
        time.sleep(15)
