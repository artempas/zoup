"""
Телеграм бот для составления списка покупок
"""

from telebot import *
import os
import traceback
from Grocery_bot import database_module as db  # TODO исправить перед заливом
import mytoken

currently_forbidden_familynames = ['families', 'category_product', 'users_database', 'transfering_logins']
bot = TeleBot(mytoken.token, threaded=False)
authenticated = False
waiting_notification = False
db.create_table('Users_database', {'User_id': 'INTEGER', 'Username': 'TEXT', 'Family': 'TEXT'})
db.create_table('Families', {'Family': 'TEXT', 'Password': 'TEXT'})


def form_list_dict(msg):
    """
    Формирует словарь {категория:продукт} относящийся к семье отправителя
    :param msg:
    :return:
    """
    family = db.read_table('Users_database', column_name='id', value=msg.chat.id)[0][2]
    cat_prod = db.read_table(family)
    print('form_list_dict -> orig', cat_prod)
    cat_prod_dict = {}
    for line in cat_prod:
        if line[0] in cat_prod_dict.keys():
            cat_prod_dict[line[0]].append(line[1])
        else:
            cat_prod_dict[line[0]] = [line[1]]
    if 'Другое' in cat_prod_dict.keys():
        if list(cat_prod_dict.keys())[-1] != 'Другое':
            temp = cat_prod_dict['Другое']
            del (cat_prod_dict['Другое'])
            cat_prod_dict['Другое'] = temp
    return cat_prod_dict


def notify(do, product, family, username=None):
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
                if do == 'del' or do == 'add':
                    bot.send_message(user[0],
                                     username + 'срочно просит купить' * int(do == "add") + 'купил(a)' * int(
                                         do == "del") + {product.capitalize()})
                elif do == 'welcome':
                    bot.send_message(user[0], f'@{product} присоединился(ась) к семье')
                elif do == 'change':
                    bot.send_message(user[0], f'@{username} сменил пароль семьи\nНовый пароль - {product}')
            except Exception as e:
                traceback.print_exc()


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
        if family[0] == entered_family:
            not_in_db = False
    not_in_transfering_logins = True
    for family_name in db.read_table('Transfering_logins'):
        if family_name[1] == entered_family:
            not_in_transfering_logins = False
    if entered_family not in currently_forbidden_familynames and not_in_db and not_in_transfering_logins:
        bot.send_message(msg.chat.id, 'Логин удовлетворяет условиям\nВведите пароль:')
        bot.register_next_step_handler(msg, final_register)
        db.add_record('transfering_logins', (msg.chat.id, entered_family))
    else:
        bot.send_message(msg.chat.id, 'Такой логин уже существует, попробуйте другой')
        bot.register_next_step_handler(msg, create_family)


def final_register(msg):
    login = db.read_table('transfering_logins', 'chat_id', msg.chat.id)[0][1]
    password = msg.text
    bot.send_message(msg.chat.id, db.add_record('Families', (login, password)))
    db.create_table(login, {'Category': 'TEXT', 'Product': 'TEXT'})
    bot.send_message(msg.chat.id,
                     db.add_record('Users_database', (msg.chat.id, msg.chat.username, login)))
    if db.remove_record('Transfering_logins', 'chat_id', msg.chat.id):
        bot.send_message(msg.chat.id, f'Семья успешно создана\nЛогин - {login}\nПароль - {password}')
    else:
        bot.send_message(msg.chat.id, 'Что-то пошло не так, попробуйте ещё раз\n/register')


@bot.message_handler(commands=['join'])
def log_in__ask_login(msg):
    bot.send_message(msg.chat.id, 'Логин:')
    bot.register_next_step_handler(msg, log_in__enter_login)


def log_in__enter_login(msg):
    if len(db.read_table('Families', column_name='Family', value=msg.text.lower())) > 0:
        db.add_record('Transfering_logins', (msg.chat.id, msg.text.lower()))
        bot.send_message(msg.chat.id, 'Введите пароль:')
        bot.register_next_step_handler(msg, log_in__enter_password)
    else:
        bot.send_message(msg.chat.id, 'Семья не найдена, попробуйте еще раз\nЛогин:')
        bot.register_next_step_handler(msg, log_in__enter_login)


def log_in__enter_password(msg):
    try:
        login = db.read_table('Transfering_logins', column_name='chat_id', value=msg.chat.id)[0][1]
    except IndexError or ValueError:
        bot.send_message(msg.chat.id, 'Попробуйте пройти процесс входа заново\n/join')
        return None
    if db.read_table('Families', 'Family', login)[0][1] == msg.text:
        bot.send_message(msg.chat.id, db.add_record('Users_database', (msg.chat.id, msg.chat.username, login)))
        bot.send_message(msg.chat.id, f'Вы вошли в семью {login}')
        notify('welcome', msg.chat.username, login)
    else:
        keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        keyboard.add(types.KeyboardButton('Попробовать ввести логин ещё раз'))
        keyboard.add(types.KeyboardButton('Попробовать ввести пароль ещё раз'))
        keyboard.add(types.KeyboardButton('Отмена'))
        bot.send_message(msg.chat.id, 'Неверный пароль\nПопробовать ещё раз?', reply_markup=keyboard)
        bot.register_next_step_handler(msg, wrong_password)


def wrong_password(msg):
    if msg.text == 'Попробовать ввести логин ещё раз':
        bot.send_message(msg.chat.id, 'Логин:', reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, log_in__enter_login)
    elif msg.text == 'Попробовать ввести пароль ещё раз':
        bot.send_message(msg.chat.id, 'Пароль:', reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, log_in__enter_password)
    else:
        bot.send_message(msg.chat.id, 'Процедура входа отменена', reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(commands=['start'])
def start_message(message):
    """
    Запуск бота
    """
    print(message.chat.username)
    helper(message)


@bot.message_handler(commands=['show_password'])
def show_password(msg):
    if len(db.read_table('Users_database', column_name='id', value=msg.chat.id)) != 0:
        family = db.read_table('Users_database', column_name='id', value=msg.chat.id)[0][2]
        password = db.read_table('families', column_name='Family', value=family)[0][1]
        bot.send_message(msg.chat.id, f'Логин семьи - {family}\nПароль - {password}')


@bot.message_handler(commands=['change_password'])
def change_password(msg):
    bot.send_message(msg.chat.id, 'Введите новый пароль:')
    bot.register_next_step_handler(msg, change_password2)


def change_password2(msg):
    family = db.read_table('Users_database', 'id', msg.chat.id)[0][2]
    if db.update_record('Families', column_name='Family', search_value=family, change_column='password',
                        new_value=msg.text):
        notify('change', msg.text, family, msg.chat.username)
    else:
        bot.send_message(msg.chat.id,
                         'При смене пароля произошла ошибка, попробуйте позже\nВы всегда можете воспользоваться /show_password')


@bot.message_handler(commands=['list'])
def show_list(msg):
    """
    отображение списка продуктов
    :param msg:
    """
    if len(db.read_table('Users_database', column_name='id', value=msg.chat.id)) != 0:
        cat_prod_dict = form_list_dict(msg)
        print(cat_prod_dict)
        message = 'Список покупок:\n'
        for category in cat_prod_dict:
            message += '\n' + category + ':\n'
            for product in cat_prod_dict[category]:
                message += f'{cat_prod_dict[category].index(product) + 1}) {product}\n'
        ans = types.InlineKeyboardMarkup(row_width=2)
        lena = 0
        for i in cat_prod_dict:
            for x in cat_prod_dict[i]:
                lena += 1
        if lena >= 10:
            for i in cat_prod_dict:
                ans.add(types.InlineKeyboardButton(i, callback_data=f'c&{i}'))
        else:
            for i in cat_prod_dict:
                for x in cat_prod_dict[i]:
                    if x[1].isupper():
                        ans.add(types.InlineKeyboardButton('✅❗️' + x + '❗️', callback_data=f'p&{x}'))
                    else:
                        ans.add(types.InlineKeyboardButton('✅' + x, callback_data=f'p&{x}'))
        bot.send_message(msg.chat.id, message, reply_markup=ans)
    else:
        bot.send_message(msg.chat.id, 'Вы не авторизованы')


@bot.callback_query_handler(func=lambda msg: 'c' in msg.data.split('&'))
def show_products_in_category(msg):
    """
    отображение продуктов в категории если продуктов больше 10-ти
    :param msg:
    """
    list_dict = form_list_dict(msg.message)
    keyboard = types.InlineKeyboardMarkup(row_width=((len(list_dict[msg.data.split('&')[1]]) - 1) // 10) + 1)
    for i in list_dict[msg.data.split('&')[1]]:
        if i[1].isupper():
            keyboard.add(types.InlineKeyboardButton('✅❗️' + i + '❗️', callback_data=f'p&{i}'))
        else:
            keyboard.add(types.InlineKeyboardButton('✅' + i, callback_data=f'p&{i}'))
    bot.edit_message_reply_markup(message_id=msg.message.message_id, chat_id=msg.message.chat.id,
                                  reply_markup=keyboard)


@bot.callback_query_handler(func=lambda msg: 'p' in msg.data.split('&'))
def remove_product(msg):
    family = db.read_table('Users_database', column_name='id', value=msg.message.chat.id)[0][2]
    if db.remove_record(family, column_name='Product', value=msg.data.split('&')[1]):
        bot.send_message(msg.message.chat.id, f'{msg.data.split("&")[1]} успешно вычеркнут(а) из списка')
    else:
        bot.send_message(msg.message.chat.id, f'{msg.data.split("&")[1]} удалить не удалось :(')
    cat_prod_dict = form_list_dict(msg.message)
    message = 'Список покупок:\n'
    for category in cat_prod_dict:
        message += '\n' + category + ':\n'
        for product in cat_prod_dict[category]:
            message += f'{cat_prod_dict[category].index(product) + 1}) {product}\n'
    ans = types.InlineKeyboardMarkup(row_width=2)
    lena = 0
    for i in cat_prod_dict:
        for x in cat_prod_dict[i]:
            lena += 1
    if lena >= 10:
        for i in cat_prod_dict:
            ans.add(types.InlineKeyboardButton(i, callback_data=f'c&{i}'))
    else:
        for i in cat_prod_dict:
            for x in cat_prod_dict[i]:
                if x[1].isupper():
                    ans.add(types.InlineKeyboardButton('✅❗️' + x + '❗️', callback_data=f'p&{x}'))
                else:
                    ans.add(types.InlineKeyboardButton('✅' + x, callback_data=f'p&{x}'))
    bot.edit_message_text(message_id=msg.message.message_id, chat_id=msg.message.chat.id, text=message,
                          reply_markup=ans)
    print(msg.data)
    if msg.data.split('&')[1].isupper():
        notify('del', msg.data.split('&')[1], family, msg.message.chat.username)


@bot.message_handler(commands=['quit_family'])
def quit(msg):
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    keyboard.add(types.KeyboardButton(':key: Выйти из семьи'))
    keyboard.add(types.KeyboardButton(':x: Отмена'))
    bot.send_message(msg.chat.id, 'Вы уверены что хотите выйти из семьи?', reply_markup=keyboard)
    bot.register_next_step_handler(msg, quit2)


def quit2(msg):
    if msg.text == ':key: Выйти из семьи':
        if db.remove_record('Users_database', 'id', msg.chat.id):
            bot.send_message(msg.chat.id, 'Вы вышли из семьи')
        else:
            bot.send_message(354640082, f'@{msg.chat.username} не смог выйти из семьи\n chat_id - {msg.chat.id}')
            bot.send_message(msg.chat.id,
                             'Во время выхода произошла ошибка, заявка направлена модератору, мы уведомим вас когда процесс будет завершен')


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
#         bot.send_message(msg.chat.id, 'Вы не авторизованы')


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
    if len(db.read_table('Users_database', column_name='id', value=msg.chat.id)) != 0:
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
        family = db.read_table('Users_database', column_name='id', value=msg.message.chat.id)[0][2]
        if db.remove_record(family, '*', '*'):
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


@bot.message_handler(content_types=['text'])
def add_product(msg):
    """
    добавление продукта в список
    :param msg:
    """
    if len(db.read_table('Users_database', column_name='id', value=msg.chat.id)) != 0:
        family = db.read_table('Users_database', column_name='id', value=msg.chat.id)[0][2]
        category = "Другое"
        msg.text = msg.text.replace('&', ' and ')
        if len(msg.text) > 62:
            msg.text = msg.text[0:63]
        found = False
        for word in msg.text.split():
            if found:
                break
            else:
                ans = db.read_table('category_product', 'product', word.lower())
                if len(ans) > 0:
                    found = True
                    category = ans[0][1]
                    break
        if not found:
            category = 'Другое'
        if 'срочно' in msg.text.lower():
            txt = ''
            for i in msg.text.split():
                if i.lower() == 'срочно':
                    continue
                else:
                    txt += i.upper() + ' '
            add_ans = db.add_record(family, (category, txt))
            if add_ans == 'Success':
                bot.send_message(msg.chat.id, txt + ' успешно добавлен(а) в список, как срочный продукт')
                notify('add', txt, family, msg.chat.username)
            else:
                bot.send_message(msg.chat.id, add_ans)
        else:
            add_ans = db.add_record(family, (category, msg.text))
            if add_ans == 'Success':
                bot.send_message(msg.chat.id, msg.text + ' успешно добавлен(а) в список')
            else:
                bot.send_message(msg.chat.id, add_ans)
    else:
        bot.send_message(msg.chat.id, 'Вы не авторизованы')


@bot.message_handler(commands=['notify'])
def notif(msg):
    if msg.chat.username == 'artem_pas':
        bot.send_message(msg.chat.id, 'Enter notification text:')
        global waiting_notification
        waiting_notification = True
    else:
        bot.send_message(msg.chat.id, 'This command is unavailable for you')


bot.enable_save_next_step_handlers(2)
bot.load_next_step_handlers()

while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        traceback.print_exc()
        bot.send_message(354640082, 'ОШИБКА!!!\n' * 3 + str(e))
        time.sleep(1)
