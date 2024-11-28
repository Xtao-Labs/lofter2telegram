from cashews import cache

from lofter.models.artwork import ArtWork


class PostCache:
    @staticmethod
    def key(post: ArtWork) -> str:
        return f"post:{post.author.auther_id}:{post.blog_id}"

    @staticmethod
    async def set(post: ArtWork):
        await cache.set(PostCache.key(post), "1", expire=60 * 60 * 24 * 7)

    @staticmethod
    async def get(post: ArtWork) -> bool:
        return await cache.get(PostCache.key(post)) is not None
