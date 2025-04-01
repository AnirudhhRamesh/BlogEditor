from .interface import HandlerInterface
from schemas.file import Metadata

class MetadataHandler(HandlerInterface):
    """
    Handler class to handle the metadata section of the blog schema
    """

    def get(self, file_name: str) -> Metadata:
        data = {}

        for attr in Metadata.__annotations__.keys():
            data[attr] = self.file_repository.get_json(f"{file_name}/metadata/{attr}.json")

        return Metadata.model_validate(data)
    
    def save(self, file_name: str, new_data: Metadata) -> None:
        old_data = self.get(file_name)

        # Save each attribute as a JSON file
        for attr in Metadata.__annotations__.keys():
            # Get the attribute data
            attr_data = getattr(new_data, attr)

            # Save the attribute data if it exists and has changed
            if attr_data is not None and self.attr_has_changed(attr, new_data, old_data):
                print(f"{attr} has changed for {file_name}, saving it!")
                self.file_repository.save_json(f"{file_name}/metadata/{attr}.json", attr_data.model_dump())
                
                # TODO: This is bad and hard-coded
                if attr == "transcript":
                    self.file_repository.save_text(f"{file_name}/metadata/transcript.txt", attr_data.text)
                    self.file_repository.save_text(f"{file_name}/metadata/transcript.md", attr_data.text)
                    # self.file_repository.save_text(f"{file_name}/content/questions.txt", attr_data.questions)