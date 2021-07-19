"""
Телеграм бот для составления списка покупок
"""
from random import randint

from requests import get
from telebot import *
import database_module as db  # TODO исправить перед заливом
import mytoken
from Product import Product, morph

admin_id = 354640082
currently_forbidden_family_names = ['families', 'category_product', 'users_database', 'transfering_logins']
bot = TeleBot(mytoken.token, threaded=False)
authenticated = False
waiting_notification = False
db.create_table('Users_database', {'id': 'INTEGER', 'Username': 'TEXT', 'Family': 'TEXT'})
db.create_table('Families', {'Family': 'TEXT', 'Password': 'TEXT'})
db.create_table('Transferring_logins', {'chat_id':'INTEGER', 'login':'TEXT'})
db.create_table('Products_database', {'Id':'unique','Category': 'TEXT', 'Product': 'TEXT', 'Urgent':'INT', 'Family':'TEXT'})




def form_keyboard(cat_prod_dict, category=None, page=1):
    print("form_keyboard:input: cat_prod_dict = ",cat_prod_dict,'\tcategory = ',category,'\tpage=',page)
    ans = types.InlineKeyboardMarkup(row_width=2)
    if category is not None and category in cat_prod_dict:
        paged = False
        if len(cat_prod_dict[category]) > 10:
            paged = True
        lena = -1
        last_index = (page - 1) * 8
        for i in cat_prod_dict[category][last_index::]:
            btn = i.get_button()
            ans.add(types.InlineKeyboardButton(btn[0], callback_data=btn[1]))
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
    else:
        lena = 0
        for category in cat_prod_dict:
                lena += len(cat_prod_dict[category])
        if lena > 10:
            for i in cat_prod_dict:
                ans.add(types.InlineKeyboardButton(i, callback_data=f'c&{i}'))
        else:
            for category in cat_prod_dict:
                for product in cat_prod_dict[category]:
                    btn=product.get_button()
                    ans.add(types.InlineKeyboardButton(btn[0],callback_data=btn[1]))
    return ans





def notify(do, product, family, msg):
    """
    уведомление всех участников семьи о покупке или добавлении в список
    срочного продукта
    :param do:
    :param product:
    """
    sender=msg.chat.id
    if msg.chat.username is not None:
        username=msg.chat.username
    else:
        username=msg.chat.first_name
    print(f'{sender}(@{username}) - notify')
    users_list = db.read_table('Users_database', column_name='family', value=family)
    for user in users_list:
        if user[0] == sender:
            continue
        else:
            try:
                if do == 'del' or do == 'add':
                    try:
                        bot.send_message(user[0],
                                         "@" + username + ' срочно просит купить ' * int(do == "add") + morph.parse(' купил ')[0].inflect({morph.parse(username)[0].tag.gender}).word * int(
                                             do == "del") + product.get_name().capitalize())
                    except ValueError:
                        bot.send_message(user[0],
                                         "@" + username + ' срочно просит купить ' * int(do == "add") +
                                         ' купил(а) ' * int(
                                             do == "del") + product.get_name().capitalize())
                elif do == 'welcome':
                    bot.send_message(user[0], f'@{username} присоединяется к семье')
                elif do == 'change':
                    try:
                        bot.send_message(user[0], f'@{username} '+ morph.parse('сменил')[0].inflect({morph.parse(username)[0].tag.gender}).word+f'пароль семьи\nНовый пароль - {product}')
                    except ValueError:
                        bot.send_message(user[0], f'@{username} сменил(а) пароль семьи\nНовый пароль - {product}')
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
                     '/list - показывает список покупок и позволяет вычёркивать купленные продукты, в случае, если продуктов больше 10 - показывает категории, нажав на которые, вы увидите продукты в данной категории\n\n'
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
    global currently_forbidden_family_names
    entered_family = msg.text.lower()
    entered_family.replace('&', 'and')
    not_in_db = True
    families = db.read_table('Families')
    for family in families:
        if family[0] == entered_family:
            not_in_db = False
    not_in_transferring_logins = True
    available = True
    for i in entered_family:
        if ord(i) in range(48, 58) or ord(i) in range(65, 91) or ord(i) in range(97, 122):
            continue
        else:
            available = False
    for family_name in db.read_table('Transfering_logins'):
        if family_name[1] == entered_family:
            not_in_transferring_logins = False
    if entered_family not in currently_forbidden_family_names and not_in_db and not_in_transferring_logins and available:
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
    for i in password:
        if ord(i) in range(48, 58) or ord(i) in range(65, 91) or ord(i) in range(97, 122):
            continue
        else:
            bot.send_message(msg.chat.id, 'В пароле разрешено использовать только буквы латинского алфавита и цифры')
    bot.send_message(msg.chat.id, db.add_record('Families', (login, password)))
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
            notify('welcome', None, login, msg)
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
        notify('change', msg.text, family, msg)
    else:
        bot.send_message(msg.chat.id,
                         'При смене пароля произошла ошибка, попробуйте позже\nВы всегда можете воспользоваться '
                         '/show_password')


@bot.message_handler(commands=['list'])
def show_list(msg):
    """
    отображение списка продуктов
    :param msg:
    """
    print(f'{msg.chat.id}(@{msg.chat.username}) - show_list')
    family=db.read_table('Users_database', column_name='id', value=msg.chat.id)
    if len(family) != 0:
        family=family[0][2]
        dct=Product(0,'').form_family_dict(family_name=family)
        text=Product(0,'').form_message_text(dct)
        if len(dct)!=0:
            kbd = form_keyboard(dct)
            bot.send_message(msg.chat.id, text, reply_markup=kbd)
        else:
            bot.send_message(msg.chat.id, text)
    else:
        bot.send_message(msg.chat.id, 'Вы не авторизованы')


@bot.callback_query_handler(func=lambda msg: 'c' in msg.data.split('&'))
def show_products_in_category(msg):
    """
    отображение продуктов в категории если продуктов больше 10-ти
    :param msg:
    """
    if len(db.read_table('Users_Database', 'id',msg.message.chat.id))!=0:
        list_dict = Product(0,'').form_family_dict(family_name=db.read_table('Users_Database', 'id',msg.message.chat.id)[0][2])
        if len(msg.data.split('&')) > 2:
            ans = form_keyboard(list_dict, msg.data.split('&')[1], int(msg.data.split('&')[2]))
            bot.answer_callback_query(msg.id, '=>' * int(msg.data.split('&')[3] == 'fo') + '<=' * int(
                msg.data.split('&')[3] == 'ba'))
        else:
            ans = form_keyboard(list_dict, msg.data.split('&')[1])
            bot.answer_callback_query(msg.id, msg.data.split('&')[1])
        bot.edit_message_reply_markup(message_id=msg.message.message_id, chat_id=msg.message.chat.id, reply_markup=ans)
    else:
        bot.answer_callback_query(msg.id, 'Вы не авторизованы')


@bot.callback_query_handler(func=lambda msg: 'p' in msg.data.split('&'))
def remove_product(msg):
    family = db.read_table('Users_database', column_name='id', value=msg.message.chat.id)
    if len(family) != 0:
        family=family[0][2]
        print(f'{msg.message.chat.id}(@{msg.message.chat.username}) - remove_product')
        print(msg.data)
        try:
            print("remove product::deleted",db.read_table('Products_database','id',int(msg.data.split('&')[1])),'\n')
            deleted=db.read_table('Products_database','Id',int(msg.data.split('&')[1]))[0]
            if deleted[4]!=family:
                bot.answer_callback_query(msg.id,'Отказано в доступе')
                raise PermissionError
            deleted=Product(int(deleted[0]),deleted[2],deleted[1],bool(int(deleted[3])))
        except IndexError:
            deleted=None
        if db.remove_record('Products_database', column_name='Id', value=int(msg.data.split('&')[1])) and deleted is not None:
            try:
                bot.answer_callback_query(msg.id, deleted.get_name() + ' успешно ' + morph.parse('вычеркнуто')[0].inflect(
                    {morph.parse(deleted.get_name().split(' ')[0])[0].tag.gender}).word + ' из списка')
            except ValueError:
                bot.answer_callback_query(msg.id, deleted.get_name() + ' успешно вычеркнут(а) в список')
            dct = Product(0, '').form_family_dict(family)
            text = Product(0, '').form_message_text(dct)
            kbd = form_keyboard(dct)
            bot.edit_message_text(message_id=msg.message.message_id, chat_id=msg.message.chat.id, text=text,
                                  reply_markup=kbd)
            if deleted.is_urgent():
                    notify('del', deleted, family,msg.message)

        else:
            bot.answer_callback_query(msg.id, f'{msg.data.split("&")[1]} удалить не удалось :(')
            dct = Product(0, '').form_family_dict(family)
            text = Product(0, '').form_message_text(dct)
            kbd = form_keyboard(dct)
            bot.edit_message_text(message_id=msg.message.message_id, chat_id=msg.message.chat.id, text=text,
                                  reply_markup=kbd)

    else:
        bot.send_message(msg.message.chat.id, 'Вы не авторизованы')

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
            bot.send_message(msg.chat.id, 'Вы вышли из семьи', reply_markup=types.ReplyKeyboardRemove())
        else:
            bot.send_message(354640082, f'@{msg.chat.username} не смог выйти из семьи\n chat_id - {msg.chat.id}')
            bot.send_message(msg.chat.id,
                             'Во время выхода произошла ошибка, заявка направлена модератору, мы уведомим вас когда процесс будет завершен',
                             reply_markup=types.ReplyKeyboardRemove())
    else:
        bot.send_message(msg.chat.id, "Отменено", reply_markup=types.ReplyKeyboardRemove())


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
        bot.send_message(msg.chat.id, 'Ошибка')
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
    if msg.text.lower() == 'выхожу':
        bot.send_message(msg.chat.id, 'sql mode ended')
    else:
        bot.send_message(msg.chat.id, db.run_anything(msg.text))
        bot.register_next_step_handler_by_chat_id(msg.chat.id, sql)


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
        id=randint(10000, 99999)
        while len(db.read_table('Products_database','Id',id))!=0:
            id = randint(00000, 99999)
        added = Product(id,msg.text)
        print(added)
        add_ans = db.add_record('Products_database', (id,added.get_category(),added.get_name(), int(added.is_urgent()),family))
        if add_ans == 'Success':
            try:
                if morph.parse(added.get_name().split(' ')[0])[0].tag.number=='sing':
                    gender=morph.parse(added.get_name().split(' ')[0])[0].tag.gender
                else:
                    gender = 'plur'
                bot.send_message(msg.chat.id, added.get_name() + ' успешно ' + morph.parse('добавлен')[0].inflect({gender, 'pssv'}).word)
            except ValueError:
                bot.send_message(msg.chat.id, msg.text + ' успешно добавлен(а) в список')
        else:
            bot.send_message(msg.chat.id, add_ans)
        if added.is_urgent():
            notify('add',added,family,msg)
    else:
        bot.send_message(msg.chat.id, 'Вы не авторизованы')


bot.enable_save_next_step_handlers(15)
bot.load_next_step_handlers()

while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(traceback.format_exc())
        bot.send_message(admin_id, 'ОШИБКА!!!\n' * 3 + str(e))
        time.sleep(1)
