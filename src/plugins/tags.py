from typing import List

from cashews import cache

from persica.factory.component import BaseComponent
from pyrogram import filters
from pyrogram.types import Message

from src.config import config
from src.core.bot import TelegramBot


class TagsBotPlugin(BaseComponent):
    def __init__(self, telegram_bot: TelegramBot):
        @telegram_bot.bot.on_message(
            filters=filters.command("add_tag") & filters.user(config.bot.owner)
        )
        async def __add_tag(_, message: Message):
            await self.add_tag(message)

        @telegram_bot.bot.on_message(
            filters=filters.command("remove_tag") & filters.user(config.bot.owner)
        )
        async def __remove_tag(_, message: Message):
            await self.remove_tag(message)

    @staticmethod
    async def get_tags() -> List[str]:
        return await cache.get("sub.tags") or []

    @staticmethod
    async def set_tags(tags: List[str]) -> None:
        await cache.set("sub.tags", tags)

    async def _add_tag(self, tag: str):
        tags = await self.get_tags()
        if tag in tags:
            return False
        tags.append(tag)
        await self.set_tags(tags)
        return True

    async def _remove_tag(self, tag: str):
        tags = await self.get_tags()
        if tag in tags:
            tags.remove(tag)
            await self.set_tags(tags)
            return True
        return False

    async def add_tag(self, message: Message):
        if len(message.command) < 1:
            return await message.reply("请发送 tag", quote=True)
        tags = message.command[1:]
        result = False
        for tag in tags:
            result = await self._add_tag(tag)
        if result:
            return await message.reply("添加 tag 成功", quote=True)
        return await message.reply("添加 tag 失败，可能已经存在", quote=True)

    async def remove_tag(self, message: Message):
        if len(message.command) < 1:
            return await message.reply("请发送 tag", quote=True)
        tags = message.command[1:]
        result = False
        for tag in tags:
            result = await self._remove_tag(tag)
        if result:
            return await message.reply("删除 tag 成功", quote=True)
        return await message.reply("删除 tag 失败，可能本来就不存在", quote=True)
