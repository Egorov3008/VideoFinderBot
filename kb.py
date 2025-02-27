from aiogram.types import ReplyKeyboardMarkup, KeyboardButtonRequestUser, KeyboardButton, KeyboardButtonRequestChat, \
    InlineKeyboardMarkup, InlineKeyboardButton

from config import ADMIN_ID


def cancel_btn():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Или нажмите на 'ОТМЕНА' для отмены"
    )


async def main_contact_kb(user_id: int):

    buttons = []
    if user_id in ADMIN_ID:
        buttons =[[
            KeyboardButton(
                text="⚙️ АДМИНКА",
            )
        ]]

    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=False
    )

    return keyboard


def admin_kb():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
            [InlineKeyboardButton(text="📧 Рассылка", callback_data="admin_broadcast")]
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
