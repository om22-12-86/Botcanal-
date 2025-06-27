from datetime import datetime
from sqlalchemy import Text
from telegram import Update, InlineKeyboardMarkup, InputMediaPhoto, InlineKeyboardButton
from telegram.ext import CallbackContext
from telegram.error import BadRequest
from keyboards.user_keyboards import (
    user_main_menu,
    categories_keyboard,
    subcategories_keyboard,
    back_button
)
from sqlalchemy import select
from database.models import SessionLocal, Banner, Subcategory, ProductList, Category
import logging

logger = logging.getLogger(__name__)
MAIN_MENU, CATEGORY, SUBCATEGORY = range(3)

async def start(update: Update, context: CallbackContext):
    async with SessionLocal() as db:
        # Исправляем запрос, чтобы category_id сравнивался с текстовым значением
        banner = await db.execute(
            select(Banner).where(Banner.category_id == "Главное меню")
        )
        banner = banner.scalars().first()

    if banner and banner.image_url:
        try:
            await update.message.reply_photo(
                photo=banner.image_url,
                caption=(
                    "Добро пожаловать в магазин! Если вы не нашли интересующий Вас товар, "
                    "напишите нам на страницу @CityGadgets_TopCase, и мы сделаем все возможное, "
                    "чтобы найти его для Вас."
                ),
                reply_markup=user_main_menu()
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке фото: {e}")
            await update.message.reply_text("Произошла ошибка при отправке баннера.")
    else:
        logger.warning("Баннер для главного меню не найден или file_id отсутствует")
        await update.message.reply_text(
            "Добро пожаловать в магазин! Если вы не нашли интересующий Вас товар, "
            "напишите нам на страницу @CityGadgets_TopCase, и мы сделаем все возможное, "
            "чтобы найти его для Вас.",
            reply_markup=user_main_menu()
        )


async def show_menu(update: Update, context: CallbackContext, menu_type: int):
    query = update.callback_query if hasattr(update, 'callback_query') else None
    user_data = context.user_data
    history = user_data.setdefault('history', [])

    new_state = {
        'type': menu_type,
        'text': get_menu_text(menu_type, user_data),
        'markup': await get_menu_markup(menu_type, user_data),  # Добавляем await
        'timestamp': datetime.now()
    }

    if not history or history[-1]['type'] != new_state['type']:
        history.append(new_state)

    if len(history) > 10:
        history.pop(0)

    modified_text = f"{new_state['text']}\u200B"

    if menu_type == MAIN_MENU:
        async with SessionLocal() as db:
            banner = await db.execute(
                select(Banner).where(Banner.category_id == "Главное меню")
            )
            banner = banner.scalars().first()

        if banner and banner.image_url:
            try:
                if query:
                    await query.edit_message_media(
                        media=InputMediaPhoto(media=banner.image_url)
                    )
                    await query.edit_message_caption(
                        caption=modified_text,
                        reply_markup=new_state['markup']
                    )
                else:
                    await update.message.reply_photo(
                        photo=banner.image_url,
                        caption=modified_text,
                        reply_markup=new_state['markup']
                    )
            except Exception as e:
                logger.error(f"Ошибка при отправке фото: {e}")
                await update.message.reply_text("Произошла ошибка при отправке баннера.")
        else:
            logger.warning("Баннер для главного меню не найден или file_id отсутствует")
            if query:
                await query.edit_message_text(
                    text=modified_text,
                    reply_markup=new_state['markup']
                )
            else:
                await update.message.reply_text(
                    text=modified_text,
                    reply_markup=new_state['markup']
                )
    else:
        if query:
            try:
                await query.edit_message_text(
                    text=modified_text,
                    reply_markup=new_state['markup']
                )
            except BadRequest:
                await query.edit_message_caption(
                    caption=modified_text,
                    reply_markup=new_state['markup']
                )
        else:
            await update.message.reply_text(
                text=modified_text,
                reply_markup=new_state['markup']
            )

async def show_category_products(update: Update, context: CallbackContext):
    category_id = context.user_data.get("current_category")
    query = update.callback_query if hasattr(update, 'callback_query') else None

    async with SessionLocal() as db:
        # Находим категорию по ID
        category_result = await db.execute(select(Category).where(Category.id == category_id))
        category = category_result.scalar()

        if not category:
            logger.error(f"Категория с ID {category_id} не найдена")
            if query:
                try:
                    await query.edit_message_text("Ошибка: категория не найдена.")
                except BadRequest:
                    await query.edit_message_caption(caption="Ошибка: категория не найдена.")
            else:
                await update.message.reply_text("Ошибка: категория не найдена.")
            return

        # Получаем баннер для категории
        banner = await db.execute(select(Banner).where(Banner.category_id == category.name))
        banner = banner.scalars().first()

    # Формируем клавиатуру для подкатегорий
    keyboard = await subcategories_keyboard(category_id)  # Используем await

    if banner and banner.image_url:
        if query:
            try:
                await query.edit_message_media(InputMediaPhoto(media=banner.image_url))
                await query.edit_message_caption(
                    caption=f"Товары для категории {category.name}:",
                    reply_markup=keyboard
                )
            except Exception as e:
                logger.error(f"Ошибка при отправке фото: {e}")
                await query.edit_message_text(f"Товары для категории {category.name}:", reply_markup=keyboard)
        else:
            await update.message.reply_photo(
                photo=banner.image_url,
                caption=f"Товары для категории {category.name}:",
                reply_markup=keyboard
            )
    else:
        if query:
            try:
                await query.edit_message_text(f"Товары для категории {category.name}:", reply_markup=keyboard)
            except BadRequest:
                await query.edit_message_caption(caption=f"Товары для категории {category.name}:", reply_markup=keyboard)
        else:
            await update.message.reply_text(f"Товары для категории {category.name}:", reply_markup=keyboard)


async def show_subcategory_products(update: Update, context: CallbackContext):
    subcategory_id = context.user_data.get("current_subcategory")

    if not subcategory_id:
        logger.error("subcategory_id не найден в user_data")
        if update.message:
            await update.message.reply_text("Ошибка: не найдена подкатегория.")
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text("Ошибка: не найдена подкатегория.")
        return

    query = update.callback_query if hasattr(update, 'callback_query') else None

    async with SessionLocal() as db:
        # Получаем подкатегорию
        subcategory_result = await db.execute(select(Subcategory).where(Subcategory.id == subcategory_id))
        subcategory = subcategory_result.scalar()

        if not subcategory:
            logger.error(f"Подкатегория с ID {subcategory_id} не найдена")
            if query:
                await query.edit_message_text("Ошибка: подкатегория не найдена.")
            elif update.message:
                await update.message.reply_text("Ошибка: подкатегория не найдена.")
            return

        # Получаем баннер для подкатегории
        banner_result = await db.execute(select(Banner).where(Banner.subcategory_id == subcategory_id))
        banner = banner_result.scalars().first()

        # Получаем список товаров для подкатегории
        product_result = await db.execute(select(ProductList).where(ProductList.subcategory_id == subcategory_id))
        product_list = product_result.scalars().all()

        if not product_list:
            if query:
                await query.edit_message_text("❌ В этой подкатегории пока нет товаров.")
            elif update.message:
                await update.message.reply_text("❌ В этой подкатегории пока нет товаров.")
            return

        # Формируем текст списка товаров
        product_text = f"📜 <b>Список товаров для {subcategory.name}:</b>\n\n"
        for product in product_list:
            product_text += product.product_text + "\n"

        # Разделяем текст на части, если он превышает 1024 символа (ограничение Telegram для подписи к медиа)
        max_caption_length = 1024
        if len(product_text) > max_caption_length:
            caption = product_text[:max_caption_length]  # Первые 1024 символа для подписи
            remaining_text = product_text[max_caption_length:]  # Остальной текст
        else:
            caption = product_text
            remaining_text = None

        # Отправляем баннер, если он есть
        if banner and banner.image_url:
            try:
                if query:
                    await query.edit_message_media(
                        InputMediaPhoto(media=banner.image_url, caption=caption, parse_mode="HTML")
                    )
                elif update.message:
                    await update.message.reply_photo(
                        photo=banner.image_url, caption=caption, parse_mode="HTML"
                    )
            except Exception as e:
                logger.error(f"Ошибка при отправке фото: {e}")
                if update.message:
                    await update.message.reply_text(caption, parse_mode="HTML")
        else:
            if query:
                await query.edit_message_text(caption, parse_mode="HTML")
            elif update.message:
                await update.message.reply_text(caption, parse_mode="HTML")

        # Отправляем остальную часть списка товаров, если она есть
        if remaining_text:
            # Разделяем оставшийся текст на части, если он превышает 4096 символов (ограничение Telegram для текстовых сообщений)
            max_text_length = 4096
            if len(remaining_text) > max_text_length:
                parts = [remaining_text[i:i + max_text_length] for i in range(0, len(remaining_text), max_text_length)]
            else:
                parts = [remaining_text]

            for part in parts:
                if update.message:
                    await update.message.reply_text(part, parse_mode="HTML")
                elif query:
                    await query.message.reply_text(part, parse_mode="HTML")

        # Добавляем кнопки "Назад" и "Контакты" в последнее сообщение
        keyboard = [
            [InlineKeyboardButton("⬅️ Назад", callback_data=f"category_{subcategory.category_id}")],
            [InlineKeyboardButton("📦 Каталог", callback_data="catalog")],
            [InlineKeyboardButton("Контакты ☎️", url="https://t.me/CityGadgets_TopCase")]
        ]
        markup = InlineKeyboardMarkup(keyboard)

        if query:
            await query.message.reply_text("Выберите действие:", reply_markup=markup)
        elif update.message:
            await update.message.reply_text("Выберите действие:", reply_markup=markup)

async def show_catalog(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    # Получаем клавиатуру с категориями
    keyboard = await categories_keyboard()  # Используем await

    try:
        await query.edit_message_text("Выберите категорию:", reply_markup=keyboard)
    except BadRequest:
        await query.message.reply_text("Выберите категорию:", reply_markup=keyboard)



def get_menu_text(menu_type: int, user_data: dict) -> str:
    if menu_type == MAIN_MENU:
        return "Добро пожаловать в магазин! @CityGadgets_TopCase"
    elif menu_type == CATEGORY:
        return "Выберите категорию:"
    elif menu_type == SUBCATEGORY:
        category = user_data.get('current_category', '')
        return f"Выберите подкатегорию для {category}:"
    return ""

async def get_menu_markup(menu_type: int, user_data: dict) -> InlineKeyboardMarkup:
    if menu_type == MAIN_MENU:
        return user_main_menu()
    elif menu_type == CATEGORY:
        return await categories_keyboard()  # Добавляем await
    elif menu_type == SUBCATEGORY:
        category = user_data.get('current_category', '')
        return await subcategories_keyboard(category)  # Добавляем await
    return InlineKeyboardMarkup([])

async def handle_back(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    user_data = context.user_data
    history = user_data.get('history', [])

    if len(history) >= 2:
        history.pop()
        previous_state = history[-1]
        user_data.pop('current_category', None)
        user_data.pop('current_subcategory', None)
        await show_menu(update, context, previous_state['type'])
    else:
        user_data.pop('current_category', None)
        user_data.pop('current_subcategory', None)
        await show_menu(update, context, MAIN_MENU)

async def handle_catalog(update: Update, context: CallbackContext):
    await show_menu(update, context, CATEGORY)

async def handle_category_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    # Получаем ID категории из callback_data
    category_id = int(query.data.split("_")[1])

    async with SessionLocal() as db:
        # Ищем категорию по ID
        category_result = await db.execute(select(Category).where(Category.id == category_id))
        category = category_result.scalar()

        if not category:
            logger.error(f"Ошибка: категория с ID '{category_id}' не найдена в базе")
            try:
                await query.edit_message_text("Ошибка: категория не найдена.")
            except BadRequest:
                await query.edit_message_caption(caption="Ошибка: категория не найдена.")
            return

        # Сохраняем ID категории в user_data
        context.user_data['current_category'] = category.id

        await db.commit()

    # Показываем товары для выбранной категории
    await show_category_products(update, context)


async def handle_subcategory_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    try:
        subcategory_id = int(query.data.split("_")[1])
    except ValueError:
        logger.error(f"Ошибка: невозможно преобразовать {query.data} в ID")
        await query.edit_message_text("Ошибка: неверный формат подкатегории.")
        return

    async with SessionLocal() as db:
        subcategory_result = await db.execute(select(Subcategory).where(Subcategory.id == subcategory_id))
        subcategory = subcategory_result.scalar()

        if not subcategory:
            logger.error(f"Ошибка: подкатегория с ID {subcategory_id} не найдена")
            await query.edit_message_text("Ошибка: подкатегория не найдена.")
            return

        context.user_data['current_subcategory'] = subcategory.id

        await db.commit()
        await show_subcategory_products(update, context)