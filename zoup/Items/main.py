"""
Телеграм бот для составления списка покупок
"""
from django.db.models import QuerySet
from telebot import *
from telebot.types import Message, CallbackQuery
from telebot.apihelper import ApiException
from os import environ
from telebot.util import quick_markup
from Items.models import *
from dotenv import load_dotenv
from Items.tools import get_inline_keyboard_page, get_cart_text

formatter = "[%(asctime)s] %(levelname)8s --- %(message)s (%(filename)s:%(lineno)s)"
logger = logging.getLogger("Bot")
load_dotenv()
bot = TeleBot(environ.get("TELETOKEN"))


def log(func):
    def wrapper(*args, **kwargs):
        func_args = inspect.signature(func).bind(*args, **kwargs).arguments
        func_args_str = ", ".join(map("{0[0]} = {0[1]!r}".format, func_args.items()))
        logger.info(f"{func.__module__}.{func.__qualname__} ( {func_args_str} )")
        return func(*args, **kwargs)

    return wrapper


def login_required(func):
    def wrapper(*args, **kwargs):
        if type(args[0]) is Message:
            try:
                if Profile.objects.get(chat_id=args[0].from_user.id).family:
                    return func(*args, **kwargs)
                else:
                    bot.send_message(args[0].chat.id, f"Необходимо войти в семью!", reply_markup=quick_markup(
                        {"Создать семью": {"url": environ.get("DOMAIN") + ""}}))  # TODO Create family URL
            except Profile.DoesNotExist:
                bot.send_message(args[0].chat.id, f"Необходимо авторизоваться!", reply_markup=quick_markup(
                    {"Создать семью": {"url": environ.get("DOMAIN") + "login"}}))

    return wrapper


@log
def notify(text: str, users: list[int]):
    for user in users:
        try:
            bot.send_message(user, text)
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
""")


@log
@login_required
@bot.message_handler(commands=["list"])
def show_list(msg: Message):
    family = Profile.objects.get(chat_id=msg.from_user.id).family
    products: QuerySet[Product] = family.get_products.all().order_by("category", "name")
    text = get_cart_text(products)
    if products:
        buttons = [i.to_button(1) for i in products]
        bot.send_message(msg.chat.id, text, reply_markup=get_inline_keyboard_page(buttons, "", 1, 2, "list&{page}"))
    else:
        bot.send_message(msg.chat.id, text)


@log
@login_required
@bot.callback_query_handler(func=lambda msg: "p" in msg.data.split("&"))
def remove_product(callback: CallbackQuery):
    family = Profile.objects.get(chat_id=callback.from_user.id).family
    _, product_id, page = callback.data.split("&")
    queryset = family.get_products.all()
    try:
        deleted = queryset.get(id=product_id).delete()
    except Product.DoesNotExist:
        bot.answer_callback_query(callback.id, f"{product_id} не существует")
    else:
        morph = MorphAnalyzer()
        first_noun = None
        for word in deleted.name.split():
            if morph.parse(word)[0].tag.POS == "NOUN":
                first_noun = word
                break
        if first_noun is None:
            bot.send_message(callback.message.chat.id, f"{deleted.name} удален(a) из списка")
        parsed = morph.parse(first_noun)[0]
        inflect_to = {"plur"} if parsed.tag.number == "plur" else {parsed.tag.gender}
        bot.answer_callback_query(
            callback.id,
            f"{deleted.name} {morph.parse('вычеркнуто')[0].inflect(inflect_to).word} из списка")
    products: QuerySet[Product] = family.get_products.all().order_by("category", "name")
    text = get_cart_text(products)
    if products:
        buttons = [i.to_button(page) for i in products]
        bot.edit_message_text(
            message_id=callback.message.message_id,
            chat_id=callback.message.chat.id, text=text,
            reply_markup=get_inline_keyboard_page(buttons, "", 1, 2, "list&{page}")
        )
    else:
        bot.edit_message_text(
            message_id=callback.message.message_id,
            chat_id=callback.message.chat.id, text=text)


@log
@login_required
@bot.message_handler(commands=["clear_list"])
def clear_list(msg):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("✅ Да, удалить!", callback_data="clear&yes"))
    keyboard.add(types.InlineKeyboardButton("❌ Нет, не удалять", callback_data=str(msg.chat.id) + "clear&no"))
    bot.send_message(
        msg.chat.id,
        "Вы уверены, что хотите полностью очистить список?\n❗️ЭТО ДЕЙСТВИЕ БУДЕТ НЕВОЗМОЖНО ОТМЕНИТЬ❗️",
        reply_markup=keyboard,
    )


@log
@login_required
@bot.callback_query_handler(func=lambda msg: msg.data.split("&")[1] == "clear")
def clear_confirmed(callback: CallbackQuery):
    clear = callback.data.split("&")[1] == "yes"
    if clear:
        Profile.objects.get(chat_id=callback.from_user.id).family.get_products.all().delete()
        bot.answer_callback_query(callback.id, "Cleared")
        bot.edit_message_text("Список успешно очищен", chat_id=callback.message.chat.id,
                              message_id=callback.message.message_id)
    else:
        bot.edit_message_text("Очистка отменена", chat_id=callback.message.chat.id,
                              message_id=callback.message.message_id)


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

@log
@login_required
@bot.edited_message_handler(func=lambda x: True)
def edit_product(msg: Message):
    queryset = Profile.objects.get(chat_id=msg.from_user.id).family.get_products
    try:
        product = queryset.get(msg.message_id)
    except Product.DoesNotExist:
        return
    product.name = msg.text
    product.category = Product.determine_category(msg.text)
    product.save()
    bot.reply_to(msg, "Изменено")


@log
@login_required
@bot.message_handler(content_types=["text"])
def add_product(msg: Message):
    user = User.objects.get(profile__chat_id=msg.from_user.id)
    product = Product.from_message(name=msg.text, created_by=user, message_id=msg.message_id)
    product.save()
    morph = MorphAnalyzer()
    first_noun = None
    for word in msg.text.split():
        if morph.parse(word)[0].tag.POS == "NOUN":
            first_noun = word
            break
    if first_noun is None:
        bot.send_message(msg.chat.id, f"{product.name} успешно добавлен(a) в список")
    parsed = morph.parse(first_noun)[0]
    inflect_to = {"plur"} if parsed.tag.number == "plur" else {parsed.tag.gender}
    bot.send_message(
        msg.chat.id,
        f"{product.name} успешно {morph.parse('добавлен')[0].inflect(inflect_to).word} в список")


