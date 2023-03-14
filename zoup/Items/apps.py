import logging
from threading import Thread
from time import sleep

from django.apps import AppConfig
from telebot import TeleBot
from os import environ
from dotenv import load_dotenv
from telebot.apihelper import ApiTelegramException


class ItemsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "Items"
    logger = logging.getLogger("Items.apps")

    def ready(self):
        load_dotenv()
        bot = TeleBot(environ.get("TELETOKEN"))
        if not environ.get("TEST_ENV"):
            bot.remove_webhook()
            sleep(1)
            bot.set_webhook(
                url=environ.get("DOMAIN") + "/api/bot_updates", secret_token=environ.get("WEBHOOK_SECRET_KEY")
            )
