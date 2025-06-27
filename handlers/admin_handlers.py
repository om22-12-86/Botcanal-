from telegram import Update
from datetime import datetime
from sqlalchemy import Text
from sqlalchemy.exc import DataError
from telegram.error import BadRequest
from telegram.ext import CallbackContext, ConversationHandler, MessageHandler, filters
from keyboards.admin_keyboards import (
    ADMIN_MENU,
    placement_type_keyboard,
    admin_categories_keyboard,
    admin_subcategories_keyboard,
    manage_categories_keyboard
)
from config import ADMIN_IDS
from database.models import SessionLocal, Category, Subcategory, Banner, ProductList
from sqlalchemy import select, delete

import logging

logger = logging.getLogger(__name__)

SELECTING_PLACEMENT, SELECTING_CATEGORY, SELECTING_SUBCATEGORY, UPLOADING_MEDIA = map(str, range(4))
SELECTING_CATEGORY_FOR_PRODUCT, SELECTING_SUBCATEGORY_FOR_PRODUCT, UPLOADING_LIST = range(3)
MANAGE_CATEGORIES = "MANAGE_CATEGORIES"

async def admin(update: Update, context: CallbackContext):
    if update.message.from_user.id in ADMIN_IDS:
        await update.message.reply_text("Панель администратора:", reply_markup=ADMIN_MENU)
        return ConversationHandler.END
    else:
        await update.message.reply_text("У вас нет прав администратора!")
        return ConversationHandler.END

async def start_banner_upload(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("У вас нет прав на загрузку баннера!")
        return ConversationHandler.END

    await update.message.reply_text(
        "Выберите место размещения баннера:",
        reply_markup=placement_type_keyboard()
    )
    return SELECTING_PLACEMENT

async def select_placement_type(update: Update, context: CallbackContext):
    placement = update.message.text
    context.user_data['placement'] = {}

    if placement == "Главное меню":
        context.user_data['placement']['type'] = 'main'
        await update.message.reply_text("Отправьте фото/гифку для главного меню")
        return UPLOADING_MEDIA
    elif placement == "Категория":
        context.user_data['placement']['type'] = 'category'
        await update.message.reply_text("Выберите категорию:", reply_markup=admin_categories_keyboard())
        return SELECTING_CATEGORY
    elif placement == "Подкатегория":
        context.user_data['placement']['type'] = 'subcategory'
        await update.message.reply_text("Сначала выберите категорию:", reply_markup=admin_categories_keyboard())
        return SELECTING_CATEGORY
    elif placement == "⬅️ Отмена":
        return await handle_back(update, context)

async def select_category(update: Update, context: CallbackContext):
    category = update.message.text
    placement_type = context.user_data['placement'].get('type')

    if category == "⬅️ Назад":
        return await handle_back(update, context)

    if placement_type == 'category':
        context.user_data['placement']['category'] = category
        await update.message.reply_text("Отправьте фото/гифку для категории")
        return UPLOADING_MEDIA

    elif placement_type == 'subcategory':
        context.user_data['placement']['category'] = category
        await update.message.reply_text(
            "Выберите подкатегорию:",
            reply_markup=await admin_subcategories_keyboard(category)  # Асинхронный вызов
        )
        return SELECTING_SUBCATEGORY


async def select_subcategory(update: Update, context: CallbackContext):
    subcategory_name = update.message.text

    # Проверяем, нажата ли кнопка "⬅️ Назад"
    if subcategory_name == "⬅️ Назад" or subcategory_name == ".":
        return await handle_back(update, context)

    async with SessionLocal() as db:
        # Ищем подкатегорию в базе данных
        subcategory_result = await db.execute(
            select(Subcategory).where(Subcategory.name == subcategory_name)
        )
        subcategory = subcategory_result.scalar()

        # Если подкатегория не найдена, сообщаем об этом
        if not subcategory:
            await update.message.reply_text("Подкатегория не найдена.")
            return SELECTING_SUBCATEGORY

        # Сохраняем данные о подкатегории
        context.user_data['placement']['subcategory'] = subcategory.name
        context.user_data['placement']['subcategory_id'] = subcategory.id

        await db.commit()

        # Переходим к следующему шагу
        await update.message.reply_text("Отправьте фото/гифку для подкатегории")
        return UPLOADING_MEDIA


async def upload_media(update: Update, context: CallbackContext):
    placement = context.user_data.get('placement', {})
    file_id = None
    file_type = None

    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        file_type = "photo"
    elif update.message.animation:
        file_id = update.message.animation.file_id
        file_type = "animation"
    elif update.message.document:
        mime_type = update.message.document.mime_type
        if mime_type in ["image/gif", "video/mp4"]:
            file_id = update.message.document.file_id
            file_type = "animation"
        else:
            await update.message.reply_text("Неподдерживаемый тип файла. Используйте фото или гифку.")
            return UPLOADING_MEDIA
    else:
        await update.message.reply_text("Неподдерживаемый тип файла. Используйте фото или гифку.")
        return UPLOADING_MEDIA

    async with SessionLocal() as db:
        try:
            banner = Banner(
                category_id=None if placement['type'] == 'main' else placement.get('category', None),
                subcategory_id=placement.get('subcategory_id', None),
                image_url=file_id,
                file_type=file_type
            )
            db.add(banner)
            await db.commit()
            await update.message.reply_text("Баннер успешно сохранен!", reply_markup=ADMIN_MENU)
        except Exception as e:
            logger.error(f"Ошибка при сохранении баннера: {e}")
            await db.rollback()
            await update.message.reply_text("Произошла ошибка при сохранении баннера. Попробуйте еще раз.")
            return UPLOADING_MEDIA

    context.user_data.clear()
    return ConversationHandler.END

async def handle_back(update: Update, context: CallbackContext):
    # Очищаем данные пользователя
    context.user_data.clear()

    # Возвращаем пользователя в главное меню администратора
    await update.message.reply_text(
        "Возвращаемся в главное меню админа:",
        reply_markup=ADMIN_MENU
    )

    # Завершаем текущий процесс
    return ConversationHandler.END


async def start_product_upload(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет прав администратора!")
        return ConversationHandler.END

    await update.message.reply_text(
        "Выберите категорию для загрузки списка товаров:",
        reply_markup=await admin_categories_keyboard()  # Асинхронный вызов
    )
    return SELECTING_CATEGORY_FOR_PRODUCT

async def select_category_for_product(update: Update, context: CallbackContext):
    category_name = update.message.text
    context.user_data['selected_category'] = category_name

    await update.message.reply_text(
        "Выберите подкатегорию:",
        reply_markup=await admin_subcategories_keyboard(category_name)  # Асинхронный вызов
    )
    return SELECTING_SUBCATEGORY_FOR_PRODUCT


async def select_subcategory_for_product(update: Update, context: CallbackContext):
    subcategory_name = update.message.text

    if subcategory_name == "⬅️ Назад":
        return await handle_back(update, context)

    async with SessionLocal() as db:
        subcategory_result = await db.execute(
            select(Subcategory).where(Subcategory.name == subcategory_name)
        )
        subcategory = subcategory_result.scalar()

        if not subcategory:
            await update.message.reply_text("Подкатегория не найдена.")
            return SELECTING_SUBCATEGORY_FOR_PRODUCT

        context.user_data['selected_subcategory'] = subcategory
        await db.commit()

        await update.message.reply_text("Отправьте список товаров для этой подкатегории:")
        return UPLOADING_LIST

async def upload_product_list(update: Update, context: CallbackContext):
    subcategory = context.user_data.get('selected_subcategory')
    product_text = update.message.text

    if len(product_text) > 4000:
        await update.message.reply_text(
            "❌ Ошибка: текст списка товаров превышает 4000 символов.",
            reply_markup=ADMIN_MENU
        )
        return UPLOADING_LIST

    async with SessionLocal() as db:
        subcategory_result = await db.execute(select(Subcategory).where(Subcategory.id == subcategory.id))
        subcategory_db = subcategory_result.scalar()

        if not subcategory_db:
            await update.message.reply_text("❌ Подкатегория не найдена.")
            return UPLOADING_LIST

        await db.execute(delete(ProductList).where(ProductList.subcategory_id == subcategory_db.id))

        new_product_list = ProductList(
            subcategory_id=subcategory_db.id,
            product_text=product_text,
            updated_at=datetime.utcnow()
        )

        db.add(new_product_list)
        await db.commit()

        await update.message.reply_text("✅ Список товаров успешно загружен.")

        return ConversationHandler.END

async def start_manage_categories(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет прав администратора!")
        return ConversationHandler.END

    await update.message.reply_text(
        "Управление категориями и подкатегориями:",
        reply_markup=manage_categories_keyboard()
    )
    return MANAGE_CATEGORIES

async def add_category(update: Update, context: CallbackContext):
    await update.message.reply_text("Введите название новой категории:")
    return "ADD_CATEGORY"

async def save_category(update: Update, context: CallbackContext):
    category_name = update.message.text

    async with SessionLocal() as db:
        category = Category(name=category_name)
        db.add(category)
        await db.commit()

    await update.message.reply_text(f"Категория '{category_name}' успешно добавлена.", reply_markup=ADMIN_MENU)
    return ConversationHandler.END

async def delete_category(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Выберите категорию для удаления:",
        reply_markup=await admin_categories_keyboard()  # Асинхронный вызов
    )
    return "DELETE_CATEGORY"

async def confirm_delete_category(update: Update, context: CallbackContext):
    category_name = update.message.text

    async with SessionLocal() as db:
        # Находим категорию по имени
        category_result = await db.execute(
            select(Category).where(Category.name == category_name)
        )
        category = category_result.scalar()

        if not category:
            await update.message.reply_text("❌ Категория не найдена.")
            return "DELETE_CATEGORY"

        # Удаляем категорию
        try:
            await db.execute(delete(Category).where(Category.id == category.id))
            await db.commit()

            # Очищаем текущую категорию в context.user_data, если она была удалена
            if context.user_data.get('current_category') == category.id:
                context.user_data.pop('current_category', None)

            await update.message.reply_text(f"✅ Категория '{category_name}' успешно удалена.", reply_markup=ADMIN_MENU)
        except Exception as e:
            logger.error(f"Ошибка при удалении категории: {e}")
            await db.rollback()
            await update.message.reply_text("❌ Произошла ошибка при удалении категории. Попробуйте еще раз.")

    return ConversationHandler.END


async def confirm_delete_subcategory(update: Update, context: CallbackContext):
    subcategory_name = update.message.text

    # Получаем категорию из context.user_data
    category_name = context.user_data.get('selected_category')

    async with SessionLocal() as db:
        # Находим категорию
        category_result = await db.execute(
            select(Category).where(Category.name == category_name)
        )
        category = category_result.scalar()

        if not category:
            await update.message.reply_text("❌ Категория не найдена.")
            return "DELETE_SUBCATEGORY"

        # Находим подкатегорию по имени и ID категории
        subcategory_result = await db.execute(
            select(Subcategory).where(
                Subcategory.name == subcategory_name,
                Subcategory.category_id == category.id
            )
        )
        subcategory = subcategory_result.scalar()

        if not subcategory:
            await update.message.reply_text(f"❌ Подкатегория '{subcategory_name}' не найдена в категории '{category_name}'.")
            return "DELETE_SUBCATEGORY"

        # Удаляем подкатегорию
        try:
            await db.execute(delete(Subcategory).where(Subcategory.id == subcategory.id))
            await db.commit()

            # Очищаем текущую подкатегорию в context.user_data, если она была удалена
            if context.user_data.get('current_subcategory') == subcategory.id:
                context.user_data.pop('current_subcategory', None)

            await update.message.reply_text(f"✅ Подкатегория '{subcategory_name}' успешно удалена.", reply_markup=ADMIN_MENU)
        except Exception as e:
            logger.error(f"Ошибка при удалении подкатегории: {e}")
            await db.rollback()
            await update.message.reply_text("❌ Произошла ошибка при удалении подкатегории. Попробуйте еще раз.")

    return ConversationHandler.END



async def add_subcategory(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Выберите категорию для добавления подкатегории:",
        reply_markup=await admin_categories_keyboard()  # Асинхронный вызов
    )
    return "ADD_SUBCATEGORY"

async def save_subcategory(update: Update, context: CallbackContext):
    subcategory_name = update.message.text
    category_name = context.user_data.get('selected_category')

    async with SessionLocal() as db:
        category_result = await db.execute(select(Category).where(Category.name == category_name))
        category = category_result.scalar()

        if not category:
            await update.message.reply_text("Категория не найдена.")
            return "ADD_SUBCATEGORY"

        subcategory = Subcategory(name=subcategory_name, category_id=category.id)
        db.add(subcategory)
        await db.commit()

    await update.message.reply_text(f"Подкатегория '{subcategory_name}' успешно добавлена.", reply_markup=ADMIN_MENU)
    return ConversationHandler.END

async def delete_subcategory(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Выберите категорию, из которой хотите удалить подкатегорию:",
        reply_markup=admin_categories_keyboard()
    )
    return "SELECT_CATEGORY_FOR_DELETE_SUBCATEGORY"


async def select_category_for_delete_subcategory(update: Update, context: CallbackContext):
    category_name = update.message.text
    context.user_data['selected_category'] = category_name

    await update.message.reply_text(
        "Выберите подкатегорию для удаления:",
        reply_markup=await admin_subcategories_keyboard(category_name)  # Асинхронный вызов
    )
    return "DELETE_SUBCATEGORY"


async def confirm_delete_subcategory(update: Update, context: CallbackContext):
    subcategory_name = update.message.text

    # Получаем категорию из context.user_data
    category_name = context.user_data.get('selected_category')

    async with SessionLocal() as db:
        # Находим категорию
        category_result = await db.execute(
            select(Category).where(Category.name == category_name)
        )
        category = category_result.scalar()

        if not category:
            await update.message.reply_text("❌ Категория не найдена.")
            return "DELETE_SUBCATEGORY"

        # Находим подкатегорию по имени и ID категории
        subcategory_result = await db.execute(
            select(Subcategory).where(
                Subcategory.name == subcategory_name,
                Subcategory.category_id == category.id
            )
        )
        subcategory = subcategory_result.scalar()

        if not subcategory:
            await update.message.reply_text(f"❌ Подкатегория '{subcategory_name}' не найдена в категории '{category_name}'.")
            return "DELETE_SUBCATEGORY"

        # Удаляем подкатегорию
        try:
            await db.execute(delete(Subcategory).where(Subcategory.id == subcategory.id))
            await db.commit()
            await update.message.reply_text(f"✅ Подкатегория '{subcategory_name}' успешно удалена.", reply_markup=ADMIN_MENU)
        except Exception as e:
            logger.error(f"Ошибка при удалении подкатегории: {e}")
            await db.rollback()
            await update.message.reply_text("❌ Произошла ошибка при удалении подкатегории. Попробуйте еще раз.")

    return ConversationHandler.END


banner_upload_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Text("📤 Загрузить баннер"), start_banner_upload)],
    states={
        SELECTING_PLACEMENT: [MessageHandler(filters.TEXT, select_placement_type)],
        SELECTING_CATEGORY: [MessageHandler(filters.TEXT, select_category)],
        SELECTING_SUBCATEGORY: [MessageHandler(filters.TEXT, select_subcategory)],
        UPLOADING_MEDIA: [MessageHandler(filters.PHOTO | filters.Document.IMAGE | filters.Document.VIDEO, upload_media)],
    },
    fallbacks=[MessageHandler(filters.Text("⬅️ Назад"), handle_back)],
)

product_upload_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Text("📂 Загрузить список товаров"), start_product_upload)],
    states={
        SELECTING_CATEGORY_FOR_PRODUCT: [MessageHandler(filters.TEXT, select_category_for_product)],
        SELECTING_SUBCATEGORY_FOR_PRODUCT: [MessageHandler(filters.TEXT, select_subcategory_for_product)],
        UPLOADING_LIST: [MessageHandler(filters.TEXT, upload_product_list)],
    },
    fallbacks=[MessageHandler(filters.Text("⬅️ Назад"), handle_back)],
)

manage_categories_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Text("➕ Добавить категорию"), start_manage_categories)],
    states={
        MANAGE_CATEGORIES: [
            MessageHandler(filters.Text("➕ Добавить категорию"), add_category),
            MessageHandler(filters.Text("➖ Удалить категорию"), delete_category),
            MessageHandler(filters.Text("➕ Добавить подкатегорию"), add_subcategory),
            MessageHandler(filters.Text("➖ Удалить подкатегорию"), delete_subcategory),
        ],
        "ADD_CATEGORY": [MessageHandler(filters.TEXT, save_category)],
        "DELETE_CATEGORY": [MessageHandler(filters.TEXT, confirm_delete_category)],
        "ADD_SUBCATEGORY": [MessageHandler(filters.TEXT, save_subcategory)],
        "SELECT_CATEGORY_FOR_DELETE_SUBCATEGORY": [MessageHandler(filters.TEXT, select_category_for_delete_subcategory)],
        "DELETE_SUBCATEGORY": [MessageHandler(filters.TEXT, confirm_delete_subcategory)],
    },
    fallbacks=[MessageHandler(filters.Text("⬅️ Назад"), handle_back)],
)