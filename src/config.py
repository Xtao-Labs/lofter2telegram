from typing import Optional

import dotenv

from pydantic_settings import BaseSettings, SettingsConfigDict

dotenv.load_dotenv(dotenv_path=dotenv.find_dotenv(usecwd=True))


class Settings(BaseSettings):
    def __new__(cls, *args, **kwargs):
        cls.model_rebuild()
        return super(Settings, cls).__new__(cls)  # pylint: disable=E1120


class BotConfig(Settings):
    api_id: int = 0
    api_hash: str = ""
    token: str = ""
    owner: int = 777000

    model_config = SettingsConfigDict(env_prefix="bot_")


class PushConfig(Settings):
    chat_id: int = 0
    topic_id: Optional[int] = None

    model_config = SettingsConfigDict(env_prefix="push_")


class ApplicationConfig(Settings):
    bot: BotConfig = BotConfig()
    push: PushConfig = PushConfig()
    cache_uri: str = "mem://"


ApplicationConfig.model_rebuild()
config = ApplicationConfig()
