from schemas.file import File
from notion_client import Client
import re
import firebase_admin
from firebase_admin import credentials, storage
from uuid import uuid4
import os
import requests

class NotionService:
    """
    Service class to publish to Notion
    """

    def __init__(self, config):
        """
        Initialize the Notion service
        """
        self.client = Client(auth=config["NOTION_TOKEN"])
        self.database = config["NOTION_DATABASE_ID"]

        if not firebase_admin._apps:
            cred = credentials.Certificate(config["FIREBASE_CREDENTIALS_PATH"])
            firebase_admin.initialize_app(cred, {
                'storageBucket': config["FIREBASE_STORAGE_BUCKET"]
            })

        self.bucket = storage.bucket()

    def upload_image(self, image_path):
        """
        Notion does not support uploading images directly, so we upload to Firebase Storage and return the public URL.
        """
        # Generate a unique filename
        file_extension = os.path.splitext(image_path)[1]
        destination_blob_name = f"images/{uuid4()}{file_extension}"

        # Upload the file
        blob = self.bucket.blob(destination_blob_name)
        blob.upload_from_filename(image_path)

        # Make the blob publicly accessible
        blob.make_public()

        # Return the public URL
        return blob.public_url

    #TODO: Add banner and photo to the page. Requires uploading file servce then adding

    def create_page(self, blog: File):
        """
        Create a new page in Notion, in the specified database (at init)
        """
        photo_url = self.upload_image(blog.files.portrait)
        banner_url = self.upload_image(blog.files.portrait.rsplit('portrait.jpeg', 1)[0] + 'content/square.png')

        # Split content by Markdown headers
        parts = re.split(r'(^#{1,3}\s.*$)', blog.blog.content, flags=re.MULTILINE)
        
        children = []

        # Add the title as a h1 heading
        children.append({
            "object": "block",
            "type": "heading_1",
            "heading_1": {"rich_text": [{"type": "text", "text": {"content": blog.blog.title}}]}
        })

        # Add the description as a paragraph in grey italics
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": blog.blog.description, "link": None}}]}
        })

        # Add the banner
        children.append({
            "object": "block",
            "type": "image",
            "image": {
                "type": "external",
                "external": {
                    "url": banner_url
                }
            }
        })

        # # Add the photo
        # children.append({
        #     "object": "block",
        #     "type": "image",
        #     "image": {
        #         "type": "external",
        #         "external": {
        #             "url": photo_url
        #         }
        #     }
        # })

        current_block = None

        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            if part.startswith('# '):
                block_type = "heading_1"
                content = part[2:]
            elif part.startswith('## '):
                block_type = "heading_2"
                content = part[3:]
            elif part.startswith('### '):
                block_type = "heading_3"
                content = part[4:]
            else:
                block_type = "paragraph"
                content = part

            if current_block:
                children.append(current_block)

            current_block = {
                "object": "block",
                "type": block_type,
                block_type: {
                    "rich_text": []
                }
            }

            # Split content into chunks of 2000 characters or less
            while content:
                chunk = content[:2000]
                content = content[2000:]
                current_block[block_type]["rich_text"].append({"type": "text", "text": {"content": chunk}})
                
                if content:  # If there's more content, create a new block
                    children.append(current_block)
                    current_block = {
                        "object": "block",
                        "type": block_type,
                        block_type: {
                            "rich_text": []
                        }
                    }

        if current_block:
            children.append(current_block)

        new_page = self.client.pages.create(
            parent={"database_id": self.database},
            properties={
                "Name": {"title": [{"text": {"content": blog.name}}]},
            },
            children=children
        )

        return new_page
