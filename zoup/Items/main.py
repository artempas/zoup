"""
Телеграм бот для составления списка покупок
"""
from itertools import chain

from django.db.models import QuerySet, Q
from telebot import *
from telebot.types import Message, CallbackQuery
from telebot.apihelper import ApiException
from os import environ
from telebot.util import quick_markup
from Items import models
from pymorphy2 import MorphAnalyzer
from dotenv import load_dotenv
from Items.tools import get_inline_keyboard_page, get_cart_text

formatter = "[%(asctime)s] %(levelname)8s --- %(message)s (%(filename)s:%(lineno)s)"
logger = logging.getLogger("Bot")
load_dotenv()
bot = TeleBot(environ.get("TELETOKEN"))


def log(func):
    def wrapper(*args, **kwargs):
        print(f"{func.__module__}.{func.__qualname__} ( {[str(i) for i in args]} )")
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            print(exc)
            return None

    return wrapper


def login_required(func):
    def wrapper(*args, **kwargs):
        if type(args[0]) is Message:
            try:
                if models.Profile.objects.get(chat_id=args[0].from_user.id).family:
                    return func(*args, **kwargs)
                else:
                    bot.send_message(
                        args[0].chat.id,
                        f"Кажется вас нет ни в одной семье",
                        reply_markup=quick_markup({"Создать семью": {"url": environ.get("DOMAIN") + "/create_family"}}),
                    )  # TODO Create family URL
            except models.Profile.DoesNotExist:
                bot.send_message(
                    args[0].chat.id,
                    f"Необходимо авторизоваться",
                    reply_markup=quick_markup(
                        {
                            "Авторизация": {
                                "url": environ.get("DOMAIN")
                                + f"/link_telegram?token={models.Profile.create_login_token(args[0].from_user.id, ('@' + args[0].from_user.username if args[0].from_user.username else None) or args[0].from_user.first_name or args[0].from_user.last_name)}"
                            }
                        }
                    ),
                )
        elif type(args[0]) is CallbackQuery:
            try:
                if models.Profile.objects.get(chat_id=args[0].from_user.id).family:
                    return func(*args, **kwargs)
                else:
                    bot.send_message(
                        args[0].message.chat.id,
                        f"Кажется вас нет ни в одной семье",
                        reply_markup=quick_markup({"Создать семью": {"url": environ.get("DOMAIN") + "/create_family"}}),
                    )  # TODO Create family URL
            except models.Profile.DoesNotExist:
                bot.send_message(
                    args[0].message.chat.id,
                    f"Необходимо авторизоваться",
                    reply_markup=quick_markup(
                        {
                            "Авторизация": {
                                "url": environ.get("DOMAIN")
                                + f"/link_telegram?token={models.Profile.create_login_token(args[0].from_user.id, ('@' + args[0].from_user.username if args[0].from_user.username else None) or args[0].from_user.first_name or args[0].from_user.last_name)}"
                            }
                        }
                    ),
                )

    return wrapper


@log
def notify(text: str, users: list[int]):
    for user in users:
        try:
            bot.send_message(user, text, parse_mode="HTML")
        except ApiException as e:
            logging.error(e)


@bot.message_handler(commands=["start"])
def start_message(message: Message):
    """
    Запуск бота
    """
    logging.info(f"{message.chat.id}(@{message.chat.username}) - start")
    helper(message)


@bot.message_handler(commands=["help"])
def helper(msg):
    """
    Вывод сообщения помощи
    :param msg:
    """
    logging.info(f"{msg.chat.id}(@{msg.chat.username}) - help")
    bot.send_message(
        msg.chat.id,
        """
Бот, созданный для помощи в составлении списка покупок семьям.\n\n\n
/list - показывает список покупок и позволяет вычёркивать купленные продукты, в случае, если продуктов 
больше 10 - показывает категории, нажав на которые, вы увидите продукты в данной категории\n\n
/add_keyword - если вы заметили, что определённый продукт оказывается в категории "Другое", но его можно определить в одну из существующих категорий нажмите на эту команду и следуйте инструкциям\n\n\n
Чтобы добавить продукт просто напишите его в этот чат, помимо самого продукта можно писать необходимое количество, комментарии и всё что вашей душе угодно\n\n
/help - выведет это сообщение\n
/register - создать семью\n
/join - присоединиться к существующей семье\n\n\n
Created by: @artem_pas
""",
    )


@bot.message_handler(commands=["list"])
@login_required
@log
def show_list(msg: Message):
    family = models.Profile.objects.get(chat_id=msg.from_user.id).family
    other_products = family.get_products.filter(category__name="Другое").order_by("name")
    categoried_products = family.get_products.filter(~Q(category__name="Другое")).order_by("category", "name")
    products = list(chain(categoried_products, other_products))
    text = get_cart_text(products)
    if products:
        buttons = [i.to_button(1) for i in products]
        bot.send_message(
            msg.chat.id,
            text,
            reply_markup=get_inline_keyboard_page(buttons, 1, 2, "list&{page}"),
            parse_mode="HTML",
        )
    else:
        bot.send_message(msg.chat.id, text)


@bot.callback_query_handler(func=lambda callback: callback.data.split("&")[0] == "list")
@login_required
@log
def show_list(callback: CallbackQuery):
    family = models.Profile.objects.get(chat_id=callback.from_user.id).family
    other_products = family.get_products.filter(category__name="Другое").order_by("name")
    categoried_products = family.get_products.filter(~Q(category__name="Другое")).order_by("category", "name")
    products = list(chain(categoried_products, other_products))
    text = get_cart_text(products)
    if products:
        buttons = [i.to_button(1) for i in products]
        bot.edit_message_text(
            text,
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=get_inline_keyboard_page(buttons, int(callback.data.split("&")[1]), 2, "list&{page}"),
            parse_mode="HTML",
        )
    else:
        bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id)


@bot.callback_query_handler(func=lambda msg: "p" in msg.data.split("&"))
@login_required
@log
def remove_product(callback: CallbackQuery):
    family = models.Profile.objects.get(chat_id=callback.from_user.id).family
    _, product_id, page = callback.data.split("&")
    queryset = family.get_products.all()
    try:
        deleted = queryset.get(id=product_id)
        deleted.delete()
    except models.Product.DoesNotExist:
        bot.answer_callback_query(callback.id, f"{product_id} не существует")
    else:
        morph = MorphAnalyzer()
        first_noun = None
        for word in deleted.name.split():
            if morph.parse(word)[0].tag.POS == "NOUN":
                first_noun = word
                break
        if first_noun is None:
            bot.answer_callback_query(callback.id, f"{deleted.name} удален(a) из списка")
        parsed = morph.parse(first_noun)[0]
        inflect_to = {"plur"} if parsed.tag.number == "plur" else {parsed.tag.gender}
        if parsed.tag.gender is None:
            bot.answer_callback_query(callback.id, f"{deleted.name} удален(a) из списка")
        else:
            bot.answer_callback_query(
                callback.id, f"{deleted.name} {morph.parse('вычеркнуто')[0].inflect(inflect_to).word} из списка"
            )
    other_products = family.get_products.filter(category__name="Другое").order_by("name")
    categoried_products = family.get_products.filter(~Q(category__name="Другое")).order_by("category", "name")
    products = list(chain(categoried_products, other_products))
    text = get_cart_text(products)
    if products:
        buttons = [i.to_button(page) for i in products]
        bot.edit_message_text(
            message_id=callback.message.message_id,
            chat_id=callback.message.chat.id,
            text=text,
            reply_markup=get_inline_keyboard_page(buttons, 1, 2, "list&{page}"),
            parse_mode="HTML",
        )
    else:
        bot.edit_message_text(message_id=callback.message.message_id, chat_id=callback.message.chat.id, text=text)


@bot.message_handler(commands=["clear_list"])
@log
@login_required
def clear_list(msg):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("✅ Да, удалить!", callback_data="clear&yes"))
    keyboard.add(types.InlineKeyboardButton("❌ Нет, не удалять", callback_data=str(msg.chat.id) + "clear&no"))
    bot.send_message(
        msg.chat.id,
        "Вы уверены, что хотите полностью очистить список?\n❗️ЭТО ДЕЙСТВИЕ БУДЕТ НЕВОЗМОЖНО ОТМЕНИТЬ❗️",
        reply_markup=keyboard,
    )


@bot.callback_query_handler(func=lambda msg: msg.data.split("&")[0] == "clear")
@log
@login_required
def clear_confirmed(callback: CallbackQuery):
    clear = callback.data.split("&")[1] == "yes"
    if clear:
        models.Profile.objects.get(chat_id=callback.from_user.id).family.get_products.all().delete()
        bot.answer_callback_query(callback.id, "Cleared")
        bot.edit_message_text(
            "Список успешно очищен", chat_id=callback.message.chat.id, message_id=callback.message.message_id
        )
    else:
        bot.edit_message_text(
            "Очистка отменена", chat_id=callback.message.chat.id, message_id=callback.message.message_id
        )


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


@bot.edited_message_handler(func=lambda x: True)
@log
@login_required
def edit_product(msg: Message):
    queryset = models.Profile.objects.get(chat_id=msg.from_user.id).family.get_products
    try:
        product = queryset.get(msg.message_id)
    except models.Product.DoesNotExist:
        return
    product.name = msg.text
    product.category = models.Product.determine_category(msg.text)
    product.save()
    bot.reply_to(msg, "Изменено")


@bot.message_handler(content_types=["text"])
@login_required
@log
def add_product(msg: Message):
    user = models.User.objects.get(profile__chat_id=msg.from_user.id)
    product = models.Product.from_message(name=msg.text, created_by=user, message_id=msg.message_id)
    product.save()
    morph = MorphAnalyzer()
    first_noun = None
    for word in msg.text.split():
        if morph.parse(word)[0].tag.POS == "NOUN":
            first_noun = word
            break
    if first_noun is None:
        bot.send_message(msg.chat.id, f"{product.name} успешно добавлен(a) в список")
    else:
        parsed = morph.parse(first_noun)[0]
        inflect_to = {"plur"} if parsed.tag.number == "plur" else {parsed.tag.gender}
        if parsed.tag.gender is None:
            bot.send_message(msg.chat.id, f"{product.name} успешно добавлен(a) в список")
        else:
            bot.send_message(
                msg.chat.id, f"{product.name} успешно {morph.parse('добавлен')[0].inflect(inflect_to).word} в список"
            )


@bot.callback_query_handler(func=lambda x: True)
def echo(callback: CallbackQuery):
    bot.answer_callback_query(callback.id, callback.data)
