import time
from telegram.ext import MessageHandler, ContextTypes, Application, CallbackContext, CommandHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler
from telegram import Update
import datetime
from datetime import date, datetime, time
import pytz
from telegram.ext import filters
import os
from dotenv import load_dotenv

#my modules
import notion
from Logger import Logger
from parser import ParseWebPage

SATURDAY = 5
SUNDAY = 6

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

class Config:
    token = TOKEN
    CHAT_ID = '-1001721632523'
    USER_CHAT_ID = '1290974014'



class WeekPast:
    @staticmethod
    def past_week():
        date_of_birth = date(2005, 12, 15)
        date_now = date.today()
        difference = (date_now - date_of_birth).days
        weeks_past = difference // 7
        return weeks_past


class Bot:
    def __init__(self):
        self.logger = Logger()
        self.parser = ParseWebPage()
        self.notion_connection = notion.Connection()

    async def __greet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(update.message.chat_id, "👋 Привет. Отправь сообщение, и я помещу его в твой inbox!")

    async def __send_inline(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [
            InlineKeyboardButton("✅", callback_data="True"),
            InlineKeyboardButton("❌", callback_data="False"),
                ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard) #contains last user message
        context.user_data['user_message'] = update.message.text
        await context.bot.send_message(chat_id=Config.USER_CHAT_ID, reply_markup=reply_markup, text="Отправить эту заметку в inbox?", parse_mode='MarkdownV2')


    async def __update_query(self, update: Update, context: CallbackContext):
        try:
            query = update.callback_query
            await query.answer()
            user_message = context.user_data.get('user_message')
            if not user_message:
                await query.edit_message_text("❌ Сообщение не найдено")
                return
            """вместо множества if, лучше использовать elif, т.к это оптимизация - это не switch тебе"""
            if query.data in ["True", "False"]:
                if query.data == "True":
                    available_tags = self.notion_connection.get_properties()
                    tags_keyboard = [
                        [InlineKeyboardButton(tag, callback_data=f"tag_{tag}")] for tag in available_tags
                    ]
                    tags_keyboard.append([InlineKeyboardButton("📥 Без тега", callback_data="no_tag")])
                    await query.edit_message_text(text="Выбери тег", reply_markup=InlineKeyboardMarkup(tags_keyboard))
                else:               #delete keyboard per se from query
                    await context.bot.delete_message(chat_id=Config.USER_CHAT_ID, message_id=query.message.message_id)
            #apllying tags
            elif query.data == "no_tag":
                self.notion_connection.addPage(user_message)
                await query.edit_message_text(text="Отправлено в Inbox 📥", reply_markup=None, parse_mode='MarkdownV2')

            elif query.data.startswith("tag_"):
                tag = query.data[4:]
                self.notion_connection.addPage(user_message, tag)
                await query.edit_message_text(text=f"Отправлено в Inbox 📥, с тегом {tag} ✅", reply_markup=None)


        except Exception as e:
            self.logger.logger.warning(f"Something goes wrong while updating query: {e}", exc_info=True)
            await query.edit_message_text("❌ Незвестная ошибка")



    async def __set_post_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chanel_post_update = update.channel_post

        if chanel_post_update:
            server_time = chanel_post_update.date
            timezone = pytz.timezone("Europe/Moscow")
            channel_post_time = server_time.astimezone(timezone)
            try:
                await context.bot.edit_message_text(
                    text=channel_post_time.strftime("%H:%M") + "\n" + chanel_post_update.text, chat_id=Config.CHAT_ID,
                    message_id=chanel_post_update.message_id)
            except Exception as exc:
                pass
                self.logger.logger.warning(f"Editing post error: cannot set post time because of unexpected cause", exc_info=True)


    async def __set_weekly_notif(self, context: ContextTypes.DEFAULT_TYPE):
        temp = self.parser.saveProcessed()
        if temp.getbuffer().nbytes > 0:
            await context.bot.send_photo(chat_id=Config.USER_CHAT_ID, photo=temp,
                                     caption=f"Cегодня воскресенье\\ 📅 Со дня твоего рождения, прошло {WeekPast.past_week()} недель, задумайся 🤭\\. Перегруппируй и пересмотри планы и цели в _Notion_ \\. Разбери _Inbox_ 📥",
                                     parse_mode='MarkdownV2')
            self.logger.logger.warning("Photo is successfuly sent")
        else: #✅ #❌
            pass
            self.logger.logger.warning("Buffer is empty there is no photo")


    async def __set_chanel_datetime(self, context: ContextTypes.DEFAULT_TYPE):
        try:
            await context.bot.send_message(chat_id=Config.CHAT_ID,
                                       text=str(datetime.utcnow().date().strftime("%d.%m.%y")) + "\n" + " ")
        except Exception as ex:
            pass
            self.logger.logger.warning(f"Date was not set beacause of: {ex}", exc_info=True)


    async def __get_updates(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chanel_post_update = update.channel_post

        if chanel_post_update:
            server_time = chanel_post_update.date
            timezone = pytz.timezone("Europe/Moscow")
            channel_post_time = server_time.astimezone(timezone)
            self.logger.logger.warning(f"\nMain log: {str(server_time.date)} \nSERVER TIME: {str(server_time.strftime("%H:%M"))} \nUSER PC TIME {str(channel_post_time.strftime("%H:%M"))}")

    def main(self):
        builder = Application.builder()
        builder.token(Config.token)
        application = builder.build()
        #'/start' handler
        application.add_handler(CommandHandler("start", self.__greet))
        #...
        application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, self.__send_inline))
        application.add_handler(CallbackQueryHandler(self.__update_query))
        application.add_handler(MessageHandler(filters.ChatType.CHANNEL & filters.TEXT, self.__set_post_time), group=1)
        application.add_handler(MessageHandler(filters.ChatType.CHANNEL & filters.TEXT, self.__get_updates))
        application.job_queue.run_daily(callback=self.__set_weekly_notif, time=time(hour=10, minute=1),
                                        days=(SATURDAY, SUNDAY)) #sat, sun
        application.job_queue.run_daily(callback=self.__set_chanel_datetime, time=time(hour=4, minute=1),
                                        days=(0,1,2,3,4,5,6)) #everyday :)
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    bot = Bot()
    bot.main()