import time
import os
from typing import List
from file_system.file_helper import FileHelper
from llms.llm_service import LLMService
from helpers.transcriber import Transcriber
from helpers.resume_extractor import ResumeExtractor
from helpers.thumbnail_generator import ThumbnailGenerator
from prompts.prompts import Prompts
from helpers.notion_service import NotionService
from helpers.podcast_generator import PodcastGenerator
from dotenv import load_dotenv
from schemas.file import Blog, Thumbnails
from schemas.prompt import SimpleResponse, Prompt
from errors import GuestNotFoundError

class BlogEditor():
    """
    Class to handle the blog editing process
    """

    def __init__(self):
        """
        Initialize the BlogEditor
        """
        # Load env variables
        load_dotenv()
        config = self.get_env_vars()

        # Initialize services
        self.file_helper = FileHelper('/Users/anirudhh/Documents/Zoom_v2')
        self.llm = LLMService(config)
        self.prompts = Prompts(self.file_helper)
        self.resume_extractor = ResumeExtractor(self.llm, self.prompts)
        self.thumbnail_generator = ThumbnailGenerator()
        self.transcriber = Transcriber(config, self.llm, self.prompts)
        self.podcast_generator = PodcastGenerator(config, self.llm, self.prompts)
        self.notion_service = NotionService(config)

    def get_env_vars(self):
        """
        Get the environment variables
        """
        return {
            "ASSEMBLYAI_API_KEY": os.getenv("ASSEMBLYAI_API_KEY"),
            "NOTION_TOKEN": os.getenv("NOTION_TOKEN"),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
            "NOTION_DATABASE_ID": os.getenv("NOTION_DATABASE_ID"),
            "FIREBASE_CREDENTIALS_PATH": os.getenv("FIREBASE_CREDENTIALS_PATH"),
            "FIREBASE_STORAGE_BUCKET": os.getenv("FIREBASE_STORAGE_BUCKET"),
            "ELEVENLABS_API_KEY": os.getenv("ELEVENLABS_API_KEY"),
        }

    # List & get files

    def list_files(self) -> List[str]:
        """
        List all the files in the file system
        """
        return self.file_helper.list_files()

    def get(self, file_name: str) -> Blog:
        """
        Get the blog with the given file name
        """
        return self.file_helper.get(file_name)


    # Extract metadata from the existing documents

    def extract_resume(self, file_name: str, callback=None) -> None:
        """
        Extract the resume from the given file name
        """
        blog = self.file_helper.get(file_name)

        if not self.check_files(blog):
            print("Missing files, upload them!")
            return

        if not blog.metadata.resume:
            if callback:
                callback("Extracting resume for " + file_name)
            blog.metadata.resume = self.resume_extractor.extract(blog)
            self.file_helper.save(blog)

    def transcribe(self, file_name: str, callback=None) -> None:
        """
        Transcribe the given file name
        """
        blog = self.file_helper.get(file_name)

        if not self.check_files(blog):
            print("Missing files, upload them!")
            return

        if not blog.metadata.utterances:
            if callback:
                callback("Utterances not found, generating for " + file_name)
            blog.metadata.utterances = self.transcriber.transcribe(blog.files.audio_file)
            self.file_helper.save(blog)

        if not blog.metadata.transcript:
            if callback:
                callback("Transcript not found, generating for " + file_name)
            blog.metadata.transcript = self.transcriber.generate_transcript(blog.metadata.utterances)
            self.file_helper.save(blog)

    # Enrich guest
    def enrich_guest(self, file_name: str, callback=None):
        """
        Enrich the guest data with first_name, origin, top companies & universities
        """
        blog = self.file_helper.get(file_name)

        if not blog.metadata.guest:
            blog.metadata.guest = self.resume_extractor.enrich_guest(blog)
            self.file_helper.save(blog)
    
    # Generate thumbnails
    def generate_thumbnails(self, file_name, callback=None):
        """
        Generate the thumbnails for the given file name
        """
        blog = self.file_helper.get(file_name)

        if not blog.files.photo:
            print(f"Photo not found for {file_name}, upload it!")
            return
        if not blog.files.resume_file:
            print(f"Resume not found for {file_name}, upload & generate it!")
            return

        # Always generate thumbnails
        if callback:
            callback(f"Generating thumbnails for {file_name}")
        blog.thumbnails = self.thumbnail_generator.generate_thumbnails(blog)
        self.file_helper.save(blog)

    # Generate blog assets (title, description, linkedin, blog)

    def generate(self, file_name: str, attr: str, model="opus", llm_stream=None, callback=None):
        """
        Handle the generation of an attribute for a blog
        """
        file = self.file_helper.get(file_name)

        if not self.check_files(file):
            print("Missing files, upload them!")
            return

        # The attribute has not been generated previously, so generate it
        if not getattr(file.blog, attr):
            prompt = self.prompts.get_prompt(file, attr)
            self._generate(file, attr, prompt, model, llm_stream, callback)
        else:
            # Attribute was already generated once, ask the user what to do
            message = f"{attr} already generated for {file_name}, skipping."
            print(message)
            llm_stream(message)
            callback(message)

    def edit(self, file_name: str, attr: str, instructions: str,model="opus", llm_stream=None, callback=None):
        """
        Edit the given attribute for the given file name

        TODO: This can be merged into generate method
        """
        file = self.file_helper.get(file_name)

        if not self.check_files(file):
            print("Missing files, upload them!")
            return

        if not getattr(file.blog, attr):
            message = f"{attr} not generated for {file_name}, generating it!"
            print(message)
            llm_stream(message)
            callback(message)
            self._generate(file, attr, model, llm_stream, callback)
            return
        
        attr_prompt = self.prompts.get_prompt(file, attr)
        prompt = f"""
        Here is the previous chat conversation:
        <previous_chat_history>
            <previous_instructions>
                {attr_prompt.text}
            </previous_instructions>
            <output>
                {getattr(file.blog, attr)} 
            </output>
        </previous_chat_history>

        You have been provided with the following user instructions:
        <user_instructions>
            {instructions}
        </user_instructions>

        Edit the text: {getattr(file.blog, attr)} using the above instructions and return.
        """

        self._generate(file, attr, Prompt(text=prompt, model=attr_prompt.model), model, llm_stream, callback)

    def _generate(self, file: Blog, attr: str, prompt: str, model="opus", llm_stream=None, callback=None):
        """
        Generate a specified attribute for the blog
        """
        if callback:
            callback(f"Generating {attr} for {file.name}")

        if llm_stream:
            print(f"Streaming {attr} for {file.name}")
            response = self.llm.stream_prompt(prompt.text, model=prompt.model, llm_stream=llm_stream)
            setattr(file.blog, attr, response)
            self.file_helper.save(file)
        else:
            if attr in ["title", "description", "linkedin"]:
                response = self.llm.prompt(prompt.text, model=prompt.model, schema=SimpleResponse)
            else:
                response = self.llm.prompt(prompt.text, model=prompt.model)
            setattr(file.blog, attr, response)
            self.file_helper.save(file)

    # Publish the blog
    # TODO: Move these into a dedicated helper class
    def publish_markdown_draft(self, file_name, callback=None):
        """
        Publish the blog as a markdown draft
        """
        file = self.file_helper.get(file_name)

        if not file.blog:
            file.blog = Blog()

        if callback:
            callback(f"Publishing markdown draft for {file_name}")

        # TODO: Old code, this must be fixed
        with open(f"/temp/{file_name}.md", "w") as f:
            blog_content = f"""
            # Title: {file.blog.title}
            Description: {file.blog.description}
            ---
            # Overview
            {file.metadata.resume}
            ---
            # Blog
            {file.blog.content}
            ---
            # LinkedIn
            {file.blog.linkedin}
            """
            f.write(blog_content)

    def publish_notion_draft(self, file_name, callback=None):
        """
        Publish the blog to notion
        """
        file = self.file_helper.get(file_name)

        if callback:
            callback(f"Publishing {file_name} to notion")

        if not file.files.photo:
            print(f"Photo not found for {file_name}, upload it!")
            return

        if not file.thumbnails.landscape:
            print(f"Banner not found for {file_name}, upload it!")
            return

        if not file.thumbnails.square:
            print(f"Square thumbnail not found for {file_name}, generate it!")
            return

        if not file.metadata.resume:
            print(f"Resume not found for {file_name}, generate it!")
            return

        if not file.blog.title:
            print(f"Title not found for {file_name}, generate it!")
            return

        if not file.blog.description:
            print(f"Description not found for {file_name}, generate it!")
            return

        if not file.blog.content:
            print(f"Blog not found for {file_name}, generate it!")
            return

        if not file.blog.linkedin:
            print(f"LinkedIn not found for {file_name}, generate it!")
            return

        self.notion_service.create_page(file)

        if callback:
            callback(f"Published {file_name} to notion")

    def reset(self, file_name, callback=None):
        """
        Reset the blog with the given file name
        """
        # TODO: Not yet implemented
        if callback:
            callback(f"Resetting {file_name}. NOT YET IMPLEMENTED")
        self.file_helper.reset(file_name)

    def generate_all(self, file_name, model="opus", llm_stream=None, callback=None):
        """
        Generate all the attributes for the given file name
        """
        if callback:
            callback(f"Generating all for {file_name}")

        self.extract_resume(file_name, callback=callback)
        self.transcribe(file_name, callback=callback)

        # Enrich the guest
        self.enrich_guest(file_name, callback=callback)

        # Generate thumbnails
        self.generate_thumbnails(file_name, callback=callback)

        # Generate blog
        for attr in Blog.__annotations__.keys():
            self.generate(file_name, attr, model=model, llm_stream=llm_stream, callback=callback)

        # Generate podcast
        # if callback:
        #         callback("Generating podcast intro...")
        # file = self.file_helper.get(file_name)
        # self.podcast_generator.generate_intro(file)

        # if callback:
        #     callback("Generating podcast...")
        # self.podcast_generator.generate_podcast(file)

        print(f"All generated for {file_name}")

    # Validation

    def check_files(self, file: Blog) -> bool:
        """
        Check if all the required files are present for the given blog

        To generate a blog, we need the following files: audio.m4a, resume.pdf and a photo.png
        """
        if not file.files.audio_file:
            return False
        if not file.files.resume_file:
            return False
        if not file.files.photo:
            return False

        return True