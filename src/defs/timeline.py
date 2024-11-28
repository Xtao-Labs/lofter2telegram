import asyncio
import contextlib
from typing import Optional

from cashews import cache

from pyrogram import Client
from pyrogram.types import InputMediaPhoto, InputMediaAnimation, InputMediaVideo
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait, WebpageCurlFailed, MediaEmpty

from lofter.client.lofter import LofterClient
from lofter.models.artwork import ArtWork, ArtWorkImage, ImageType

from src.config import config
from src.defs.cache import PostCache
from src.utils.log import logs


def flood_wait():
    def decorator(function):
        async def wrapper(*args, **kwargs):
            try:
                return await function(*args, **kwargs)
            except (WebpageCurlFailed, MediaEmpty):
                try:
                    url = args[1].url
                except IndexError:
                    url = ""
                logs.warning(f"遇到 WebpageCurlFailed / MediaEmpty，跳过此贴！ url[%s]", url)
            except FloodWait as e:
                logs.warning(f"遇到 FloodWait，等待 {e.value} 秒后重试！")
                await asyncio.sleep(e.value + 1)
                return await wrapper(*args, **kwargs)
            except Exception as e:
                raise e

        return wrapper

    return decorator


class Timeline:
    def __init__(self, bot: Client):
        self.bot = bot
        self.client = LofterClient()
        self.queue = asyncio.Queue()
        self.keys = []

    async def push_one(self, tag: str):
        logs.info("Timeline push task req tag %s", tag)
        posts = await self.client.get_web_tag_posts(tag, page_size=30)
        posts.reverse()
        for post in posts:
            if not post.images:
                # TODO: 发送长文
                continue
            key = PostCache.key(post)
            if await PostCache.get(post) or key in self.keys:
                continue
            self.keys.append(key)
            await self.queue.put(post)

    async def push(self):
        logs.info("开始检查更新")
        tags = await cache.get("sub.tags")
        if not tags:
            return
        for tag in tags:
            await self.push_one(tag)
        logs.info("检查更新完成")
        logs.info("Timeline pull task remain %s", self.queue.qsize())

    async def pull(self):
        logs.info("Timeline pull task started")
        while True:
            try:
                post = await asyncio.wait_for(self.queue.get(), 10)
                if not post:
                    raise asyncio.TimeoutError
            except asyncio.TimeoutError:
                await asyncio.sleep(.5)
                continue

            try:
                if len(post.images) == 1:
                    await self.send_single_to_user(post)
                else:
                    await self.send_to_user(post)
                await PostCache.set(post)
            except Exception as exc:
                logs.warning("Timeline pull task send posts failed exc[%s]", str(exc), exc_info=True)
            finally:
                key = PostCache.key(post)
                with contextlib.suppress(ValueError):
                    self.keys.pop(self.keys.index(key))
            if self.queue.qsize() % 10 == 0:
                logs.info("Timeline pull task remain %s", self.queue.qsize())

        logs.info("Timeline pull task stopped")

    @flood_wait()
    async def send_single_to_user(self, post: ArtWork):
        bot = self.bot
        text = post.format_text()
        image = post.images[0]
        func = bot.send_document
        url = image.url
        if image.type == ImageType.STATIC:
            func = bot.send_photo
            url = image.format_url
        elif image.type == ImageType.GIF:
            func = bot.send_animation
        elif image.type == ImageType.GIF:
            func = bot.send_video
        return await func(
                config.push.chat_id,
                url,
                caption=text,
                reply_to_message_id=config.push.topic_id,
                parse_mode=ParseMode.HTML,
            )

    @staticmethod
    def get_media_input(image: ArtWorkImage, text: Optional[str] = None):
        if image.type == ImageType.STATIC:
            return InputMediaPhoto(media=image.format_url, caption=text, parse_mode=ParseMode.HTML)
        elif image.type == ImageType.GIF:
            return InputMediaAnimation(media=image.url, caption=text, parse_mode=ParseMode.HTML)
        elif image.type == ImageType.VIDEO:
            return InputMediaVideo(media=image.url, caption=text, parse_mode=ParseMode.HTML)

    @flood_wait()
    async def send_to_user(self, post: ArtWork):
        bot = self.bot
        text = post.format_text()
        data = []
        images = post.images[:10]  # todo: 发送超过十张图片
        for idx, img in enumerate(images):
            if i := self.get_media_input(img, text if (idx == len(images) - 1) else None):
                data.append(i)
        return await bot.send_media_group(
            config.push.chat_id,
            data,
            reply_to_message_id=config.push.topic_id,
            parse_mode=ParseMode.HTML,
        )
