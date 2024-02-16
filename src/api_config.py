"""API configuration module."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))


@dataclass
class APIConfig:
    username: str = os.getenv("USERNAME", "")
    token: str = os.getenv("TOKEN", "")
    base_url: str = os.getenv("BASE_URL", "https://eventsapi.chaturbate.com/events/")
    request_timeout: int = int(os.getenv("TIMEOUT", "30"))
