from typing import Sequence

from django.db.models import QuerySet
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_inline_keyboard_page(
    items: Sequence[InlineKeyboardButton],
    page: int,
    columns: int,
    pagination_callback: str,
    rows=9,
) -> InlineKeyboardMarkup:
    """

    @param items: Buttons of all objects
    @param page:
    @param columns:
    @param pagination_callback: callback to next page, should contain {page} for page number
    @param rows:
    @param back_to: callback for page number button
    @return:
    """
    if rows > 9:
        raise ValueError("Telegram API doesn't support more than 10 rows (one needed for pagination buttons)")
    starts_from = (page - 1) * columns * rows
    while starts_from >= len(items):
        page -= 1
        starts_from = (page - 1) * columns * rows
    ends_on = starts_from + columns * rows
    keyboard = []
    for i in range(starts_from, min(len(items), ends_on), columns):
        keyboard.append(items[i : i + columns])
    btns = []
    if page > 1:
        btns.append(
            InlineKeyboardButton(
                "<=",
                callback_data=pagination_callback.format(page=str(page - 1)),
            )
        )
    if len(items) > columns * rows:
        btns.append(
            InlineKeyboardButton(
                f"{page}/{(len(items) / (columns * rows)).__ceil__()}",
                callback_data=f"{page}/{(len(items) / (columns * rows)).__ceil__()}",
            )
        )
    # else:
    #     btns.append(types.InlineKeyboardButton("Назад", callback_data=f"{back_to}"))
    if ends_on < len(items):
        btns.append(
            InlineKeyboardButton(
                "=>",
                callback_data=pagination_callback.format(page=str(page + 1)),
            )
        )
    keyboard.append(btns)
    return InlineKeyboardMarkup(keyboard)


def get_cart_text(products: QuerySet) -> str:
    if not products:
        return "Список пуст"
    else:
        current_category = products[0].category
        text = f"Список покупок:\n\n\t{current_category.name}\n"
        for product in products:
            if product.category != current_category:
                text += f"\t{current_category.name}\n"
                current_category = product.category
            text += product.to_string() + "\n"
    return text
