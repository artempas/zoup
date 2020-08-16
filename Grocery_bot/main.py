"""
Телеграм бот для составления списка покупок
"""

from telebot import *
import os
import traceback
import database as db
import mytoken

currently_forbidden_familynames = ['families', 'category_product', 'users_database']
transfering_logins = {}
bot = TeleBot(mytoken.token, threaded=False)
authenticated = False
db.create_table('Users_database', {'User_id': 'INTEGER', 'Username': 'TEXT', 'Family': 'TEXT'})
db.create_table('Families', {'Family': 'TEXT', 'Password': 'TEXT'})


def form_list_dict(msg):
    """
    Формирует словарь {категория:продукт} относящийся к семье отправителя
    :param msg:
    :return:
    """
    family = db.read_table('Users_database', column='id', value=msg.chat.id)[2]
    cat_prod = db.read_table(family)
    cat_prod_dict = {}
    for line in cat_prod:
        if line[0] in cat_prod_dict.keys():
            cat_prod_dict[line[0]].append(line[1])
        else:
            cat_prod_dict[line[0]] = []
    return cat_prod_dict


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


def notify(do, product, family):
    """
    уведомление всех участников семьи о покупке или добавлении в список
    срочного продукта
    :param do:
    :param product:
    """
    print('GOT TO NOTIFY')
    users_list = db.read_table('Users_database')
    for user in users_list:
        if user[2] == family:
            print(user[1])
            try:
                bot.send_message(user[0],
                                 f'{product.capitalize()} {"куплен(a)" * int(do == "del") + "необходимо купить❗️" * int(do == "add")}')
            except Exception as e:
                traceback.print_exc()
                bot.send_message(354640082, 'ОШИБКА!!!\n' * 3 + str(e))


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


# TODO append_file ПОСМОТРЕТЬ ЗАЧЕМ НУЖНА
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


# TODO нужна ли?
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
                     '/help - выведет это сообщение\n'
                     '/register - создать семью\n'
                     '/join - присоединиться к существующей семье\n\n\n'
                     'Created by: @artem_pas')


'''ОТСЮДА ГОТОВО'''


@bot.message_handler(commands=['register'])
def register(msg):
    bot.send_message(msg.chat.id, 'Придумайте логин для семьи:')
    bot.register_next_step_handler(msg, create_family)


def create_family(msg):
    global currently_forbidden_familynames
    entered_family = msg.text.lower()
    not_in_db = True
    families = db.read_table('Families')
    for family in families:
        if family[0] != entered_family:
            continue
        else:
            not_in_db = False
    if entered_family not in currently_forbidden_familynames and not_in_db and entered_family not in transfering_logins.values():
        bot.send_message(msg.chat.id, 'Логин удовлетворяет условиям\nВведите пароль:')
        bot.register_next_step_handler(msg, final_register)
        transfering_logins[msg.chat.id] = entered_family
    else:
        bot.send_message(msg.chat.id, 'Такой логин уже существует, попробуйте другой')
        bot.register_next_step_handler(msg, final_register)


def final_register(msg):
    password = msg.text
    bot.send_message(msg.chat.id, db.add_record('Families', (transfering_logins[msg.chat.id], password)))
    db.create_table(transfering_logins[msg.chat.id], {'Category': 'TEXT', 'Product': 'TEXT'})
    bot.send_message(msg.chat.id,
                     db.add_record('Users_database', (msg.chat.id, msg.chat.username, transfering_logins[msg.chat.id])))
    bot.send_message(msg.chat.id,
                     f'Семья успешно создана\nЛогин - {transfering_logins[msg.chat.id]}\nПароль - {password}')
    del (transfering_logins[msg.chat.id])


'''ДОЮСДА ГОТОВО'''


@bot.message_handler(commands=['start'])
def start_message(message):
    """
    Запуск бота
    """
    print(message.chat.username)
    helper(message)


@bot.message_handler(commands=['list'])
def show_list(msg):
    """
    отображение списка продуктов
    :param msg:
    """
    if len(db.read_table('Users_database', column='id', value=msg.chat.id)) != 0:
        cat_prod_dict = form_list_dict(msg)
        message = 'Список покупок:\n'
        for category in cat_prod_dict:
            message += '\n' + category + ':\n'
            for product in cat_prod_dict[category]:
                message += f'{cat_prod_dict[category].index(product) + 1}) {product}'
        ans = types.InlineKeyboardMarkup(row_width=2)
        if len(cat_prod_dict.values()) >= 10:
            for i in cat_prod_dict:
                ans.add(types.InlineKeyboardButton(i, callback_data=f'c,{i}'))
        else:
            for i in cat_prod_dict:
                for x in cat_prod_dict[i]:
                    if x[1].isupper():
                        ans.add(types.InlineKeyboardButton('✅❗️' + x + '❗️', callback_data=f'p,{x}'))
                    else:
                        ans.add(types.InlineKeyboardButton('✅' + x, callback_data=f'p,{x}'))
        bot.send_message(msg.chat.id, message, reply_markup=ans)
    else:
        bot.send_message(msg.chat.id, 'Вы не авторизованы')


@bot.callback_query_handler(func=lambda msg: 'c' in msg.data.split(','))
def show_products_in_category(msg):
    """
    отображение продуктов в категории если продуктов больше 10-ти
    :param msg:
    """
    list_dict = form_list_dict(msg.message)
    keyboard = types.InlineKeyboardMarkup(row_width=((len(list_dict[msg.data.split(',')[1]]) - 1) // 10) + 1)
    for i in list_dict[msg.data.split(',')[1]]:
        if i[1].isupper():
            keyboard.add(types.InlineKeyboardButton('✅❗️' + i + '❗️', callback_data=f'p,{i}'))
        else:
            keyboard.add(types.InlineKeyboardButton('✅' + i, callback_data=f'p,{i}'))
    bot.edit_message_reply_markup(message_id=msg.message.message_id, chat_id=msg.message.chat.id,
                                  reply_markup=keyboard)


@bot.callback_query_handler(func=lambda msg: 'p' in msg.data.split(','))
def remove_product(msg):
    family = db.read_table('Users_database', column='id', value=msg.chat.id)[2]
    if db.remove_record(family, column='Product', value=msg.data.split(',')[1]):
        bot.send_message(msg.message.chat.id, f'{msg.data.split(",")[1]} успешно вычеркнут(а) из списка')
    else:
        bot.send_message(msg.message.chat.id, f'{msg.data.split(",")[1]} удалить не удалось :(')
    cat_prod_dict = form_list_dict(msg.message)
    message = 'Список покупок:\n'
    for category in cat_prod_dict:
        message += '\n' + category + ':\n'
        for product in cat_prod_dict[category]:
            message += f'{cat_prod_dict[category].index(product) + 1}) {product}'
    ans = types.InlineKeyboardMarkup(row_width=2)
    if len(cat_prod_dict.values()) >= 10:
        for i in cat_prod_dict:
            ans.add(types.InlineKeyboardButton(i, callback_data=f'c,{i}'))
    else:
        for i in cat_prod_dict:
            for x in cat_prod_dict[i]:
                if x[1].isupper():
                    ans.add(types.InlineKeyboardButton('✅❗️' + x + '❗️', callback_data=f'p,{x}'))
                else:
                    ans.add(types.InlineKeyboardButton('✅' + x, callback_data=f'p,{x}'))
    bot.edit_message_text(message_id=msg.message.message_id, chat_id=msg.message.chat.id, text=message,
                          reply_markup=ans)
    if msg.data.split(',')[1].isupper():
        notify('del', msg.data.split(',')[1], family)


# TODO Временно отключено

# @bot.message_handler(commands=['add_keyword'])
# def choose_category(msg):
#     """
#     начало добавления ключевого слова
#     запрос категории
#     :param msg:
#     """
#     if UA(msg.chat.id):
#         global keyboard
#         keyboard = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
#         for i in category_product:
#             keyboard.add(types.KeyboardButton(i))
#         bot.send_message(msg.chat.id, 'Выберите категорию в которую вы хотите добавить ключевое слово',
#                          reply_markup=keyboard)
#         global cur_id
#         global pass_to_keyword
#         cur_id = msg.chat.id
#         pass_to_keyword = True
#     else:
#         bot.send_message(msg.chat.id, 'Для получания доступа к боту обратитесь к @artem_pas')


# TODO переделать

# @bot.message_handler(func=lambda msg: msg.chat.id == cur_id and pass_to_keyword)
# def add_keyword(msg):
#     """
#     запрос ключевого слова
#     :param msg:
#     """
#     global category
#     global pass_to_keyword
#     global pass_to_add
#     category = msg.text
#     bot.send_message(msg.chat.id, 'Введите ключевое слово:', reply_markup=types.ReplyKeyboardRemove())
#     pass_to_keyword = False
#     pass_to_add = True


# TODO на переработку

# @bot.message_handler(func=lambda msg: cur_id == msg.chat.id and pass_to_add)
# def adding_keyword(msg):
#     """
#     добавление полученного ключевого слова
#     :param msg:
#     """
#     global pass_to_add
#     global cur_id
#     pass_to_add = False
#     cur_id = 0
#     category_product[category] = append_tuple(category_product[category], msg.text)
#     append_file('Category_product.csv', category, msg.text)
#     bot.send_message(msg.chat.id, f'{msg.text} добавлен(а) в список ключевых слов')


@bot.message_handler(commands=['clear_list'])
def clear_list(msg):
    if len(db.read_table('Users_database', column='id', value=msg.chat.id)) != 0:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton('✅ Да, удалить!', callback_data=str(msg.chat.id) + '&clear&yes'))
        keyboard.add(types.InlineKeyboardButton('❌ Нет, не удалять', callback_data=str(msg.chat.id) + '&clear&no'))
        bot.send_message(msg.chat.id,
                         'Вы уверены, что хотите полностью очистить список?\n❗️ЭТО ДЕЙСТВИЕ БУДЕТ НЕВОЗМОЖНО ОТМЕНИТЬ❗️',
                         reply_markup=keyboard)
    else:
        bot.send_message(msg.chat.id, 'Вы не авторизованы')


@bot.callback_query_handler(func=lambda msg: msg.data.split('&')[1] == 'clear')
def clear_confirmed(msg):
    msg.data = [str(i) for i in msg.data.split('&')]
    if msg.data[2] == 'yes':
        if db.remove_record(db.read_table('Users_database',
                                          column='id',
                                          value=msg.message.chat.id),
                            '*',
                            '*'):
            bot.edit_message_text('Список успешно очищен',
                                  chat_id=msg.message.chat.id,
                                  message_id=msg.message.message_id)
        else:
            bot.edit_message_text('Во время очистки произошла ошибка, обратитесь к @artem_pas',
                                  chat_id=msg.message.chat.id,
                                  message_id=msg.message.message_id)
    else:
        bot.edit_message_text('Очистка отменена', chat_id=msg.message.chat.id, message_id=msg.message.message_id)


@bot.message_handler(func=lambda msg: waiting_notification and msg.chat.username == 'artem_pas')
def notification(msg):
    global waiting_notification
    waiting_notification = False
    users = db.read_table('Users_database')
    errors = []
    for user in users:
        try:
            bot.send_message(user[1], msg.text)
        except Exception as e:
            errors.append(str(user[1]) + ' - ' + str(e))
    if len(errors) > 0:
        bot.send_message(354640082, str(errors))


# TODO ПЕРЕДЕЛАТЬ КАТЕГОРИЗАЦИЮ
# @bot.message_handler(content_types=['text'])
# def add_product(msg):
#     """
#     добавление продукта в список
#     :param msg:
#     """
#     global file
#     category = "Другое"
#     if UA(msg.chat.id):
#         if len(msg.text) > 62:
#             msg.text = msg.text[0:63]
#         text = [str(i).lower() for i in coma_to_dot(msg.text).split()]
#         found = False
#         for i in text:
#             if found:
#                 break
#             elif i[0].isdigit():
#                 continue
#             else:
#                 for x in category_product:
#                     if i in category_product[x]:
#                         category = x
#                         found = True
#         if 'срочно' in msg.text.lower():
#             txt = ''
#             for i in coma_to_dot(msg.text).split():
#                 if i.lower() == 'срочно':
#                     continue
#                 else:
#                     txt += i.upper() + ' '
#             with open(login + '.csv', 'a', encoding='UTF-8') as file:
#                 file.write(category + ',' + txt + '\n')
#             bot.send_message(msg.chat.id, txt + ' успешно добавлен(а) в список, как срочный продукт')
#             notify('add', txt)
#         else:
#             with open(login + '.csv', 'a', encoding='UTF-8') as file:
#                 file.write(category + ',' + coma_to_dot(msg.text).capitalize() + '\n')
#             bot.send_message(msg.chat.id, coma_to_dot(msg.text) + ' успешно добавлен(а) в список')
#     else:
#         bot.send_message(msg.chat.id, 'Для получания доступа к боту обратитесь к @artem_pas')


@bot.message_handler(commands=['notify'])
def notif(msg):
    if msg.chat.username == 'artem_pas':
        bot.send_message(msg.chat.id, 'Enter notification text:')
        global waiting_notification
        waiting_notification = True
    else:
        bot.send_message(msg.chat.id, 'This command is unavailable for you')


if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            traceback.print_exc()
            bot.send_message(354640082, 'ОШИБКА!!!\n' * 3 + str(e))
            time.sleep(1)
