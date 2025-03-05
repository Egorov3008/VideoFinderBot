from aiogram import Router, F
from aiogram.enums import ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from logger import logger
from db import get_all_users, get_subscription, add_sub_url, delete_subscription, get_user_counts
from filters.admin import IsAdminFilter
from kb import admin_kb, edit_sub
from utils_bot.utils import broadcast_message

router = Router()


class Form(StatesGroup):
    start_broadcast = State()
    sub_action = State()


@router.callback_query(F.data == 'admin_panel', IsAdminFilter())
async def admin_handler(call: CallbackQuery):
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


    await call.message.answer(text, reply_markup=admin_kb())


@router.callback_query(F.data == 'admin_broadcast', IsAdminFilter())
async def admin_broadcast_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.answer(
        'Отправьте любое сообщение, а я его перехвачу и перешлю всем пользователям с базы данных'
    )
    await state.set_state(Form.start_broadcast)


@router.callback_query(F.data == "subscription", IsAdminFilter())
async def handle_subscription(callback: CallbackQuery):
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
    await callback.message.answer(text, reply_markup = builder.as_markup())





@router.message(F.content_type.in_({'text', 'photo', 'document', 'video', 'audio'}), Form.start_broadcast, IsAdminFilter())
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
    kb = edit_sub(url_subscription)
    await state.update_data(url_sub=url_subscription)
    await callback.message.answer("Выберете действие", reply_markup=kb.as_markup())


@router.callback_query(F.data == "add_sub", IsAdminFilter())
async def handle_add_sub(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите ссылку канала и название через '|'\n\n"
                                  "Пример: https://t.me/username|название канала\n"
                                  "Название канала должно быть коротким и понятным для Вас.")
    await state.set_state(Form.sub_action)


@router.message(F.text, Form.sub_action, IsAdminFilter())
async def handle_url_sub(message: Message, state: FSMContext):
    sub_url = message.text.split("|")[0]
    name_sub = message.text.split("|")[1]
    await add_sub_url(name=name_sub, url_sub=sub_url)
    buttons = InlineKeyboardBuilder()
    buttons.row(InlineKeyboardButton(text="Назад", callback_data="subscription"))
    await message.answer("Подписка принята", reply_markup=buttons.as_markup())

@router.callback_query(F.data.startswith("delete_"))
async def handle_delete_sub(callback: CallbackQuery):
    logger.info(callback.data)
    url_subscription = callback.data[7:]
    logger.info(f"Удаляю подписку {url_subscription}")
    await delete_subscription(url_subscription)
    buttons = InlineKeyboardBuilder()
    buttons.row(InlineKeyboardButton(text="Назад", callback_data="subscription"))
    await callback.message.answer("Подписка удалена", reply_markup=buttons.as_markup())




