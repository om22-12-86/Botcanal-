from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import SessionLocal, Category, Subcategory
from sqlalchemy import select

# Главное меню для пользователей
def user_main_menu():
    buttons = [
        [InlineKeyboardButton("Каталог 📦", callback_data="catalog")],
        [InlineKeyboardButton("Контакты ☎️", url="https://t.me/CityGadgets_TopCase")]
    ]
    return InlineKeyboardMarkup(buttons)

# Динамическая клавиатура категорий с кнопкой "Контакты ☎️"
async def categories_keyboard():
    async with SessionLocal() as db:
        # Получаем все категории из базы данных
        categories_result = await db.execute(select(Category))
        categories = categories_result.scalars().all()

    buttons = []

    # Группируем категории по две в каждой строке
    for i in range(0, len(categories), 2):
        row = []
        # Добавляем первую кнопку в строку
        if i < len(categories):
            row.append(InlineKeyboardButton(categories[i].name, callback_data=f"category_{categories[i].id}"))
        # Добавляем вторую кнопку в строку, если она существует
        if i + 1 < len(categories):
            row.append(InlineKeyboardButton(categories[i + 1].name, callback_data=f"category_{categories[i + 1].id}"))
        buttons.append(row)

    # Добавляем кнопки "Назад" и "Контакты" в последнюю строку
    buttons.append([
        InlineKeyboardButton("⬅️ Назад", callback_data="back"),
        InlineKeyboardButton("Контакты ☎️", url="https://t.me/CityGadgets_TopCase")
    ])

    return InlineKeyboardMarkup(buttons)

# Динамическая клавиатура подкатегорий с кнопкой "Контакты ☎️"
async def subcategories_keyboard(category_id: int):
    """Создаёт клавиатуру для подкатегорий по category_id"""
    async with SessionLocal() as db:
        # Получаем все подкатегории для выбранной категории
        subcategories_result = await db.execute(
            select(Subcategory).where(Subcategory.category_id == category_id)
        )
        subcategories = subcategories_result.scalars().all()

    buttons = []

    # Группируем подкатегории по две в каждой строке
    for i in range(0, len(subcategories), 2):
        row = []
        # Добавляем первую кнопку в строку
        if i < len(subcategories):
            row.append(InlineKeyboardButton(subcategories[i].name, callback_data=f"subcategory_{subcategories[i].id}"))
        # Добавляем вторую кнопку в строку, если она существует
        if i + 1 < len(subcategories):
            row.append(InlineKeyboardButton(subcategories[i + 1].name, callback_data=f"subcategory_{subcategories[i + 1].id}"))
        buttons.append(row)

    # Добавляем кнопки "Назад" и "Контакты" в последнюю строку
    buttons.append([
        InlineKeyboardButton("⬅️ Назад", callback_data="catalog"),
        InlineKeyboardButton("Контакты ☎️", url="https://t.me/CityGadgets_TopCase")
    ])

    return InlineKeyboardMarkup(buttons)

# Кнопка "Назад" с "Контакты ☎️"
def back_button():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Назад", callback_data="back")],
        [InlineKeyboardButton("Контакты ☎️", url="https://t.me/CityGadgets_TopCase")]
    ])