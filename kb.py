from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_kb():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
            [InlineKeyboardButton(text="📧 Рассылка", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="🔗 Подписка", callback_data="subscription")]
        ]
    )
    return keyboard


def broadcast_kb():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_admin")],
            [
                InlineKeyboardButton(text="🚀 Начать рассылку", callback_data="start_broadcast")
            ]
        ]
    )
    return keyboard


def channels_kb(kb_list: list):
    inline_keyboard = []

    for channel_data in kb_list:
        label = channel_data.get('label')
        url = channel_data.get('url')

        # Проверка на наличие необходимых ключей
        if label and url:
            kb = [InlineKeyboardButton(text=label, url=url)]
            inline_keyboard.append(kb)

    # Добавление кнопки "Проверить подписку"
    inline_keyboard.append([InlineKeyboardButton(text="Проверить подписку", callback_data="check_subscription")])

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def sub_kb(data: dict):
    builder = InlineKeyboardBuilder()
    for k, v in data.items():
        builder.row(InlineKeyboardButton(text=f"{k}", callback_data=f"view_{v}"))
    builder.row(InlineKeyboardButton(text="Добавить подписку", callback_data="add_sub"))
    return builder


def edit_sub(url_sub):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Удалить канал", callback_data=f"delete_{url_sub}"))
    return builder
