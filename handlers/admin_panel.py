from io import BytesIO

from aiogram import Router, F
from aiogram.enums import ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import html
from db import get_all_users, get_subscription, add_sub_url, delete_subscription, get_user_counts, get_info_subscription
from filters.admin import IsAdminFilter
from kb import admin_kb, edit_sub
from logger import logger
from utils_bot.utils import broadcast_message

router = Router()


class Form(StatesGroup):
    start_broadcast = State()
    sub_action = State()


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
    # logger.debug(f"Список пользователей {users}")
    if not users:
        await call.message.answer(
            "📭 Нет пользователей для экспорта.", reply_markup=admin_kb()
        )
        return

    csv_data = "tg_id, Дата и время подписки\n"  # Заголовщк CSV
    for user in users:
        csv_data += f"{user[0]}, {user[1]}\n"
        # logger.debug(f"{user[0]}, {user[1]}")

    file_name = BytesIO(csv_data.encode("utf-8-sig"))
    file_name.seek(0)

    file = BufferedInputFile(file_name.getvalue(), filename="users_export.xlsx")

    await call.message.answer_document(
        file,
        caption=text,
        reply_markup=admin_kb(),
    )
    file_name.close()


@router.callback_query(F.data == 'admin_broadcast', IsAdminFilter())
async def admin_broadcast_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.answer(
        'Отправьте любое сообщение, а я его перехвачу и перешлю всем пользователям с базы данных'
    )
    await state.set_state(Form.start_broadcast)


@router.callback_query(F.data == "subscription", IsAdminFilter())
async def handle_subscription(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    dict_subscription: dict = await get_subscription()
    builder = InlineKeyboardBuilder()
    text = ''
    if dict_subscription:
        text = '<b>Обязательные подписки: </b>'
        for k, v in dict_subscription.items():
            builder.row(InlineKeyboardButton(text=f"{k}", callback_data=f"view_{v}"))
    else:
        text = "<b>Добавить подписку</b> 👇"
    builder.row(InlineKeyboardButton(text="Добавить подписку", callback_data="add_sub"))
    builder.row(InlineKeyboardButton(text="Назад", callback_data="admin_panel"))
    await callback.message.answer(text, reply_markup=builder.as_markup())


@router.message(F.content_type.in_({'text', 'photo', 'document', 'video', 'audio'}), Form.start_broadcast,
                IsAdminFilter())
async def universe_broadcast(message: Message, state: FSMContext):
    users_data = await get_all_users()
    await message.answer(f'Начинаю рассылку на {len(users_data)} пользователей.')

    # Определяем параметры для рассылки в зависимости от типа сообщения
    content_type = message.content_type

    good_send, bad_send = await broadcast_message(
        users_data=users_data,
        text=message.text if content_type == ContentType.TEXT else None,
        photo_id=message.photo[-1].file_id if content_type == ContentType.PHOTO else None,
        document_id=message.document.file_id if content_type == ContentType.DOCUMENT else None,
        video_id=message.video.file_id if content_type == ContentType.VIDEO else None,
        audio_id=message.audio.file_id if content_type == ContentType.AUDIO else None,
        caption=message.caption,
        content_type=content_type
    )
    buttons = InlineKeyboardBuilder()
    buttons.row(InlineKeyboardButton(text="Админ_панель", callback_data="admin_panel"))
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
    text = (f"<b>Подписка</b> {link}\n"
            f"<b>Статус</b> {activ_sub}\n"
            f"<b>Пользователей подписалось</b> {info_sub['users_actual']}\n"
            f"<b>Установленный лимит подписчиков</b> {info_sub['users_set']}")
    await callback.message.answer(text, reply_markup=kb.as_markup())


@router.callback_query(F.data == "add_sub", IsAdminFilter())
async def handle_add_sub(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("<b>Пожалуйста, введите ссылку на канал и его название, разделив их символом '|'.</b>\n"
                                  "Пример: 👇\n\nhttps://t.me/username|название канала|количество пользователей\n\n"
                                  "Обратите внимание, что название канала должно быть коротким и легко воспринимаемым для вас.")
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
    await message.answer("Подписка принята", reply_markup=buttons.as_markup())


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
