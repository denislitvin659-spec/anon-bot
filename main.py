import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandObject
from aiohttp import web

# --- НАСТРОЙКИ ---
API_TOKEN = "8268566712:AAER3fxK8nI7SyZNADKp_ClsPL5u1_-YAs8"
DB_FILE = "users_data.json"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- ЛОГИКА БАЗЫ ДАННЫХ ---
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        active_chats = json.load(f)
else:
    active_chats = {}

def save_db():
    with open(DB_FILE, "w") as f:
        json.dump(active_chats, f)

# --- ФЕЙКОВЫЙ ВЕБ-СЕРВЕР ДЛЯ RENDER ---
async def handle(request):
    return web.Response(text="Bot is alive!")

async def start_web():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    # Render дает порт в переменной окружения PORT, если ее нет — ставим 10000
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# --- ОБРАБОТЧИКИ КОМАНД ---
@dp.message(Command("start"))
async def start_handler(message: types.Message, command: CommandObject):
    args = command.args
    user_id = str(message.from_user.id)
    
    if args:
        active_chats[user_id] = args
        save_db()
        await message.answer("🤫 Напиши сообщение, и я его перешлю анонимно!")
    else:
        bot_info = await bot.get_me()
        link = f"https://t.me/{bot_info.username}?start={user_id}"
        await message.answer(f"🔗 Твоя ссылка для анонимных сообщений:\n`{link}`", parse_mode="Markdown")

@dp.message()
async def forward_handler(message: types.Message):
    user_id = str(message.from_user.id)
    
    if user_id in active_chats:
        target_id = active_chats[user_id]
        try:
            await bot.send_message(target_id, f"✉️ **Анонимно:**\n\n{message.text}", parse_mode="Markdown")
            await message.answer("🚀 Отправлено!")
            del active_chats[user_id]
            save_db()
        except:
            await message.answer("❌ Ошибка отправки. Возможно, пользователь заблокировал бота.")
    else:
        await message.answer("Перейди по ссылке пользователя, чтобы написать ему.")

# --- ЗАПУСК ---
async def main():
    # Запускаем фейковый веб-сервер
    await start_web()
    print("--- БОТ ЗАПУЩЕН НА СЕРВЕРЕ ---")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
 
