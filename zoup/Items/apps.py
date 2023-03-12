from time import sleep

from django.apps import AppConfig
from telebot import TeleBot
from os import environ
from dotenv import load_dotenv


class ItemsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "Items"

    def ready(self):
        load_dotenv()
        bot = TeleBot(environ.get("TELETOKEN"))
        bot.remove_webhook()
        sleep(1)
        bot.set_webhook(url=environ.get("DOMAIN")+"/api/bot_updates", secret_token=environ.get("WEBHOOK_SECRET_KEY"))
