from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, UniqueConstraint

# Настройки подключения к базе данных
DATABASE_URL = "postgresql+asyncpg://botcanal:botcanal@localhost:5432/botcanal"

# Создание асинхронного движка SQLAlchemy
engine = create_async_engine(DATABASE_URL, echo=True)

# Создание асинхронной сессии
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Базовый класс для моделей
Base = declarative_base()

class Banner(Base):
    __tablename__ = "banners"
    id = Column(Integer, primary_key=True)
    category_id = Column(String, ForeignKey("categories.id"), nullable=True)
    subcategory_id = Column(Integer, ForeignKey("subcategories.id"), nullable=True)
    image_url = Column(String, nullable=False)
    file_type = Column(String, nullable=False)

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    subcategories = relationship("Subcategory", back_populates="category", cascade="all, delete-orphan")

class Subcategory(Base):
    __tablename__ = "subcategories"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    category = relationship("Category", back_populates="subcategories")
    products = relationship("ProductList", back_populates="subcategory", cascade="all, delete-orphan")

class ProductList(Base):
    __tablename__ = 'product_lists'
    id = Column(Integer, primary_key=True)
    subcategory_id = Column(Integer, ForeignKey("subcategories.id", ondelete="CASCADE"), nullable=False)
    product_text = Column(String(4000), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    subcategory = relationship("Subcategory", back_populates="products")