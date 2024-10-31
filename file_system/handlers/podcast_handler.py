from .interface import HandlerInterface
from typing import Any
from schemas.file import Podcast

class PodcastHandler(HandlerInterface):
    """
    Handler class to handle the podcast section of the blog schema (WIP)
    """

    def save(self, file_name: str, data: Any) -> None:
        raise NotImplementedError("PodcastHandler not implemented")

    def get(self, file_name: str) -> Podcast:
        raise NotImplementedError("PodcastHandler not implemented")