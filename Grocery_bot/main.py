"""
Телеграм бот для составления списка покупок
"""
from telebot import *
import mytoken
from database_module import Database
from Product import Product, morph
import datetime
import fastapi
import uvicorn



WEBHOOK_HOST = '46.151.24.37'
WEBHOOK_PORT = 8443  # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_LISTEN = '0.0.0.0'  # In some VPS you may need to put here the IP addr

WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Path to the ssl certificate
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # Path to the ssl private key

# Quick'n'dirty SSL certificate generation:
#
# openssl genrsa -out webhook_pkey.pem 2048
# openssl req -new -x509 -days 3650 -key webhook_pkey.pem -out webhook_cert.pem
#
# When asked for "Common Name (e.g. server FQDN or YOUR name)" you should reply
# with the same value in you put in WEBHOOK_HOST

WEBHOOK_URL_BASE = "https://{}:{}".format(WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/{}/".format(mytoken.teletoken)

formatter = '[%(asctime)s] %(levelname)8s --- %(message)s (%(filename)s:%(lineno)s)'
logging.basicConfig(
    filename=f'bot-from-{datetime.datetime.now().date()}.log',
    filemode='w',
    format=formatter,
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.WARNING
)
edit = False
admin_id = 354640082
bot = TeleBot(mytoken.teletoken, threaded=False)
db = Database(mytoken.airtable_token, mytoken.base_id)
authenticated = False
waiting_notification = False
app = fastapi.FastAPI(docs=None, redoc_url=None)

@app.post(f'/{mytoken.teletoken}/')
def process_webhook(update: dict):
    """
    Process webhook calls
    """
    if update:
        update = telebot.types.Update.de_json(update)
        bot.process_new_updates([update])
    else:
        return
def form_keyboard(cat_prod_dict, category=None, page=1):
    logging.info(f"form_keyboard:input: {cat_prod_dict=}\t{category =}\t{page=}")
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
                    btn = product.get_button()
                    ans.add(types.InlineKeyboardButton(btn[0], callback_data=btn[1]))
    return ans


def notify(do, product, family, msg):
    """
    уведомление всех участников семьи о покупке или добавлении в список
    срочного продукта
    :param do:
    :param product:
    """
    sender = msg.chat.id
    if msg.chat.username is not None:
        username = msg.chat.username
    else:
        username = msg.chat.first_name
    logging.info(f'{sender}(@{username}) - notify')

    for user in list(db.users_database.iterate(formula="({family}=\"" + family + '\")'))[0]:
        if user['fields']['id'] == sender:
            continue
        else:
            try:
                if do == 'del' or do == 'add':
                    try:
                        bot.send_message(user['fields']['id'],
                                         "@" + username + ' срочно просит купить ' * int(do == "add") +
                                         morph.parse(' купил ')[0].inflect(
                                             {morph.parse(username)[0].tag.gender}).word * int(
                                             do == "del") + product.capitalize())
                    except Exception:
                        bot.send_message(user['fields']['id'],
                                         "@" + username + ' срочно просит купить ' * int(do == "add") +
                                         ' купил(а) ' * int(
                                             do == "del") + product.capitalize())
                elif do == 'welcome':
                    bot.send_message(user['fields']['id'], f'@{username} присоединяется к семье')
                elif do == 'change':
                    try:
                        bot.send_message(user['fields']['id'], f'@{username} ' + morph.parse('сменил')[0].inflect(
                            {morph.parse(username)[0].tag.gender}).word + f'пароль семьи\nНовый пароль - {product}')
                    except Exception:
                        bot.send_message(user['fields']['id'],
                                         f'@{username} сменил(а) пароль семьи\nНовый пароль - {product}')
            except Exception as e:
                logging.error(e)

@bot.message_handler(commands=['help'])
def helper(msg):
    """
    Вывод сообщения помощи
    :param msg:
    """
    logging.info(f'{msg.chat.id}(@{msg.chat.username}) - help')
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
    if db.users_database.first(formula='{id}=' + str(msg.chat.id)) is None:
        logging.info(f'{msg.chat.id}(@{msg.chat.username}) - register(begin)')
        bot.send_message(msg.chat.id, 'Придумайте логин для семьи:')
        bot.register_next_step_handler(msg, create_family)
    else:
        bot.send_message(msg.chat.id, 'Вы и так находитесь в семье, используйте /quit_family для выхода')


def create_family(msg):
    logging.info(f'{msg.chat.id}(@{msg.chat.username}) - register(entered login)')
    entered_family = msg.text.lower()
    in_db = db.families.first(formula="({family}=\""+msg.text+'")') is not None
    in_transferring_logins = db.transferring_logins.first(formula="({login}=\""+msg.text+'")') is not None
    if not in_db and not in_transferring_logins:
        bot.send_message(msg.chat.id, 'Логин удовлетворяет условиям\nВведите пароль:')
        bot.register_next_step_handler(msg, final_register)
        db.transferring_logins.create({'chat_id': msg.chat.id, 'login': entered_family})
    else:
        bot.send_message(msg.chat.id,
                         'Такой логин уже существует или использован недопустимый символ (допустимы только буквы английского алфавита) попробуйте другой')
        bot.register_next_step_handler(msg, create_family)


def final_register(msg):
    try:
        login = db.transferring_logins.first(formula='{chat_id}=' + str(msg.chat.id))
        password = msg.text
        for i in password:
            if ord(i) in range(48, 58) or ord(i) in range(65, 91) or ord(i) in range(97, 122):
                continue
            else:
                bot.send_message(msg.chat.id,
                                 'В пароле разрешено использовать только буквы латинского алфавита и цифры')
        db.families.create({"family": login['fields']['login'], "password": password})
        if msg.chat.username is not None:
            db.users_database.create(
                {"id": msg.chat.id, "username": msg.chat.username, "family": login['fields']['login']})
        else:
            db.users_database.create(
                {"id": msg.chat.id, "username": msg.chat.first_name, "family": login['fields']['login']})
            bot.send_message(msg.chat.id,
                             'У вашего аккаунта отсутствует никнейм, для корректного отображения рекомендуем '
                             'вам создать его, а после перезайти в семью с помощью /quit /join\n'
                             'Создать никнейм можно через вкладку "Настройки"')
        db.transferring_logins.delete(login['id'])
        logging.info(f'{msg.chat.id}(@{msg.chat.username}) - registered')
        bot.send_message(msg.chat.id,
                         f'Семья успешно создана\nЛогин - {login["fields"]["login"]}\nПароль - {password}')
    except Exception as e:
        bot.send_message(msg.chat.id, 'Что-то пошло не так, попробуйте ещё раз\n/register')
        bot.send_message(admin_id, str(e))
        print(traceback.format_exc())


@bot.message_handler(commands=['join'])
def log_in__ask_login(msg):
    if db.users_database.first(formula='{id}=' + str(msg.chat.id)) is None:
        logging.info(f'{msg.chat.id}(@{msg.chat.username}) - log_in(start)')
        bot.send_message(msg.chat.id, 'Логин:')
        bot.register_next_step_handler(msg, log_in__enter_login)
    else:
        bot.send_message(msg.chat.id, 'Вы и так находитесь в семье, используйте /quit_family для выхода')


def log_in__enter_login(msg):
    logging.info(f'{msg.chat.id}(@{msg.chat.username}) - log_in(continue)')
    if db.families.first(formula="({family}=\"" + msg.text + "\")") is not None:
        db.transferring_logins.create({"chat_id": msg.chat.id, "login": msg.text.lower()})
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
        login = db.transferring_logins.first(formula='({chat_id}=' + str(msg.chat.id)+')')
    except IndexError or ValueError:
        bot.send_message(msg.chat.id, 'Попробуйте пройти процесс входа заново\n/join')
        return None
    if db.families.first(formula="({family}=\"" + login['fields']['login'] + "\")")['fields']['password'] == msg.text:
        if msg.chat.username is not None:
            db.users_database.create(
                {'id': msg.chat.id, 'username': msg.chat.username, 'family': login['fields']['login']})
            notify('welcome', msg.chat.username, login['fields']['login'], msg)
        else:
            db.users_database.create(
                {'id': msg.chat.id, 'username': msg.chat.first_name, 'family': login['fields']['login']})
            bot.send_message(msg.chat.id,
                             'У вашего аккаунта отсутствует никнейм, для корректного отображения рекомендуем '
                             'вам создать его, а после перезайти в семью с помощью /quit_family /join\n'
                             'Создать никнейм можно через вкладку "Настройки"')
            notify('welcome', msg.chat.first_name, login, msg)
        bot.send_message(msg.chat.id, f'Вы вошли в семью {login["fields"]["login"]}')
        db.transferring_logins.delete(login['id'])
        logging.info(f'{msg.chat.id}(@{msg.chat.username}) - log_in(complete)')

    else:
        keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        keyboard.add(types.KeyboardButton('Попробовать ввести логин ещё раз'))
        keyboard.add(types.KeyboardButton('Попробовать ввести пароль ещё раз'))
        keyboard.add(types.KeyboardButton('Отмена'))
        bot.send_message(msg.chat.id, 'Неверный пароль\nПопробовать ещё раз?', reply_markup=keyboard)
        bot.register_next_step_handler(msg, wrong_password)


def wrong_password(msg):
    logging.info(f'{msg.chat.id}(@{msg.chat.username}) - wrong_password')
    if msg.text == 'Попробовать ввести логин ещё раз':
        db.transferring_logins.delete(
            db.transferring_logins.first(formula="({chat_id}=" + str(msg.chat.id) + ")")['id'])
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
    logging.info(f'{message.chat.id}(@{message.chat.username}) - start')
    helper(message)


@bot.message_handler(commands=['show_password'])
def show_password(msg):
    logging.info(f'{msg.chat.id}(@{msg.chat.username}) - show_password')
    family = db.users_database.first(formula="({id}=" + str(msg.chat.id) + ")")
    if family is not None:
        password = db.families.first(formula="({family}=\"" + family['fields']['family']+'")')
        bot.send_message(msg.chat.id,
                         f'Логин семьи - {family["fields"]["family"]}\nПароль - {password["fields"]["password"]}')
    else:
        bot.send_message(msg.chat.id, "Вы не авторизованы")


@bot.message_handler(commands=['change_password'])
def change_password(msg):
    logging.info(f'{msg.chat.id}(@{msg.chat.username}) - change_password')
    bot.send_message(msg.chat.id, 'Введите новый пароль:')
    bot.register_next_step_handler(msg, change_password2)


def change_password2(msg):
    logging.info(f'{msg.chat.id}(@{msg.chat.username}) - change_password2')
    try:
        family = db.users_database.first(formula="({id}=" + str(msg.chat.id) + ")")
        db.families.update(db.families.first(formula="({family}=\"" + family['fields']['family'] + "\")")['id'])
        notify('change', msg.text, family, msg)
    except Exception:
        bot.send_message(msg.chat.id,
                         'При смене пароля произошла ошибка, попробуйте позже\nВы всегда можете воспользоваться '
                         '/show_password')


@bot.message_handler(commands=['list'])
def show_list(msg):
    """
    отображение списка продуктов
    :param msg:
    """
    logging.info(f'{msg.chat.id}(@{msg.chat.username}) - show_list')
    family = db.users_database.first(formula="({id}=" + str(msg.chat.id) + ")")
    if family is not None:
        family = family['fields']['family']
        dct = Product(0, '').form_family_dict(family_name=family)
        text = Product(0, '').form_message_text(dct)
        if len(dct) != 0:
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
    family = db.users_database.first(formula="({id}=" + str(msg.message.chat.id) + ")")
    if family is not None:
        list_dict = Product(0, '').form_family_dict(
            family_name=family['fields']['family'])
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
    family = db.users_database.first(formula="({id}=" + str(msg.message.chat.id) + ")")
    if family is not None:
        family = family["fields"]['family']
        logging.info(f'{msg.message.chat.id}(@{msg.message.chat.username}) - remove_product')
        deleted_rec = db.products_database.first(formula='({id}=' + msg.data.split('&')[1] + ')')
        if deleted_rec is not None:
            if deleted_rec['fields']['family'] != family:
                bot.answer_callback_query(msg.id, 'Отказано в доступе')
                raise PermissionError
            deleted = Product(deleted_rec['fields']['id'],
                                  deleted_rec['fields']['product'],
                                  deleted_rec['fields']['category'],
                                  True if deleted_rec['fields']['urgent'] == 'True' else False)
            db.products_database.delete(deleted_rec['id'])

            try:
                bot.answer_callback_query(msg.id,
                                          deleted.get_name() + ' успешно ' + morph.parse('вычеркнуто')[0].inflect(
                                              {morph.parse(deleted.get_name().split(' ')[0])[
                                                   0].tag.gender}).word + ' из списка')
            except Exception:
                bot.answer_callback_query(msg.id, deleted.get_name() + ' успешно вычеркнут(а) в список')
            dct = Product(0, '').form_family_dict(family)
            text = Product(0, '').form_message_text(dct)
            kbd = form_keyboard(dct)
            bot.edit_message_text(message_id=msg.message.message_id, chat_id=msg.message.chat.id, text=text,
                                  reply_markup=kbd)
            if deleted.is_urgent():
                notify('del', deleted.get_name(), family, msg.message)

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
    logging.info(f'{msg.chat.id}(@{msg.chat.username}) - quit')
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    keyboard.add(types.KeyboardButton('Выйти из семьи'))
    keyboard.add(types.KeyboardButton('Отмена'))
    bot.send_message(msg.chat.id, 'Вы уверены что хотите выйти из семьи?', reply_markup=keyboard)
    bot.register_next_step_handler(msg, quit2)


def quit2(msg):
    if msg.text == 'Выйти из семьи':
        logging.info(f'{msg.chat.id}(@{msg.chat.username}) - quit2(yes)')
        db.users_database.delete(db.users_database.first(formula='({id}=' + str(msg.chat.id) + ')')['id'])
        bot.send_message(msg.chat.id, 'Вы вышли из семьи', reply_markup=types.ReplyKeyboardRemove())
        # else:
        #     bot.send_message(354640082, f'@{msg.chat.username} не смог выйти из семьи\n chat_id - {msg.chat.id}')
        #     bot.send_message(msg.chat.id,
        #                      'Во время выхода произошла ошибка, заявка направлена модератору, мы уведомим вас когда процесс будет завершен',
        #                      reply_markup=types.ReplyKeyboardRemove())
    else:
        bot.send_message(msg.chat.id, "Отменено", reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(commands=['add_keyword'])
def choose_category(msg):
    """
    начало добавления ключевого слова
    запрос категории
    :param msg:
    """
    logging.info(f'{msg.chat.id}(@{msg.chat.username}) - add_keyword(start)')
    keyboard = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
    categories = set(i['fields']['category'] for i in db.category_product.all())
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
    if db.category_product.first(formula="({category}=\"" + msg.text + "\")") is not None:
        logging.info(f'{msg.chat.id}(@{msg.chat.username}) - add_keyword(chosen_category)')
        db.transferring_logins.create({'chat_id': msg.chat.id, 'login': f'&{msg.text}&'})
        bot.send_message(msg.chat.id, 'Введите ключевое слово или отмена:', reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, add_keyword)
    else:
        bot.send_message(msg.chat.id, 'Отменено', reply_markup=types.ReplyKeyboardRemove())


def add_keyword(msg):
    """
    добавление полученного ключевого слова
    :param msg:
    """
    category_rec = db.transferring_logins.first(formula="({chat_id}=" + str(msg.chat.id) + ")")
    category_rec["fields"]["login"]=category_rec["fields"]["login"].replace('&','')
    logging.info(
        f'{msg.chat.id}(@{msg.chat.username}) - add_keyword(added ({msg.text} -> {category_rec["fields"]["login"]}))')
    if msg.text.lower() == 'отмена':
        bot.send_message(msg.chat.id, 'Отменено')
        return None
    db.transferring_logins.delete(category_rec['id'])
    if db.category_product.first(formula='({product}="' + msg.text + '")') is None:
        db.category_product.create({"category": category_rec['fields']['login'], 'product': msg.text})
        bot.send_message(msg.chat.id, f'{msg.text} добавлен(а) в список ключевых слов')
        bot.send_message(354640082,
                         f'@{msg.chat.username} добавил(а) ключевое слово\nCategory - {category_rec["fields"]["login"]}\nProduct - {msg.text}')
    else:
        bot.send_message(msg.chat.id, 'Ключевое слово уже в базе данных')


@bot.message_handler(commands=['clear_list'])
def clear_list(msg):
    logging.info(f'{msg.chat.id}(@{msg.chat.username}) - clear_list')
    family = db.users_database.first(formula="({id}=" + str(msg.chat.id) + ")")
    if family is not None:
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
        logging.info(f'{msg.message.chat.id}(@{msg.message.chat.username}) - clear_confirmed')
        family = db.users_database.first(formula="({id}=" + str(msg.message.chat.id) + ")")
        db.products_database.batch_delete(list(
            i['id'] for i in db.products_database.all(formula="({family}=\"" + family['fields']['family'] + "\")")))
        bot.answer_callback_query(msg.id, 'Cleared')
        bot.edit_message_text('Список успешно очищен',
                              chat_id=msg.message.chat.id,
                              message_id=msg.message.message_id)
    else:
        bot.edit_message_text('Очистка отменена', chat_id=msg.message.chat.id, message_id=msg.message.message_id)


# @bot.message_handler(commands=['notify'])
# def notif(msg):
#     if msg.chat.username == 'artem_pas':
#         bot.send_message(msg.chat.id, 'Enter notification text:')
#         bot.register_next_step_handler(msg, notification)
#     else:
#         bot.send_message(msg.chat.id, 'This command is unavailable for you')
#
#
# def notification(msg):
#     users = db.read_table('Users_database')
#     errors = []
#     for user in users:
#         try:
#             bot.send_message(user[0], msg.text)
#         except Exception as e:
#             errors.append(str(user[1]) + ' - ' + str(e))
#     if len(errors) > 0:
#         bot.send_message(354640082, 'Errors:' + str(errors))


# @bot.message_handler(commands=['admin'])
# def admin_startup(msg):
#     if msg.chat.username == 'artem_pas':
#         keyboard = types.InlineKeyboardMarkup()
#         keyboard.add(types.InlineKeyboardButton('Update', callback_data='a&u'))
#         keyboard.add(types.InlineKeyboardButton('Restart', callback_data='a&r'))
#         keyboard.add(types.InlineKeyboardButton('SQL', callback_data='a&sql'))
#         keyboard.add(types.InlineKeyboardButton('Get "Other"', callback_data='a&get_other'))
#         bot.send_message(msg.chat.id, 'Select tool', reply_markup=keyboard)
#         bot.disable_save_next_step_handlers()
#     else:
#         bot.send_message(msg.chat.id, 'Access denied')
#
#
# @bot.callback_query_handler(func=lambda cb: 'a' == cb.data.split('&')[0])
# def admin_tool_selection(cb):
#     tool = cb.data.split('&')[1]
#     if tool == 'u':
#         bot.send_message(cb.message.chat.id, 'waiting for update file (0 to cancel)')
#         bot.register_next_step_handler_by_chat_id(cb.message.chat.id, update)
#     elif tool == 'r':
#         if bot.answer_callback_query(cb.id, 'Restarting...'):
#             bot.send_message(cb.message.chat.id, 'restarting')
#             exit()
#     elif tool == 'sql':
#         bot.send_message(cb.message.chat.id, 'now in sql mode (выхожу to cancel)')
#         bot.register_next_step_handler_by_chat_id(cb.message.chat.id, sql)
#     elif tool == "get_other":
#         txt = '\n'.join([str(i[0]) for i in db.read_table('Other')])
#         bot.send_message(cb.message.chat.id, txt)
#
#
# def update(msg):
#     file = bot.get_file(msg.document.file_id)
#     loaded = bot.download_file(file.file_path)
#     open('main1.py', 'wb').write(loaded)
#     bot.send_message(msg.chat.id, 'File is downloaded, restarting')
#     exit()
#
#
# def sql(msg):
#     if msg.text.lower() == 'выхожу':
#         bot.send_message(msg.chat.id, 'sql mode ended')
#     else:
#         bot.send_message(msg.chat.id, db.run_anything(msg.text))
#         bot.register_next_step_handler_by_chat_id(msg.chat.id, sql)


@bot.edited_message_handler(func=
                            lambda msg: db.products_database.first(
                                formula="({id}=" + str(msg.message_id) + ')') is not None)
def edit_product(msg):
    global edit
    edit = True
    db.products_database.delete(db.products_database.first(formula="({id}=" + str(msg.message_id) + ')')['id'])
    add_product(msg)


@bot.message_handler(content_types=['text'])
def add_product(msg):
    """
    добавление продукта в список
    :param msg:
    """
    global edit
    logging.info(f'{msg.chat.id}(@{msg.chat.username}) - add_product')
    family = db.users_database.first(formula="({id}=" + str(msg.chat.id) + ")")
    if family is not None:
        family = family['fields']['family']
        id = msg.message_id
        added = Product(id, msg.text)
        db.products_database.create(
            {'id': id, 'category': added.get_category(), 'urgent': str(added.is_urgent()), 'family': family,'product':added.get_name()})
        if edit:
            bot.reply_to(msg, 'Изменено')
            edit=False
        else:
            try:
                bot.send_message(msg.chat.id, added.get_name() + ' успешно ' + morph.parse('добавлен')[0].inflect({
                    morph.parse(
                        added.get_name().split(
                            ' ')[
                            0])[
                        0].tag.gender * bool(
                        morph.parse(
                            added.get_name().split(
                                ' ')[
                                0])[
                            0].tag.number == 'sing'),
                    'pssv',
                    morph.parse(
                        added.get_name().split(
                            ' ')[
                            0])[
                        0].tag.number}).word + ' в список')
            except Exception:
                bot.send_message(msg.chat.id, added.get_name() + ' успешно добавлен(а) в список')


        if added.is_urgent():
            notify('add', added.get_name(), family, msg)
    else:
        bot.send_message(msg.chat.id, 'Вы не авторизованы')


bot.enable_save_next_step_handlers(15)
bot.load_next_step_handlers()

bot.remove_webhook()

# Set webhook
bot.set_webhook(
    url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
    certificate=open(WEBHOOK_SSL_CERT, 'r')
)


uvicorn.run(
    app,
    host=WEBHOOK_LISTEN,
    port=WEBHOOK_PORT,
    ssl_certfile=WEBHOOK_SSL_CERT,
    ssl_keyfile=WEBHOOK_SSL_PRIV
)