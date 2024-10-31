from .interface import HandlerInterface
from typing import Any
from schemas.file import Thumbnails

class ThumbnailsHandler(HandlerInterface):
    """
    Handler class to handle the thumbnails section of the blog schema
    """

    def get(self, file_name: str) -> Thumbnails:
        data = {}

        for attr in Thumbnails.__annotations__.keys():
            if attr == "photo_no_bg":
                data[attr] = self.file_repository.get_image(f"{file_name}/thumbnails/{attr}.png")
            elif attr == "landscape" or attr == "square":
                data[attr] = self.file_repository.get_image(f"{file_name}/content/{attr}.png")
            else:
                data[attr] = self.file_repository.get_json(f"{file_name}/thumbnails/{attr}.json")

        return Thumbnails.model_validate(data)
    
    def save(self, file_name: str, data: Any) -> None:
        # Only save changes
        old_data = self.get(file_name)
        if self.attr_has_changed("photo_no_bg", data, old_data):    
            # Save parameters and no_bg to generated folder
            self.file_repository.save_image(f"{file_name}/thumbnails/photo_no_bg.png", data.photo_no_bg)
            self.file_repository.save_json(f"{file_name}/thumbnails/thumbnail_text.json", data.thumbnail_text.model_dump())
            self.file_repository.save_json(f"{file_name}/thumbnails/landscape_params.json", data.landscape_params.model_dump())
            self.file_repository.save_json(f"{file_name}/thumbnails/square_params.json", data.square_params.model_dump())
        
        # Save final images to main directory
        if self.attr_has_changed("landscape", data, old_data):
            self.file_repository.save_image(f"{file_name}/content/landscape.png", data.landscape)
        
        if self.attr_has_changed("square", data, old_data):
            self.file_repository.save_image(f"{file_name}/content/square.png", data.square)