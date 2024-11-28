import asyncio
from asyncio import Lock

from persica.factory.component import BaseComponent
from pyrogram import filters
from pyrogram.types import Message

from src.config import config
from src.core.bot import TelegramBot
from src.core.scheduler import TimeScheduler
from src.defs.timeline import Timeline

_lock = Lock()


class UpdateBotPlugin(BaseComponent):
    def __init__(self, telegram_bot: TelegramBot, scheduler: TimeScheduler):
        self.timeline = Timeline(telegram_bot.bot)
        self.consumer_task = telegram_bot.bot.loop.create_task(self.timeline.pull())

        @telegram_bot.bot.on_message(
            filters=filters.command("check_update") & filters.user(config.bot.owner)
        )
        async def _update_all(_, message: "Message"):
            if _lock.locked():
                await message.reply("正在检查更新，请稍后再试！")
                return
            async with _lock:
                msg = await message.reply("开始检查更新！")
                await self.timeline.push()
                await msg.edit("检查更新完毕！")

        @scheduler.scheduler.scheduled_job(
            "cron", hour="*", minute="*/10", second="0", id="update_all"
        )
        async def update_all_10_minutes():
            if _lock.locked():
                return
            async with _lock:
                await self.timeline.push()
