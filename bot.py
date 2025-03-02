
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.types import ContentType
from aiogram.filters import Command
import aiohttp


bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

@router.message(Command("start"))
async def send_welcome(message: types.Message):
    welcome_text = ("🤖 Assalomu alaykum! Men kiber yordamchiman.\n"
                    "Ushbu bot zararli fayllarni tekshirish uchun tashkil qilingan. Undan foydalanish uchun shubhali faylni📁 yoki havolani🖇 botga joʻnating")
    await message.reply(welcome_text)

@router.message(F.document)
async def handle_file(message: types.Message):
    document = message.document
    
    # 📝 Faylni kanalda saqlash
    await bot.send_document(CHANNEL_ID, document.file_id, caption=f"📂 {message.from_user.full_name} tomonidan yuborilgan fayl")
    
    file_path = await bot.get_file(document.file_id)
    file_url = f"https://api.telegram.org/file/bot{API_TOKEN}/{file_path.file_path}"
    
    await message.reply("🔍Faylni tekshirish biroz vaqt olishi mumkin\n⏳ Fayl tekshirilmoqda, biroz kuting...")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as resp:
            if resp.status == 200:
                file_data = await resp.read()
                async with session.post(FILE_CHECKER_API_URL, data={"file": file_data}) as api_resp:
                    result = await api_resp.json()
                    await message.reply(format_response(result, is_file=True))
            else:
                await message.reply("❌ Faylni yuklab bo‘lmadi!")

@router.message()
async def handle_url(message: types.Message):
    url = message.text.strip()
    
    # 🌐 Havolani kanalda saqlash
    await bot.send_message(CHANNEL_ID, f"🔗 {message.from_user.full_name} tomonidan yuborilgan havola:\n{url}")
    
    await message.reply("⏳ Havola tekshirilmoqda, biroz kuting...")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{URL_CHECKER_API_URL}?text={url}") as api_resp:
            result = await api_resp.json()
            await message.reply(format_response(result, is_file=False))

def format_response(data, is_file):
    if data.get("status") == "success":
        vt_link = data.get("virus_total_link", "Noma‘lum")
        total = data.get("total_engines", "?")
        malicious = data.get("malicious", "?")
        
        if int(malicious) > 0:
            verdict = "⛔️ Ogoh bo'ling‼️ Havola yoki dastur zararli fayl ekanligi aniqlandi! \n\nIzoh: Agarda havola zararli deb topilgan bo'lsa uni ocha ko'rmang! \n\n Agarda sizning yuborgan faylingiz zararli deb topilgan bo'lsa uni yuklay ko'rmang. Allaqachon yuklab olgan bo'lsangiz, quyidagi video qo'llanmadan foydalanib o'chirishingiz mumkin.\n https://t.me/cyber_csec_uz/1355 "
        else:
            verdict = "✅ Zararli kodlar aniqlanmadi."
        
        item = "Fayl" if is_file else "Havola"
        
        return (f"🔍 {item} natijalari:\n"
                f"❌ Xavfli: {malicious}\n"
                f"{verdict}")
    else:
        return "❌ Tekshiruvda xatolik yuz berdi!"

async def main():
    logging.basicConfig(level=logging.INFO)
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
