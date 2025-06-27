from database.models import SessionLocal

async def save_banner(category: str, subcategory_id: int, file_id: str):
    async with SessionLocal() as db:
        banner = Banner(category=category, subcategory_id=subcategory_id, image_url=file_id)
        db.add(banner)
        await db.commit()