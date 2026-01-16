import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import json
import os
from flask import Flask
from threading import Thread

# Flask web server (Render uchun)
app = Flask('')

@app.route('/')
def home():
    return "Bot ishlayapti! ✅"

@app.route('/health')
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)

# Bot sozlamalari
BOT_TOKEN = "8121611417:AAHNLY6WrAvtugzNlCYDm4FUcUyjDSW45Ac"  # @BotFather dan olingan token
ADMIN_ID = 6965587290 # Sizning Telegram ID raqamingiz
CHANNEL_USERNAME = "@kinochibillo"  # Kanalingiz username (@ bilan)
CHANNEL_ID = -1003346732387  # Kanalingiz ID raqami
BANNER_FILE_ID = "AgACAgIAAxkBAAMzaWj1mWZEaW1BTKyZeoH9m6cZ0BcAAiIMaxstLkhLzNObqwHBbe4BAAMCAAN5AAM4BA"  # Banner rasm file_id (birinchi yuborilgandan keyin olinadi)

# Ma'lumotlar fayllari
DATA_FILE = "movies.json"
STATS_FILE = "stats.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_stats(stats):
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

# Bot va Dispatcher
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# FSM states
class AddMovie(StatesGroup):
    waiting_for_code = State()
    waiting_for_file = State()

class DeleteMovie(StatesGroup):
    waiting_for_code = State()

class SetBanner(StatesGroup):
    waiting_for_photo = State()

# Ma'lumotlar bazasi
movies_db = load_data()
stats_db = load_stats()

# Menu tugmalari
def get_main_menu(is_admin=False):
    keyboard = [
        [KeyboardButton(text="🎬 Kino olish")],
        [KeyboardButton(text="🔝 Top kinolar"), KeyboardButton(text="📊 Statistika")],
        [KeyboardButton(text="ℹ️ Yordam")]
    ]
    
    if is_admin:
        keyboard.append([KeyboardButton(text="👮 Admin Panel")])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# Obunani tekshirish
async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logging.error(f"Obunani tekshirishda xatolik: {e}")
        return False

# /start komandasi
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    
    # Obunani tekshirish
    if not await check_subscription(user_id) and user_id != ADMIN_ID:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub")]
        ])
        
        await message.answer(
            "❌ <b>Botdan foydalanish uchun kanalimizga obuna bo'ling!</b>\n\n"
            f"👉 Kanal: {CHANNEL_USERNAME}\n\n"
            "Obuna bo'lgach, '✅ Obunani tekshirish' tugmasini bosing.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return
    
    # Banner yuborish (agar mavjud bo'lsa)
    if BANNER_FILE_ID and BANNER_FILE_ID != "AgACAgIAAxkBAAI...":
        try:
            await message.answer_photo(
                photo=BANNER_FILE_ID,
                caption="🎬Kinochi Billo Botga xush kelibsiz!"
            )
        except:
            pass
    
    # Asosiy xabar
    is_admin = user_id == ADMIN_ID
    await message.answer(
        "🎬 <b>Kinochi Billo</b>ga xush kelibsiz!\n\n"
        "📝 Kino kodini yozing va kinoni oling\n"
        "Masalan: <code>001</code>\n\n"
        "📋 Menyu tugmalaridan foydalaning 👇",
        reply_markup=get_main_menu(is_admin),
        parse_mode="HTML"
    )

# Obunani tekshirish callback
@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    if await check_subscription(user_id) or user_id == ADMIN_ID:
        is_admin = user_id == ADMIN_ID
        
        # Banner yuborish
        if BANNER_FILE_ID and BANNER_FILE_ID != "AgACAgIAAxkBAAI...":
            try:
                await callback.message.answer_photo(
                    photo=BANNER_FILE_ID,
                    caption="🎬 <b>Kino Bot</b>ga xush kelibsiz!"
                )
            except:
                pass
        
        await callback.message.answer(
            "✅ <b>Obuna tasdiqlandi!</b>\n\n"
            "🎬 Endi botdan foydalanishingiz mumkin!\n"
            "📝 Kino kodini yozing va kinoni oling\n\n"
            "📋 Menyu tugmalaridan foydalaning 👇",
            reply_markup=get_main_menu(is_admin),
            parse_mode="HTML"
        )
        await callback.message.delete()
    else:
        await callback.answer(
            "❌ Siz hali obuna bo'lmadingiz!\n"
            "Iltimos, avval kanalga obuna bo'ling.",
            show_alert=True
        )

# Kino olish tugmasi
@dp.message(F.text == "🎬 Kino olish")
async def movie_request(message: types.Message):
    user_id = message.from_user.id
    
    if not await check_subscription(user_id) and user_id != ADMIN_ID:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub")]
        ])
        
        await message.answer(
            "❌ Botdan foydalanish uchun kanalimizga obuna bo'ling!",
            reply_markup=keyboard
        )
        return
    
    await message.answer(
        "📝 Kino kodini yozing\n"
        "Masalan: <code>001</code>",
        parse_mode="HTML"
    )

# Top kinolar
@dp.message(Command("top"))
@dp.message(F.text == "🔝 Top kinolar")
async def cmd_top(message: types.Message):
    user_id = message.from_user.id
    
    if not await check_subscription(user_id) and user_id != ADMIN_ID:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub")]
        ])
        
        await message.answer(
            "❌ Botdan foydalanish uchun kanalimizga obuna bo'ling!",
            reply_markup=keyboard
        )
        return
    
    if not stats_db:
        await message.answer("📭 Hozircha statistika yo'q!")
        return
    
    # Top 5 ni saralash
    sorted_movies = sorted(stats_db.items(), key=lambda x: x[1], reverse=True)[:5]
    
    text = "🔝 <b>Eng ko'p ko'rilgan kinolar:</b>\n\n"
    
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for i, (code, views) in enumerate(sorted_movies):
        text += f"{medals[i]} Kod: <code>{code}</code> - {views} marta ko'rilgan\n"
    
    await message.answer(text, parse_mode="HTML")

# Statistika
@dp.message(F.text == "📊 Statistika")
async def show_stats(message: types.Message):
    user_id = message.from_user.id
    
    if not await check_subscription(user_id) and user_id != ADMIN_ID:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub")]
        ])
        
        await message.answer(
            "❌ Botdan foydalanish uchun kanalimizga obuna bo'ling!",
            reply_markup=keyboard
        )
        return
    
    total_movies = len(movies_db)
    total_views = sum(stats_db.values())
    
    text = (
        "📊 <b>Statistika:</b>\n\n"
        f"🎬 Jami kinolar: {total_movies}\n"
        f"👁 Jami ko'rishlar: {total_views}"
    )
    
    await message.answer(text, parse_mode="HTML")

# Yordam
@dp.message(F.text == "ℹ️ Yordam")
async def show_help(message: types.Message):
    user_id = message.from_user.id
    
    if not await check_subscription(user_id) and user_id != ADMIN_ID:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub")]
        ])
        
        await message.answer(
            "❌ Botdan foydalanish uchun kanalimizga obuna bo'ling!",
            reply_markup=keyboard
        )
        return
    
    text = (
        "ℹ️ <b>Yordam:</b>\n\n"
        "🎬 <b>Kino olish:</b> Kino kodini yozing (masalan: 001)\n"
        "🔝 <b>Top kinolar:</b> Eng ko'p ko'rilgan kinolarni ko'ring\n"
        "📊 <b>Statistika:</b> Bot statistikasini ko'ring\n\n"
        "❓ Savollar bo'lsa, admin bilan bog'laning."
    )
    
    await message.answer(text, parse_mode="HTML")

# Admin panel
@dp.message(Command("admin"))
@dp.message(F.text == "👮 Admin Panel")
async def cmd_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Sizda admin huquqi yo'q!")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Kino qo'shish", callback_data="add_movie")],
        [InlineKeyboardButton(text="🗑 Kino o'chirish", callback_data="delete_movie")],
        [InlineKeyboardButton(text="📋 Barcha kinolar", callback_data="list_movies")],
        [InlineKeyboardButton(text="🖼 Banner o'rnatish", callback_data="set_banner")]
    ])
    
    await message.answer(
        "👮 <b>Admin Panel</b>\n\n"
        "Quyidagi tugmalardan birini tanlang:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# Banner o'rnatish
@dp.callback_query(F.data == "set_banner")
async def set_banner_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🖼 <b>Banner o'rnatish</b>\n\n"
        "Banner rasmini yuboring:",
        parse_mode="HTML"
    )
    await state.set_state(SetBanner.waiting_for_photo)
    await callback.answer()

@dp.message(SetBanner.waiting_for_photo, F.photo)
async def set_banner_photo(message: types.Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    
    await message.answer(
        f"✅ Banner o'rnatildi!\n\n"
        f"📝 File ID: <code>{file_id}</code>\n\n"
        f"Ushbu file_id ni kodingizda BANNER_FILE_ID ga qo'ying.",
        parse_mode="HTML"
    )
    await state.clear()

# Kino qo'shish
@dp.callback_query(F.data == "add_movie")
async def add_movie_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "➕ <b>Kino qo'shish</b>\n\n"
        "Kino kodini yozing (masalan: 001):",
        parse_mode="HTML"
    )
    await state.set_state(AddMovie.waiting_for_code)
    await callback.answer()

@dp.message(AddMovie.waiting_for_code)
async def add_movie_code(message: types.Message, state: FSMContext):
    code = message.text.strip()
    
    if code in movies_db:
        await message.answer(f"⚠️ <code>{code}</code> kodi allaqachon mavjud!", parse_mode="HTML")
        return
    
    await state.update_data(code=code)
    await message.answer(
        f"✅ Kod saqlandi: <code>{code}</code>\n\n"
        "Endi kino faylini yuboring:",
        parse_mode="HTML"
    )
    await state.set_state(AddMovie.waiting_for_file)

@dp.message(AddMovie.waiting_for_file, F.video | F.document)
async def add_movie_file(message: types.Message, state: FSMContext):
    data = await state.get_data()
    code = data['code']
    
    if message.video:
        file_id = message.video.file_id
        file_type = "video"
    else:
        file_id = message.document.file_id
        file_type = "document"
    
    movies_db[code] = {
        "file_id": file_id,
        "file_type": file_type
    }
    save_data(movies_db)
    
    # Statistika uchun 0 qo'shish
    if code not in stats_db:
        stats_db[code] = 0
        save_stats(stats_db)
    
    await message.answer(
        f"✅ Kino muvaffaqiyatli qo'shildi!\n\n"
        f"📝 Kod: <code>{code}</code>\n"
        f"📁 Fayl turi: {file_type}",
        parse_mode="HTML"
    )
    await state.clear()

# Kino o'chirish
@dp.callback_query(F.data == "delete_movie")
async def delete_movie_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    
    if not movies_db:
        await callback.message.edit_text("📭 Hozircha kinolar yo'q!")
        await callback.answer()
        return
    
    await callback.message.edit_text(
        "🗑 <b>Kino o'chirish</b>\n\n"
        "O'chirmoqchi bo'lgan kino kodini yozing:",
        parse_mode="HTML"
    )
    await state.set_state(DeleteMovie.waiting_for_code)
    await callback.answer()

@dp.message(DeleteMovie.waiting_for_code)
async def delete_movie_code(message: types.Message, state: FSMContext):
    code = message.text.strip()
    
    if code not in movies_db:
        await message.answer(f"❌ <code>{code}</code> kodi topilmadi!", parse_mode="HTML")
        return
    
    del movies_db[code]
    save_data(movies_db)
    
    if code in stats_db:
        del stats_db[code]
        save_stats(stats_db)
    
    await message.answer(
        f"✅ Kino o'chirildi!\n\n"
        f"📝 Kod: <code>{code}</code>",
        parse_mode="HTML"
    )
    await state.clear()

# Barcha kinolarni ko'rish
@dp.callback_query(F.data == "list_movies")
async def list_movies(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    
    if not movies_db:
        await callback.message.edit_text("📭 Hozircha kinolar yo'q!")
        await callback.answer()
        return
    
    text = "📋 <b>Barcha kinolar:</b>\n\n"
    for code in sorted(movies_db.keys()):
        views = stats_db.get(code, 0)
        text += f"📝 <code>{code}</code> - {views} ko'rilgan\n"
    
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()

# Foydalanuvchi kino kodini yozganda
@dp.message(F.text)
async def get_movie(message: types.Message):
    user_id = message.from_user.id
    
    # Obunani tekshirish
    if not await check_subscription(user_id) and user_id != ADMIN_ID:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub")]
        ])
        
        await message.answer(
            "❌ Botdan foydalanish uchun kanalimizga obuna bo'ling!",
            reply_markup=keyboard
        )
        return
    
    code = message.text.strip()
    
    if code not in movies_db:
        await message.answer(
            "❌ Bunday kod topilmadi!\n\n"
            "To'g'ri kod yozing (masalan: <code>001</code>)",
            parse_mode="HTML"
        )
        return
    
    movie = movies_db[code]
    
    # Statistikani yangilash
    if code not in stats_db:
        stats_db[code] = 0
    stats_db[code] += 1
    save_stats(stats_db)
    
    try:
        if movie['file_type'] == "video":
            await message.answer_video(
                movie['file_id'],
                caption=f"🎬 Kod: <code>{code}</code>\n👁 Ko'rilgan: {stats_db[code]} marta",
                parse_mode="HTML"
            )
        else:
            await message.answer_document(
                movie['file_id'],
                caption=f"🎬 Kod: <code>{code}</code>\n👁 Ko'rilgan: {stats_db[code]} marta",
                parse_mode="HTML"
            )
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await message.answer("❌ Kino yuborishda xatolik yuz berdi!")

# Botni ishga tushirish
async def main():
    keep_alive()  # Flask serverni ishga tushirish
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    print("🤖 Bot ishga tushdi...")
    asyncio.run(main())
