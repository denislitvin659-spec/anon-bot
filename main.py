import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandObject
 
API_TOKEN = "8268566712:AAER3fxK8nI7SyZNADKp_ClsPL5u1_-YAs8"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Временная база тех, кому мы сейчас пишем анонимно {кто_пишет: кому_придет}
active_chats = {}

@dp.message(Command("start"))
async def start_handler(message: types.Message, command: CommandObject):
    args = command.args # Это то, что идет после ?start=
    
    if args:
        # Если человек перешел по ссылке
        target_id = args
        active_chats[message.from_user.id] = target_id
        await message.answer("🤫 Напиши своё анонимное сообщение ниже, и я его перешлю!")
    else:
        # Если человек просто зашел в бот
        bot_info = await bot.get_me()
        link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
        
        text = (
            f"👋 Привет! Это бот анонимных сообщений.\n\n"
            f"🔗 Твоя личная ссылка:\n`{link}`\n\n"
            f"Размести её в описании профиля или сторис. Люди смогут писать тебе анонимно по ней!"
        )
        await message.answer(text, parse_mode="Markdown")

@dp.message()
async def forward_handler(message: types.Message):
    user_id = message.from_user.id
    
    if user_id in active_chats:
        target_id = active_chats[user_id]
        try:
            # Отправляем сообщение владельцу ссылки
            await bot.send_message(
                target_id, 
                f"✉️ **Новое анонимное сообщение:**\n\n{message.text}", 
                parse_mode="Markdown"
            )
            await message.answer("🚀 Сообщение отправлено!")
            # Очищаем чат, чтобы следующее сообщение не ушло тому же человеку случайно
            del active_chats[user_id]
        except Exception:
            await message.answer("❌ Не удалось отправить. Возможно, пользователь заблокировал бота.")
    else:
        await message.answer("Чтобы отправить анонимное сообщение, перейдите по ссылке пользователя.")

async def main():
    print("--- БОТ НА ССЫЛКАХ ЗАПУЩЕН ---")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
