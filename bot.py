import logging
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters
)
from config import BOT_TOKEN
from handlers.user_handlers import start, handle_catalog, handle_category_selection, handle_subcategory_selection, handle_back
from handlers.admin_handlers import admin, banner_upload_handler, product_upload_handler, manage_categories_handler

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def main():
    # Создание приложения бота
    app = Application.builder().token(BOT_TOKEN).build()

    # Обработчики команд
    app.add_handler(CommandHandler("start", start))  # Обработчик команды /start
    app.add_handler(CommandHandler("admin", admin))  # Обработчик команды /admin

    # Пользовательские обработчики
    app.add_handler(CallbackQueryHandler(handle_catalog, pattern="catalog"))  # Обработчик каталога
    app.add_handler(CallbackQueryHandler(handle_category_selection, pattern="category_"))  # Обработчик выбора категории
    app.add_handler(CallbackQueryHandler(handle_subcategory_selection, pattern="subcategory_"))  # Обработчик выбора подкатегории
    app.add_handler(CallbackQueryHandler(handle_back, pattern="back"))  # Обработчик кнопки "Назад"

    # Обработчик загрузки списка товаров
    app.add_handler(product_upload_handler)

    # Обработчик загрузки баннера
    app.add_handler(banner_upload_handler)

    # Обработчик управления категориями (добавление, изменение, удаление)
    app.add_handler(manage_categories_handler)

    # Запуск бота
    print("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()