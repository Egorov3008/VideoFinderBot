import asyncio
from io import BytesIO
from typing import Optional, List, Dict

from aiogram import Router, F
from aiogram.enums import ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import html
from selenium.webdriver.common.devtools.v85.runtime import await_promise

from bot import bot
from db import get_all_users, get_subscription, add_sub_url, delete_subscription, get_user_counts, get_info_subscription
from filters.admin import IsAdminFilter
from kb import admin_kb, edit_sub
from logger import logger
from utils_bot.utils import msg_post, check_bot_status

router = Router()


class Form(StatesGroup):
    start_broadcast = State()
    sub_action = State()


class MediaGroupState(StatesGroup):
    waiting_for_media_group = State()
    send_media_group = State()


@router.callback_query(F.data == 'admin_panel', IsAdminFilter())
async def admin_handler(call: CallbackQuery, state: FSMContext):
    await state.clear()
    kb = admin_kb()
    await call.message.answer('Выберите действие👇', reply_markup=kb)


@router.callback_query(F.data == 'admin_users', IsAdminFilter())
async def admin_users_handler(call: CallbackQuery):
    await call.answer('Готовлю список пользователей')
    users_data = await get_all_users()
    dict_users_added = await get_user_counts()

    text = (f'<b>Всего зарегистрировано {len(users_data)} пользователей. </b>\n\n'
            f'За последнюю неделю: {dict_users_added["users_added_last_week"]}\n'
            f'За последний месяц: {dict_users_added["users_added_last_month"]}\n')

    users = [(user["telegram_id"], user["subscription_time"]) for user in users_data]

    if not users:
        await call.message.answer(
            "📭 Нет пользователей для экспорта.", reply_markup=admin_kb()
        )
        return

    # Создание CSV файла
    csv_data = "tg_id, Дата и время подписки\n"  # Заголовок CSV
    for user in users:
        csv_data += f"{user[0]}, {user[1]}\n"

    csv_file = BytesIO(csv_data.encode("utf-8-sig"))
    csv_file.seek(0)

    csv_buffered_file = BufferedInputFile(csv_file.getvalue(), filename="users_export.csv")

    # Создание TXT файла с только Telegram ID
    txt_data = "\n".join([str(user[0]) for user in users])  # Только Telegram ID
    txt_file = BytesIO(txt_data.encode("utf-8-sig"))
    txt_file.seek(0)

    txt_buffered_file = BufferedInputFile(txt_file.getvalue(), filename="users_export.txt")

    # Отправка обоих файлов
    await call.message.answer_document(
        csv_buffered_file,
        caption=text,
    )

    await call.message.answer_document(
        txt_buffered_file,
        caption="📜 Список Telegram ID пользователей.",
        reply_markup=admin_kb(),
    )

    # Закрытие файлов
    csv_file.close()
    txt_file.close()


@router.callback_query(F.data == 'admin_broadcast', IsAdminFilter())
async def admin_broadcast_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text='Назад', callback_data='admin_panel'))
    await call.message.answer(
        'Отправьте любое сообщение, а я его перехвачу и перешлю всем пользователям с базы данных\n\n'
        'Для отправки альбома:\n'
        '1. Отправьте одним сообщением все медиафайлы\n'
        '2. После их загрузки отправьте текстовое сообщение в необходимом формате.\n\n'
        'Для отправки одного подписанного медиа-файла можно отправлять как обычно 🙂',
        reply_markup=builder.as_markup()
    )
    await state.set_state(Form.start_broadcast)


@router.callback_query(F.data == "subscription", IsAdminFilter())
async def handle_subscription(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    dict_subscription: Optional[List[Dict]] = await get_subscription()
    builder = InlineKeyboardBuilder()
    text = ''
    if dict_subscription:
        text = '<b>Обязательные подписки: </b>'
        for data in dict_subscription:
            for k, v in data.items():
                builder.row(InlineKeyboardButton(text=f"{k}", callback_data=f"view_{v}"))
    else:
        text = "<b>Добавить подписку</b> 👇"
    builder.row(InlineKeyboardButton(text="Добавить подписку", callback_data="add_sub"))
    builder.row(InlineKeyboardButton(text="Назад", callback_data="admin_panel"))
    await callback.message.answer(text, reply_markup=builder.as_markup())


@router.message(Form.start_broadcast)
async def handle_media_group_start(message: Message, state: FSMContext):
    if message.media_group_id:
        logger.info("Приступаю к сбору медиагруппы")
        data = await state.get_data()
        media_group = data.get("media_group", [])
        logger.info(f"Длина media_group: {len(media_group)}")
        if media_group:
            logger.info("Добавляем сообщение в медиагруппу")
            media_group.append(message)
            await state.update_data(media_group=media_group)
            return
        await state.update_data(media_group=[message])
        await state.set_state(MediaGroupState.send_media_group)
    else:
        good_send = 0
        bad_send = 0
        users_data = await get_all_users()
        buttons = InlineKeyboardBuilder()
        buttons.row(InlineKeyboardButton(text="Админ_панель", callback_data="admin_panel"))
        await message.answer(f'Начинаю рассылку на {len(users_data)} пользователей.')
        for user in users_data:
            try:
                chat_id = user.get('telegram_id')
                await message.copy_to(chat_id=chat_id)
                good_send += 1
            except Exception as e:
                logger.error(f"Ошибка при пересылке сообщения: {e}")
                bad_send += 1

        await state.clear()
        await message.answer(f'Рассылка завершена. Сообщение получило <b>{good_send}</b>, '
                                     f'НЕ получило <b>{bad_send}</b> пользователей.', reply_markup=admin_kb())


@router.message(F.text, MediaGroupState.send_media_group)
async def handle_text_msg(message: Message, state: FSMContext):
    good_send = 0
    bad_send = 0
    users_data = await get_all_users()
    buttons = InlineKeyboardBuilder()
    buttons.row(InlineKeyboardButton(text="Админ_панель", callback_data="admin_panel"))
    await message.answer(f'Начинаю рассылку на {len(users_data)} пользователей.')

    for user in users_data:
        try:
            chat_id = user.get('telegram_id')
            await msg_post(message, state, chat_id=chat_id)
            good_send += 1
        except Exception as e:
            logger.error(f"Ошибка при пересылке сообщения: {e}")
            bad_send += 1


    await state.clear()
    await message.answer(f'Рассылка завершена. Сообщение получило <b>{good_send}</b>, '
                                 f'НЕ получило <b>{bad_send}</b> пользователей.', reply_markup=admin_kb())



@router.callback_query(F.data.startswith("view_"), IsAdminFilter())
async def handel_view_subscription(callback: CallbackQuery, state: FSMContext):
    logger.info(f"Работаю с подпиской {callback.data}")
    url_subscription = callback.data[5:]
    logger.info(f"Выбрана подписка: {url_subscription}")
    info_sub = await get_info_subscription(url_subscription)
    kb = edit_sub(url_subscription)
    await state.update_data(url_sub=url_subscription)
    link = html.link(info_sub["name_subscription"], info_sub["url_subscription"])
    activ_sub = "АКТИВНА" if not info_sub["active"] else "ВЫПОЛНЕНО"
    channel_username: str = url_subscription.split('/')[-1]
    is_bot_admin = await check_bot_status(channel_username)
    state_bot = "Админ" if is_bot_admin else "Бот не является админом"
    text = (f"<b>Подписка</b> {link}\n"
            f"<b>Статус подписки</b> {activ_sub}\n"
            f"<b>Статус бота в группе: {state_bot}</b>\n"
            f"<b>Пользователей подписалось</b> {info_sub['users_actual']}\n"
            f"<b>Установленный лимит подписчиков</b> {info_sub['users_set']}")
    await callback.message.answer(text, reply_markup=kb.as_markup())


@router.callback_query(F.data == "add_sub", IsAdminFilter())
async def handle_add_sub(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "<b>Пожалуйста, введите ссылку на канал и его название, разделив их символом '|'.</b>\n"
        "Пример: 👇\n\nhttps://t.me/username|название канала|количество пользователей\n\n"
        "Обратите внимание, что название канала должно быть коротким и легко воспринимаемым для вас.\n"
        "!!! для проверки подписки пользователей группа должна иметь @username\n"
        "Группы с такими ссылками: 'https://t.me/+b8i31D-0UHwzY2Ji' не определяются, даже если бот является админом\n"
        "Добавить username")
    await state.set_state(Form.sub_action)


@router.message(F.text, Form.sub_action)
async def handle_url_sub(message: Message, state: FSMContext):
    list_msg = message.text.split("|")
    if len(list_msg) != 3:
        await message.answer("Вы ввели некорректные данные, попробуйте еще раз")
        return
    sub_url = list_msg[0]
    name_sub = list_msg[1]
    users_set = list_msg[2]
    await add_sub_url(name=name_sub, url_sub=sub_url, users_set=int(users_set))
    buttons = InlineKeyboardBuilder()
    buttons.row(InlineKeyboardButton(text="Назад", callback_data="subscription"))
    link = html.link('канала', sub_url)
    await message.answer(f"Подписка принята, не забудьте добавить бота в админы {link}",
                         reply_markup=buttons.as_markup())


@router.callback_query(F.data.startswith("delete_"), IsAdminFilter())
async def handle_delete_sub(callback: CallbackQuery):
    url_subscription = callback.data[7:]
    logger.info(f"Удаляю подписку {url_subscription}")
    await delete_subscription(url_subscription)
    buttons = InlineKeyboardBuilder()
    buttons.row(InlineKeyboardButton(text="Назад", callback_data="subscription"))
    await callback.message.answer("Подписка удалена", reply_markup=buttons.as_markup())


@router.callback_query(F.data == "edit", IsAdminFilter())
async def handle_edit_sub(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("<b>Для обновления информации введите:</b>"
                                  f"\n\nhttps://t.me/username|название канала|количество пользователей\n\n")
    await state.set_state(Form.sub_action)
