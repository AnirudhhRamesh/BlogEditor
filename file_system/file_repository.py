import os
import json

from schemas.file import Blog

class FileRepository:
    """
    Class to handle the Zoom file system
    """

    def __init__(self, directory: str):
        """
        Initialize the file repository
        """
        self.directory = directory

    def list_files(self):
        """
        List all the files in the directory
        """
        files = os.listdir(self.directory)
        # Filter out hidden files/directories that start with .
        visible_files = [f for f in files if not f.startswith('.')]
        return sorted(visible_files)

    # Handle retrieving user-uploaded files
    def get_file_ends_with(self, file_path: str, extensions: list[str]):
        """
        Get the first file in the given file_path that ends with the given extension
        """
        files = []

        for extension in extensions:
            files.extend([f for f in os.listdir(f"{self.directory}/{file_path}") if f.endswith(extension)])

        if len(files) == 0:
            return None
        else:
            return f"{self.directory}/{file_path}/{files[0]}"

    # Handle JSON files
    def get_json(self, file_path: str):
        """
        Get the JSON data from the given file path
        """
        try:
            with open(f"{self.directory}/{file_path}", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return None

    def save_json(self, file_path: str, data: dict):
        """
        Save the JSON data to the given file path
        """
        self._ensure_directory_exists(file_path)
        with open(f"{self.directory}/{file_path}", "w") as f:
            json.dump(data, f)

    # Handle image files
    def get_image(self, file_path: str):
        """
        Returns the bytes of the image
        """
        try:
            with open(f"{self.directory}/{file_path}", "rb") as f:
                return f.read()
        except FileNotFoundError:
            return None

    def save_image(self, file_path: str, data: bytes):
        """
        Save the image data to the given file path
        """
        self._ensure_directory_exists(file_path)
        with open(f"{self.directory}/{file_path}", "wb") as f:
            f.write(data)

    # Handle markdown files
    def get_text(self, file_path: str):
        """
        Get the text from the given file path
        """
        try:
            with open(f"{self.directory}/{file_path}", "r") as f:
                return f.read()
        except FileNotFoundError:
            return None
    
    def save_text(self, file_path: str, data: str): 
        """
        Save the text to the given file path
        """
        self._ensure_directory_exists(file_path)
        with open(f"{self.directory}/{file_path}", "w") as f:
            f.write(data)

    def _ensure_directory_exists(self, file_path: str):
        """
        Helper method to create directory structure if it doesn't exist
        """
        directory = os.path.dirname(f"{self.directory}/{file_path}")
        os.makedirs(directory, exist_ok=True)