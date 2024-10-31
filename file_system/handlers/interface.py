from abc import ABC, abstractmethod
from typing import Any
from errors import GuestNotFoundError
from file_system.file_repository import FileRepository

class HandlerInterface(ABC):
    """
    Interface class for the handlers
    """

    def __init__(self, file_repository: FileRepository):
        """
        Initialize the handler
        """
        self.file_repository = file_repository

    @abstractmethod
    def get(self, blog_name: str) -> Any:
        """
        Get the data from the given blog name
        """
        pass

    @abstractmethod
    def save(self, blog_name: str, data: Any) -> None:
        """
        Save the data to the given blog name
        """
        pass

    def has_changed(self, new_data: Any, old_data: Any) -> bool:
        """
        Check if the data has changed
        """
        return any(self.attr_has_changed(attr, new_data, old_data) for attr in new_data.__annotations__.keys())

    def attr_has_changed(self, attr: str, new_data: Any, old_data: Any) -> bool:
        """
        Check if a specific attribute of the data has changed
        """
        return getattr(new_data, attr) != getattr(old_data, attr)

    # @abstractmethod
    # def reset(self, blog_name: str) -> None:
    #     pass