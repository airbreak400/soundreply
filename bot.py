import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineQuery, InlineQueryResultVoice
from uuid import uuid4
from config import settings
from database import init_db, DatabaseManager
from myinstants import search_instants, get_top_us_sounds

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await DatabaseManager.get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )
    
    text = (
        "👋 <b>Assalomu alaykum!</b>\n\n"
        "Men MyInstants.com dan tovushlar qidiradigan botman!\n\n"
        "📝 <b>Qanday ishlatish:</b>\n"
        "Istalgan chatda quyidagini yozing:\n"
        "<code>@{} tovush nomi</code>\n\n"
        "Masalan:\n"
        "<code>@{} bruh</code>\n"
        "<code>@{} rick roll</code>\n\n"
        "🎵 Yaxshi dam oling!"
    ).format(
        (await bot.get_me()).username,
        (await bot.get_me()).username,
        (await bot.get_me()).username
    )
    
    await message.answer(text)


@dp.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "📖 <b>Yordam</b>\n\n"
        "Bu bot MyInstants.com dan tovushlar qidiradi.\n\n"
        "Istalgan chatda botni chaqiring:\n"
        "<code>@{} qidiruv so'zi</code>\n\n"
        "🔍 Masalan: <code>@{} hallelujah</code>"
    ).format(
        (await bot.get_me()).username,
        (await bot.get_me()).username
    )
    await message.answer(text)


@dp.message(Command("info"))
async def cmd_info(message: Message):
    text = (
        "ℹ️ <b>Bot haqida</b>\n\n"
        "🔹 MyInstants.com tovushlar bazasi\n"
        "🔹 O'zbek tilida\n"
        "🔹 Aiogram + PostgreSQL\n\n"
        "👨‍💻 Original: @heylouiz\n"
        "🇺🇿 O'zbek versiyasi"
    )
    await message.answer(text)


@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    stats = await DatabaseManager.get_statistics()
    
    text = (
        "📊 <b>Statistika</b>\n\n"
        f"👥 Foydalanuvchilar: {stats['total_users']}\n"
        f"🔍 Qidiruvlar: {stats['total_searches']}\n"
        f"🎵 Yuborilgan tovushlar: {stats['total_sent']}"
    )
    await message.answer(text)


@dp.inline_query()
async def inline_query_handler(inline_query: InlineQuery):
    query = inline_query.query.strip()
    user_id = inline_query.from_user.id
    
    # Foydalanuvchini saqlash
    await DatabaseManager.get_or_create_user(
        user_id,
        inline_query.from_user.username,
        inline_query.from_user.first_name
    )
    
    # Agar qidiruv bo'sh bo'lsa - TOP tovushlarini ko'rsatish
    if not query:
        logger.info(f"TOP tovushlar - Foydalanuvchi: {user_id}")
        
        try:
            results = await get_top_us_sounds()
            
            inline_results = []
            for instant in results[:50]:  # Maksimum 50 ta
                inline_results.append(
                    InlineQueryResultVoice(
                        id=str(uuid4()),
                        title=instant['text'],
                        voice_url=instant['url']
                    )
                )
            
            if inline_results:
                await inline_query.answer(
                    inline_results,
                    cache_time=300,
                    is_personal=False
                )
            else:
                await inline_query.answer(
                    [],
                    switch_pm_text="⚠️ TOP tovushlarni yuklab bo'lmadi",
                    switch_pm_parameter="start",
                    cache_time=10
                )
        
        except Exception as e:
            logger.error(f"TOP tovushlar xatolik: {e}")
            await inline_query.answer(
                [],
                switch_pm_text="⚠️ Xatolik yuz berdi. Qayta urinib ko'ring",
                switch_pm_parameter="start",
                cache_time=5
            )
        
        return
    
    # Qidiruv mavjud bo'lsa - oddiy qidiruv
    await DatabaseManager.log_search(user_id, query)
    logger.info(f"Qidiruv: '{query}' - Foydalanuvchi: {user_id}")
    
    try:
        results = await search_instants(query)
        
        inline_results = []
        for instant in results[:50]:  # Maksimum 50 ta natija
            inline_results.append(
                InlineQueryResultVoice(
                    id=str(uuid4()),
                    title=f"🔊 {instant['text']}",
                    voice_url=instant['url']
                )
            )
        
        if inline_results:
            await inline_query.answer(
                inline_results,
                cache_time=300,
                is_personal=False
            )
            # Yuborilgan tovushlarni sanash
            await DatabaseManager.increment_sent_count(user_id)
        else:
            await inline_query.answer(
                [],
                switch_pm_text="❌ Tovush topilmadi. Boshqa so'z bilan qidiring",
                switch_pm_parameter="start",
                cache_time=10
            )
    
    except Exception as e:
        logger.error(f"Inline query xatolik: {e}")
        await inline_query.answer(
            [],
            switch_pm_text="⚠️ Xatolik yuz berdi. Qayta urinib ko'ring",
            switch_pm_parameter="start",
            cache_time=5
        )


async def main():
    await init_db()
    logger.info("🚀 Bot ishga tushdi!")
    
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
