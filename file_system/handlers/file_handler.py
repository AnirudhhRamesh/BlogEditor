from schemas.file import Files
from .interface import HandlerInterface
from typing import Any

class FileHandler(HandlerInterface):
    """
    Handler class to handle the files section of the blog schema
    """

    def get(self, file_name: str) -> Files:
        data = {}

        for attr in Files.__annotations__.keys():
            if attr == "audio_file":
                data[attr] = self.file_repository.get_file_ends_with(f"{file_name}", [".m4a", ".mp3"])
            elif attr == "video_file":
                data[attr] = self.file_repository.get_file_ends_with(f"{file_name}", [".mp4", ".mov"])
            elif attr == "resume_file":
                data[attr] = self.file_repository.get_file_ends_with(f"{file_name}", [".pdf"])
            elif attr == "portrait":
                data[attr] = self.file_repository.get_file_ends_with(f"{file_name}", [f"{attr}.png", f"{attr}.jpeg", f"{attr}.jpg"])
            elif attr == "photo":
                data[attr] = self.file_repository.get_file_ends_with(f"{file_name}", [f"{attr}.png", f"{attr}.jpeg", f"{attr}.jpg"])

        return Files.model_validate(data)

    def save(self, file_name: str, data: Any) -> None:
        # Normally we will never save imported files
        pass