from telegram import ReplyKeyboardMarkup
from sqlalchemy import select
from database.models import SessionLocal, Category, Subcategory


ADMIN_MENU = ReplyKeyboardMarkup([
    ["📤 Загрузить баннер"],
    ["📂 Загрузить список товаров"],
    ["➕ Добавить категорию"],
    ["⬅️ Назад"]
], resize_keyboard=True)

def placement_type_keyboard():
    keyboard = [
        ["Главное меню"],
        ["Категория"],
        ["Подкатегория"],
        ["⬅️ Отмена"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def admin_categories_keyboard():
    async with SessionLocal() as db:
        # Получаем все категории из базы данных
        categories_result = await db.execute(select(Category))
        categories = categories_result.scalars().all()

        # Формируем список названий категорий
        category_names = [category.name for category in categories]

        # Создаем клавиатуру
        keyboard = []
        for i in range(0, len(category_names), 2):
            keyboard.append(category_names[i:i+2])
        keyboard.append(["⬅️ Назад"])

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)



async def admin_subcategories_keyboard(category):
    async with SessionLocal() as db:
        # Находим категорию по имени
        category_result = await db.execute(
            select(Category).where(Category.name == category)
        )
        category_obj = category_result.scalar()

        if not category_obj:
            # Если категория не найдена, возвращаем клавиатуру с кнопкой "Назад"
            return ReplyKeyboardMarkup([["⬅️ Назад"]], resize_keyboard=True)

        # Получаем все подкатегории для данной категории
        subcategories_result = await db.execute(
            select(Subcategory).where(Subcategory.category_id == category_obj.id)
        )
        subcategories = subcategories_result.scalars().all()

        # Формируем список названий подкатегорий
        subcategory_names = [subcategory.name for subcategory in subcategories]

        # Создаем клавиатуру
        keyboard = []
        for i in range(0, len(subcategory_names), 2):
            keyboard.append(subcategory_names[i:i+2])
        keyboard.append(["⬅️ Назад"])

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def manage_categories_keyboard():
    keyboard = [
        ["➕ Добавить категорию", "✏️ Изменить категорию"],
        ["➖ Удалить категорию", "➕ Добавить подкатегорию"],
        ["✏️ Изменить подкатегорию", "➖ Удалить подкатегорию"],
        ["⬅️ Назад"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)