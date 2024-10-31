from .interface import HandlerInterface
from typing import Any
from schemas.file import Blog

class BlogHandler(HandlerInterface):
    """
    Handler class to handle the blog section of the blog schema
    """

    def get(self, file_name: str) -> Blog:
        data = {}

        for attr in Blog.__annotations__.keys():
            # Get the latest version
            version = self.file_repository.get_json(f"{file_name}/generated/{attr}/version.json")

            if version:
                version = int(version.get("version", 0))
            else:
                version = 0

            data[attr] = self.file_repository.get_text(f"{file_name}/generated/{attr}/{attr}_v{version}.txt")

        return Blog.model_validate(data)

    def save(self, file_name: str, data: Any) -> None:
        old_data = self.get(file_name)

        for field, content in data.model_dump().items():
            # If the attribute has changed, update the version
            if self.attr_has_changed(field, data, old_data):
                print(f"Attribute {field} has changed, updating version")
                # Keep a record of the previous version
                version = self.file_repository.get_json(f"{file_name}/generated/{field}/version.json")

                if version:
                    version = int(version.get("version", 0)) + 1
                else:
                    version = 1

                # Update the version and save to generated
                self.file_repository.save_text(f"{file_name}/generated/{field}/{field}_v{version}.txt", content)
                self.file_repository.save_json(f"{file_name}/generated/{field}/version.json", {"version": version})

                # Rewrite the latest version in the root directory
                # TODO: Currently just writing text (and not json))
                self.file_repository.save_text(f"{file_name}/content/{field}.txt", content)