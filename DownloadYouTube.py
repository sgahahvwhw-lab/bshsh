import re
import httpx
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
)

API_ID = "30170218"
API_HASH = "c6be563a4ed1ce81591ef5e6d637648a"
API_TOKEN = "8621194105:AAGpLgU3oQp40t88gqGlteMmsUzCq0nylV0"

app = Client("DownloadYouTube", api_id=API_ID, api_hash=API_HASH, bot_token=API_TOKEN)
api_key = "ed6157259537158fd05a398400edd20"

user_queries = {}

def extract_chat_and_msg_id(link):
    match = re.match(r"https://t.me/([^/]+)/(\d+)", link)
    if match:
        return match.group(1), int(match.group(2))
    return None, None

async def fetch_and_send_file(message: Message, query: str, filetype: str):
    api_url = f"http://46.250.243.74:5000/{filetype}/{query.replace(' ', '_')}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, params={"api_key": api_key}, timeout=None)
        if response.status_code != 200:
            return await message.edit("فشل تحميل الملف من الخادم.")
        data = response.json()
        if data.get("status") != "ok" or not data.get("link"):
            return await message.edit("لم يتم العثور على الرابط الصحيح.")
        tg_link = data["link"]
        title = data.get("title", "عنوان غير معروف")
        duration = data.get("duration", 0)
        chat_username, msg_id = extract_chat_and_msg_id(tg_link)
        if not chat_username or not msg_id:
            return await message.edit("رابط تيليجرام غير صالح.")
        tg_msg = await app.get_messages(chat_username, msg_id)
        if filetype == "m4a" and tg_msg.audio:
            file_id = tg_msg.audio.file_id
            caption = f"🎵 الاسم: {title[:40]}\n👤 بواسطة: {message.from_user.mention if message.from_user else 'مجهول'}"
            await message.reply_audio(file_id, caption=caption, title=title, duration=duration)
        elif filetype == "mp4" and tg_msg.video:
            file_id = tg_msg.video.file_id
            caption = f"🎬 الاسم: {title[:40]}\n👤 بواسطة: {message.from_user.mention if message.from_user else 'مجهول'}"
            await message.reply_video(file_id, caption=caption, duration=duration)
        else:
            return await message.edit("⚠️ لم يتم العثور على الملف المطلوب.")
    except Exception as e:
        await message.edit(f"🚫 حدث خطأ:\n`{e}`")

@app.on_message(filters.text & (filters.private | filters.group))
async def handle_message(client, message: Message):
    text = message.text.strip()
    if text.lower() in ["/start", "start", "ابدأ"]:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👤 مطور البوت", url="https://t.me/rr8r9")]
        ])
        return await message.reply(
            "أهلاً بك في بوت تحميل الصوت والفيديو من YouTube .\n"
            "أرسل رابط أو اسم الفيديو لبدء عملية التحميل .\n\n"
            "⚡️ سريع - مجاني - بدون إعلانات",
            reply_markup=keyboard
        )

    user_queries[message.from_user.id] = text
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("تحميل فيديو", callback_data="download_mp4"),
            InlineKeyboardButton("تحميل صوت", callback_data="download_m4a")
        ],
        [InlineKeyboardButton("👤 مطور البوت", url="https://t.me/rr8r9")]
    ])
    await message.reply("اختر طريقة التحميل:", reply_markup=keyboard)

@app.on_callback_query()
async def handle_callback(client, callback_query: CallbackQuery):
    query = user_queries.get(callback_query.from_user.id)
    if not query:
        return await callback_query.answer("لم يتم العثور على طلب التحميل.", show_alert=True)

    await callback_query.answer()
    try:
        await callback_query.message.delete()
    except:
        pass

    loading_msg = await callback_query.message.reply("جارٍ التحميل ...")
    filetype = "mp4" if callback_query.data == "download_mp4" else "m4a"
    try:
        await fetch_and_send_file(loading_msg, query, filetype)
    finally:
        try:
            await loading_msg.delete()
        except:
            pass

if __name__ == "__main__":
    app.run()