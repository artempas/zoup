"""
Телеграм бот для составления списка покупок
"""

from telebot import *
import database_module as db  # TODO исправить перед заливом
import mytoken

currently_forbidden_familynames = ['families', 'category_product', 'users_database', 'transfering_logins']
bot = TeleBot(mytoken.token, threaded=False)
authenticated = False
waiting_notification = False
db.create_table('Users_database', {'User_id': 'INTEGER', 'Username': 'TEXT', 'Family': 'TEXT'})
db.create_table('Families', {'Family': 'TEXT', 'Password': 'TEXT'})


def form_keyboard(cat_prod_dict, category=False, page=1):
    message = ''
    for cat in cat_prod_dict:
        message += '\n' + cat + ':\n'
        for product in cat_prod_dict[cat]:
            message += f'{cat_prod_dict[cat].index(product) + 1}) {product}\n'
    ans = types.InlineKeyboardMarkup(row_width=2)
    if type(category) == bool:
        lena = 0
        for i in cat_prod_dict:
            for x in cat_prod_dict[i]:
                lena += 1
        if lena > 10:
            for i in cat_prod_dict:
                ans.add(types.InlineKeyboardButton(i, callback_data=f'c&{i}'))
        else:
            for i in cat_prod_dict:
                for x in cat_prod_dict[i]:
                    if x.isupper():
                        ans.add(types.InlineKeyboardButton('✅❗️' + x + '❗️', callback_data=f'p&{x}'))
                    else:
                        ans.add(types.InlineKeyboardButton('✅' + x, callback_data=f'p&{x}'))
    else:
        paged = False
        if len(cat_prod_dict[category]) > 10:
            paged = True
        lena = -1
        last_index = (page - 1) * 8
        for i in cat_prod_dict[category][last_index::]:
            if i.isupper():
                ans.add(types.InlineKeyboardButton('✅❗️' + i + '❗️', callback_data=f'p&{i}'))
            else:
                ans.add(types.InlineKeyboardButton('✅' + i, callback_data=f'p&{i}'))
            lena += 1
            print(len(cat_prod_dict[category]))
            print(last_index)
            print(lena)
            if lena == 7 and paged or len(cat_prod_dict[category]) - last_index == lena + 1:
                last_index += lena
                if page != 1:
                    ans.add(types.InlineKeyboardButton('<=', callback_data=f'c&{category}&{page - 1}&ba'))
                if ((len(cat_prod_dict[category]) + 1) // 8) + 1 != page:
                    ans.add(types.InlineKeyboardButton('=>', callback_data=f'c&{category}&{page + 1}&fo'))
                break
    return message, ans


def form_list_dict(msg):
    """
    Формирует словарь {категория:продукт} относящийся к семье отправителя
    :param msg:
    :return:
    """
    family = db.read_table('Users_database', column_name='id', value=msg.chat.id)[0][2]
    cat_prod = db.read_table(family)
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


def notify(do, product, family, username, sender):
    """
    уведомление всех участников семьи о покупке или добавлении в список
    срочного продукта
    :param do:
    :param product:
    """
    print(f'{sender}(@{username}) - notify')
    users_list = db.read_table('Users_database', column_name='family', value=family)
    for user in users_list:
        if user[0] == sender:
            continue
        else:
            try:
                if do == 'del' or do == 'add':
                    bot.send_message(user[0],
                                     "@" + username + ' срочно просит купить ' * int(do == "add") + ' купил(a) ' * int(
                                         do == "del") + product.capitalize())
                elif do == 'welcome':
                    bot.send_message(user[0], f'@{product} присоединился(ась) к семье')
                elif do == 'change':
                    bot.send_message(user[0], f'@{username} сменил пароль семьи\nНовый пароль - {product}')
            except Exception as e:
                print(str(e))


@bot.message_handler(commands=['help'])
def helper(msg):
    """
    Вывод сообщения помощи
    :param msg:
    """
    print(f'{msg.chat.id}(@{msg.chat.username}) - help')
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


@bot.message_handler(commands=['register'])
def register(msg):
    if len(db.read_table('Users_database', column_name='id', value=msg.chat.id)) == 0:
        print(f'{msg.chat.id}(@{msg.chat.username}) - register(begin)')
        bot.send_message(msg.chat.id, 'Придумайте логин для семьи:')
        bot.register_next_step_handler(msg, create_family)
    else:
        bot.send_message(msg.chat.id, 'Вы и так находитесь в семье, используйте /quit_family для выхода')


def create_family(msg):
    print(f'{msg.chat.id}(@{msg.chat.username}) - register(entered login)')
    global currently_forbidden_familynames
    entered_family = msg.text.lower()
    entered_family.replace('&', 'and')
    not_in_db = True
    families = db.read_table('Families')
    for family in families:
        if family[0] == entered_family:
            not_in_db = False
    not_in_transfering_logins = True
    available = True
    for i in entered_family:
        if ord(i) >= 41 and ord(i) <= 90 or ord(i) >= 97 and ord(i) <= 122:
            continue
        else:
            available = False
    for family_name in db.read_table('Transfering_logins'):
        if family_name[1] == entered_family:
            not_in_transfering_logins = False
    if entered_family not in currently_forbidden_familynames and not_in_db and not_in_transfering_logins and available:
        bot.send_message(msg.chat.id, 'Логин удовлетворяет условиям\nВведите пароль:')
        bot.register_next_step_handler(msg, final_register)
        db.add_record('transfering_logins', (msg.chat.id, entered_family))
    else:
        bot.send_message(msg.chat.id,
                         'Такой логин уже существует или использован недопустимый символ (допустимы только буквы английского алфавита) попробуйте другой')
        bot.register_next_step_handler(msg, create_family)


def final_register(msg):
    login = db.read_table('transfering_logins', 'chat_id', msg.chat.id)[0][1]
    password = msg.text
    bot.send_message(msg.chat.id, db.add_record('Families', (login, password)))
    db.create_table(login, {'Category': 'TEXT', 'Product': 'TEXT'})
    if msg.chat.username is not None:
        bot.send_message(msg.chat.id,
                         db.add_record('Users_database', (msg.chat.id, msg.chat.username, login)))
    else:
        bot.send_message(msg.chat.id,
                         db.add_record('Users_database', (msg.chat.id, msg.chat.first_name, login)))
        bot.send_message(msg.chat.id, 'У вашего аккаунта отсутствует никнейм, для корректного отображения рекомендуем '
                                      'вам создать его, а после перезайти в семью с помощью /quit /join\n'
                                      'Создать никнейм можно через вкладку "Настройки"')
    if db.remove_record('Transfering_logins', 'chat_id', msg.chat.id):
        print(f'{msg.chat.id}(@{msg.chat.username}) - registered')
        bot.send_message(msg.chat.id, f'Семья успешно создана\nЛогин - {login}\nПароль - {password}')
    else:
        bot.send_message(msg.chat.id, 'Что-то пошло не так, попробуйте ещё раз\n/register')


@bot.message_handler(commands=['join'])
def log_in__ask_login(msg):
    if len(db.read_table('Users_database', column_name='id', value=msg.chat.id)) == 0:
        print(f'{msg.chat.id}(@{msg.chat.username}) - log_in(start)')
        bot.send_message(msg.chat.id, 'Логин:')
        bot.register_next_step_handler(msg, log_in__enter_login)
    else:
        bot.send_message(msg.chat.id, 'Вы и так находитесь в семье, используйте /quit_family для выхода')


def log_in__enter_login(msg):
    print(f'{msg.chat.id}(@{msg.chat.username}) - log_in(continue)')
    if len(db.read_table('Families', column_name='Family', value=msg.text.lower())) > 0:
        db.add_record('Transfering_logins', (msg.chat.id, msg.text.lower()))
        bot.send_message(msg.chat.id, 'Введите пароль:')
        bot.register_next_step_handler(msg, log_in__enter_password)
    elif msg.text[0] == '/':
        bot.send_message(msg.chat.id, 'Вход отменен')
        return
    else:
        bot.send_message(msg.chat.id,
                         'Семья не найдена, попробуйте еще раз\nЧтобы отменить вход вызовите любую команду\nЛогин:')
        bot.register_next_step_handler(msg, log_in__enter_login)


def log_in__enter_password(msg):
    try:
        login = db.read_table('Transfering_logins', column_name='chat_id', value=msg.chat.id)[0][1]
    except IndexError or ValueError:
        bot.send_message(msg.chat.id, 'Попробуйте пройти процесс входа заново\n/join')
        return None
    if db.read_table('Families', 'Family', login)[0][1] == msg.text:
        if msg.chat.username is not None:
            bot.send_message(msg.chat.id,
                             db.add_record('Users_database', (msg.chat.id, msg.chat.username, login)))
            notify('welcome', msg.chat.username, login, None, msg.chat.id)
        else:
            bot.send_message(msg.chat.id,
                             db.add_record('Users_database', (msg.chat.id, msg.chat.first_name, login)))
            bot.send_message(msg.chat.id,
                             'У вашего аккаунта отсутствует никнейм, для корректного отображения рекомендуем '
                             'вам создать его, а после перезайти в семью с помощью /quit_family /join\n'
                             'Создать никнейм можно через вкладку "Настройки"')
            notify('welcome', msg.chat.first_name, login, None, msg.chat.id)
        bot.send_message(msg.chat.id, f'Вы вошли в семью {login}')
        db.remove_record('Transfering_logins', column_name='chat_id', value=msg.chat.id)
        print(f'{msg.chat.id}(@{msg.chat.username}) - log_in(complete)')

    else:
        keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        keyboard.add(types.KeyboardButton('Попробовать ввести логин ещё раз'))
        keyboard.add(types.KeyboardButton('Попробовать ввести пароль ещё раз'))
        keyboard.add(types.KeyboardButton('Отмена'))
        bot.send_message(msg.chat.id, 'Неверный пароль\nПопробовать ещё раз?', reply_markup=keyboard)
        bot.register_next_step_handler(msg, wrong_password)


def wrong_password(msg):
    print(f'{msg.chat.id}(@{msg.chat.username}) - wrong_password')
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
    print(f'{message.chat.id}(@{message.chat.username}) - start')
    helper(message)


@bot.message_handler(commands=['show_password'])
def show_password(msg):
    print(f'{msg.chat.id}(@{msg.chat.username}) - show_password')
    if len(db.read_table('Users_database', column_name='id', value=msg.chat.id)) != 0:
        family = db.read_table('Users_database', column_name='id', value=msg.chat.id)[0][2]
        password = db.read_table('families', column_name='Family', value=family)[0][1]
        bot.send_message(msg.chat.id, f'Логин семьи - {family}\nПароль - {password}')


@bot.message_handler(commands=['change_password'])
def change_password(msg):
    print(f'{msg.chat.id}(@{msg.chat.username}) - change_password')
    bot.send_message(msg.chat.id, 'Введите новый пароль:')
    bot.register_next_step_handler(msg, change_password2)


def change_password2(msg):
    print(f'{msg.chat.id}(@{msg.chat.username}) - change_password2')
    family = db.read_table('Users_database', 'id', msg.chat.id)[0][2]
    if db.update_record('Families', column_name='Family', search_value=family, change_column='password',
                        new_value=msg.text):
        if msg.chat.username is not None:
            notify('change', msg.text, family, msg.chat.username, msg.chat.id)
        else:
            notify('change', msg.text, family, msg.chat.first_name, msg.chat.id)
    else:
        bot.send_message(msg.chat.id,
                         'При смене пароля произошла ошибка, попробуйте позже\nВы всегда можете воспользоваться /show_password')


@bot.message_handler(commands=['list'])
def show_list(msg):
    """
    отображение списка продуктов
    :param msg:
    """
    print(f'{msg.chat.id}(@{msg.chat.username}) - show_list')
    if len(db.read_table('Users_database', column_name='id', value=msg.chat.id)) != 0:
        cat_prod_dict = form_list_dict(msg)
        message = 'Список покупок:\n'
        [mes, ans] = form_keyboard(cat_prod_dict, False)
        message += mes
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
    if len(msg.data.split('&')) > 2:
        ans = form_keyboard(list_dict, msg.data.split('&')[1], int(msg.data.split('&')[2]))[1]
        bot.answer_callback_query(msg.id, '=>' * int(msg.data.split('&')[3] == 'fo') + '<=' * int(
            msg.data.split('&')[3] == 'ba'))
    else:
        ans = form_keyboard(list_dict, msg.data.split('&')[1])[1]
        bot.answer_callback_query(msg.id, msg.data.split('&')[1])
    bot.edit_message_reply_markup(message_id=msg.message.message_id, chat_id=msg.message.chat.id, reply_markup=ans)


@bot.callback_query_handler(func=lambda msg: 'p' in msg.data.split('&'))
def remove_product(msg):
    print(f'{msg.message.chat.id}(@{msg.message.chat.username}) - remove_product')
    family = db.read_table('Users_database', column_name='id', value=msg.message.chat.id)[0][2]
    if db.remove_record(family, column_name='Product', value=msg.data.split('&')[1]):
        bot.answer_callback_query(msg.id, f'{msg.data.split("&")[1]} успешно вычеркнут(а) из списка')
    else:
        bot.answer_callback_query(msg.id, f'{msg.data.split("&")[1]} удалить не удалось :(')
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
                if x.isupper():
                    ans.add(types.InlineKeyboardButton('✅❗️' + x + '❗️', callback_data=f'p&{x}'))
                else:
                    ans.add(types.InlineKeyboardButton('✅' + x, callback_data=f'p&{x}'))
    bot.edit_message_text(message_id=msg.message.message_id, chat_id=msg.message.chat.id, text=message,
                          reply_markup=ans)
    if msg.data.split('&')[1].isupper():
        if msg.message.chat.username is not None:
            notify('del', msg.data.split('&')[1], family, msg.message.chat.username, msg.message.chat.id)
        else:
            notify('del', msg.data.split('&')[1], family, msg.message.chat.first_name, msg.message.chat.id)


@bot.message_handler(commands=['quit_family'])
def quit(msg):
    print(f'{msg.chat.id}(@{msg.chat.username}) - quit')
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    keyboard.add(types.KeyboardButton('Выйти из семьи'))
    keyboard.add(types.KeyboardButton('Отмена'))
    bot.send_message(msg.chat.id, 'Вы уверены что хотите выйти из семьи?', reply_markup=keyboard)
    bot.register_next_step_handler(msg, quit2)


def quit2(msg):
    if msg.text == 'Выйти из семьи':
        print(f'{msg.chat.id}(@{msg.chat.username}) - quit2(yes)')
        if db.remove_record('Users_database', 'id', msg.chat.id):
            bot.answer_callback_query(msg.id, 'Success')
            bot.send_message(msg.chat.id, 'Вы вышли из семьи', reply_markup=types.ReplyKeyboardRemove())
        else:
            bot.send_message(354640082, f'@{msg.chat.username} не смог выйти из семьи\n chat_id - {msg.chat.id}')
            bot.send_message(msg.chat.id,
                             'Во время выхода произошла ошибка, заявка направлена модератору, мы уведомим вас когда процесс будет завершен',
                             reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(commands=['add_keyword'])
def choose_category(msg):
    """
    начало добавления ключевого слова
    запрос категории
    :param msg:
    """
    print(f'{msg.chat.id}(@{msg.chat.username}) - add_keyword(start)')
    keyboard = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
    categories = []
    for i in db.read_table('Category_product'):
        if i[1] not in categories:
            categories.append(i[1])
    for i in categories:
        keyboard.add(types.KeyboardButton(i))
    keyboard.add(types.KeyboardButton('Отмена'))
    bot.send_message(msg.chat.id, 'Выберите категорию в которую вы хотите добавить ключевое слово',
                     reply_markup=keyboard)
    bot.register_next_step_handler(msg, ask_keyword)


def ask_keyword(msg):
    """
    запрос ключевого слова
    :param msg:
    """
    if len(db.read_table('Category_product', 'category', msg.text)) != 0:
        print(f'{msg.chat.id}(@{msg.chat.username}) - add_keyword(chosen_category)')
        db.add_record('Transfering_logins', (msg.chat.id, f'&{msg.text}&'))
        bot.send_message(msg.chat.id, 'Введите ключевое слово или отмена:', reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, add_keyword)
    else:
        bot.send_message(msg.chat.id, 'Отменено', reply_markup=types.ReplyKeyboardRemove())


def add_keyword(msg):
    """
    добавление полученного ключевого слова
    :param msg:
    """
    category = db.read_table('transfering_logins', 'chat_id', msg.chat.id)[0][1].replace('&', '')
    print(f'{msg.chat.id}(@{msg.chat.username}) - add_keyword(added ({msg.text} -> {category}))')
    if msg.text.lower() == 'отмена':
        bot.send_message(msg.chat.id, 'Отменено')
        return None
    if not db.remove_record('transfering_logins', 'chat_id', msg.chat.id):
        return None
    if msg.text not in db.read_table('category_product', 'product', msg.text):
        bot.send_message(msg.chat.id,
                         db.add_record('category_product', (msg.text, category)))
        bot.send_message(msg.chat.id, f'{msg.text} добавлен(а) в список ключевых слов')
        bot.send_message(354640082,
                         f'@{msg.chat.username} добавил(а) ключевое слово\nCategory - {category}\nProduct - {msg.text}')
    else:
        bot.send_message(msg.chat.id, 'Ключевое слово уже в базе данных')


@bot.message_handler(commands=['clear_list'])
def clear_list(msg):
    print(f'{msg.chat.id}(@{msg.chat.username}) - clear_list')
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
        print(f'{msg.message.chat.id}(@{msg.message.chat.username}) - clear_confirmed')
        family = db.read_table('Users_database', column_name='id', value=msg.message.chat.id)[0][2]
        if db.remove_record(family, '*', '*'):
            bot.answer_callback_query(msg.id, 'Cleared')
            bot.edit_message_text('Список успешно очищен',
                                  chat_id=msg.message.chat.id,
                                  message_id=msg.message.message_id)
        else:
            bot.edit_message_text('Во время очистки произошла ошибка, обратитесь к @artem_pas',
                                  chat_id=msg.message.chat.id,
                                  message_id=msg.message.message_id)
    else:
        bot.edit_message_text('Очистка отменена', chat_id=msg.message.chat.id, message_id=msg.message.message_id)


@bot.message_handler(commands=['notify'])
def notif(msg):
    if msg.chat.username == 'artem_pas':
        bot.send_message(msg.chat.id, 'Enter notification text:')
        bot.register_next_step_handler(msg, notification)
    else:
        bot.send_message(msg.chat.id, 'This command is unavailable for you')


def notification(msg):
    users = db.read_table('Users_database')
    errors = []
    for user in users:
        try:
            bot.send_message(user[0], msg.text)
        except Exception as e:
            errors.append(str(user[1]) + ' - ' + str(e))
    if len(errors) > 0:
        bot.send_message(354640082, 'Errors:' + str(errors))


@bot.message_handler(commands=['admin'])
def admin_startup(msg):
    if msg.chat.username == 'artem_pas':
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton('Update', callback_data='a&u'))
        keyboard.add(types.InlineKeyboardButton('Restart', callback_data='a&r'))
        keyboard.add(types.InlineKeyboardButton('SQL', callback_data='a&sql'))
        keyboard.add(types.InlineKeyboardButton('Block user', callback_data='a&b'))
        bot.send_message(msg.chat.id, 'Select tool', reply_markup=keyboard)
        bot.disable_save_next_step_handlers()
    else:
        bot.send_message(msg.chat.id, 'Access denied')


@bot.callback_query_handler(func=lambda cb: 'a' == cb.data.split('&')[0])
def admin_tool_selection(cb):
    tool = cb.data.split('&')[1]
    if tool == 'u':
        bot.send_message(cb.message.chat.id, 'waiting for update file (0 to cancel)')
        bot.register_next_step_handler_by_chat_id(cb.message.chat.id, update)
    elif tool == 'r':
        if bot.answer_callback_query(cb.id, 'Restarting...'):
            bot.send_message(cb.message.chat.id, 'restarting')
            exit()
    elif tool == 'sql':
        bot.send_message(cb.message.chat.id, 'now in sql mode (выхожу to cancel)')
        bot.register_next_step_handler_by_chat_id(cb.message.chat.id, sql)
    elif tool == "b":
        bot.send_message(cb.message.chat.id, 'chat_id to block')
        bot.register_next_step_handler_by_chat_id(cb.message.chat.id, block)


def update(msg):
    file = bot.get_file(msg.document.file_id)
    loaded = bot.download_file(file.file_path)
    open('main1.py', 'wb').write(loaded)
    bot.send_message(msg.chat.id, 'File is downloaded, restarting')
    exit()


def sql(msg):
    pass


def block(msg):
    pass


@bot.message_handler(content_types=['text'])
def add_product(msg):
    """
    добавление продукта в список
    :param msg:
    """
    print(f'{msg.chat.id}(@{msg.chat.username}) - add_product')
    if len(db.read_table('Users_database', column_name='id', value=msg.chat.id)) != 0:
        family = db.read_table('Users_database', column_name='id', value=msg.chat.id)[0][2]
        category = "Другое"
        msg.text = msg.text.replace('&', ' and ')
        msg.text = msg.text.replace('%', 'проц.')
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
                if msg.chat.username is not None:
                    notify('add', txt, family, msg.chat.username, msg.chat.id)
                else:
                    notify('add', txt, family, msg.chat.first_name, msg.chat.id)
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





bot.enable_save_next_step_handlers(2)
bot.load_next_step_handlers()

while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(str(e))
        bot.send_message(354640082, 'ОШИБКА!!!\n' * 3 + str(e))
        time.sleep(1)
