from typing import Dict, Type
from .file_repository import FileRepository
from .handlers.file_handler import FileHandler
from .handlers.metadata_handler import MetadataHandler
from .handlers.thumbnails_handler import ThumbnailsHandler
from .handlers.blog_handler import BlogHandler
from .handlers.podcast_handler import PodcastHandler
from schemas.file import File
from errors import GuestNotFoundError

class FileHelper:
    """
    Helper class to handle the business logic of the (Zoom) file system
    """

    def __init__(self, directory: str):
        """
        Initialize the file helper
        """
        self.file_repository = FileRepository(directory)
        self.handlers: Dict[str, FileHandler] = {
            'files': FileHandler(self.file_repository),
            'metadata': MetadataHandler(self.file_repository),
            'thumbnails': ThumbnailsHandler(self.file_repository),
            'blog': BlogHandler(self.file_repository),
        }

    def list_files(self):
        """
        List all the files in the directory
        """
        return self.file_repository.list_files()

    def get(self, blog_name: str) -> File:
        """
        Get the folder named with the blog_name from the Zoom directory
        """

        # Check if the blog exists
        if blog_name not in self.list_files():
            raise GuestNotFoundError(f"Blog '{blog_name}' not found")

        data = {'name': blog_name}

        # Get each section of the blog
        for section, handler in self.handlers.items():
            data[section] = handler.get(blog_name)

        return File(**data)

    def save(self, blog: File) -> None:
        """
        Save the blog to the Zoom directory
        """
        # Save each section using its specific handler, only if the section has changed
        for section, handler in self.handlers.items():
            if handler.has_changed(blog, self.get(blog.name)):
                handler.save(blog.name, getattr(blog, section))

    def reset(self, blog_name: str):
        """
        Reset the blog by deleting all its files
        """
        for handler in self.handlers.values():
            handler.reset(blog_name)
