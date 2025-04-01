from pydantic import BaseModel
from typing import Optional, List

class Files(BaseModel):
    """
    Files uploaded by the user
    """
    audio_file: str
    video_file: str
    resume_file: str
    portrait: str
    photo: str

# Metadata assets
class Resume(BaseModel):
    """
    Schema for the resume extracted from the resume pdf file
    """
    name: str
    studies: List[str]
    experiences: List[str]
    linkedin_url: str

    def __str__(self):
        return f"Resume: {self.name}\nStudies: {self.studies}\nExperiences: {self.experiences}\nLinkedIn URL: {self.linkedin_url}"

class Word(BaseModel):
    """
    Schema for the word extracted from the transcription
    """
    text: str
    start: int
    end: int
    confidence: float
    speaker: str

class Utterance(BaseModel):
    """
    AssemblyAI schema for the utterance extracted from the transcription
    """
    confidence: float
    end: int
    speaker: str
    start: int
    text: str
    words: Optional[List[Word]] = None

    class Config:
        allow_extra = True
        

    def __str__(self):
        return f"Utterance: {self.text}\nSpeaker: {self.speaker}\nConfidence: {self.confidence}\nStart: {self.start}\nEnd: {self.end}"

class Utterances(BaseModel):
    """
    Schema for the utterances extracted from the transcription
    """
    utterances: List[Utterance]

    def __str__(self):
        return "\n".join([utterance.__str__() for utterance in self.utterances])

class Transcript(BaseModel):
    """
    Schema for the transcript (generated from the AssemblyAI transcription)
    text is the transcript in markdown format
    """
    text: str

    def __str__(self):
        return self.text

class Guest(BaseModel):
    """
    Schema for the guest
    """
    first_name: str
    top_companies: List[str]
    top_universities: List[str]
    origin: str

class Metadata(BaseModel):
    """
    Metadata extracted from the files
    """
    resume: Optional[Resume]
    utterances: Optional[Utterances]
    transcript: Optional[Transcript]
    guest: Optional[Guest]

class ThumbnailParams(BaseModel):
    """
    Schema for the thumbnail parameters
    """
    height: int
    width: int
    
    # Fonts
    companies_font_size: int
    companies_x_offset: int
    companies_y_offset: int
    
    universities_font_size: int = 74
    universities_x_offset: int
    universities_y_offset: int
    
    name_font_size: int = 74
    name_x_offset: int = 0
    name_y_offset: int = 0

    portrait_ratio: float #TODO: 0.9 previously?
    portrait_align: str
    portrait_x_offset: int = 0
    portrait_y_offset: int = 0

class Thumbnails(BaseModel):
    """
    Thumbnails generated from the metadata & files
    """
    photo_no_bg: Optional[bytes] = None
    landscape: Optional[bytes] = None
    landscape_params: Optional[ThumbnailParams] = None
    square: Optional[bytes] = None
    square_params: Optional[ThumbnailParams] = None

class Blog(BaseModel):
    """
    Blog assets generated from the metadata & files
    """
    structure: Optional[str] = None
    content: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    linkedin: Optional[str] = None

# Podcast assets
class Podcast(BaseModel):
    """
    Podcast generated from the metadata & files
    """
    title: Optional[str] = None
    description: Optional[str] = None
    blog: Optional[str] = None
    linkedin: Optional[str] = None

class File(BaseModel):
    """
    Schema for the file object
    """
    name: Optional[str]
    files: Optional[Files]
    metadata: Optional[Metadata]
    thumbnails: Optional[Thumbnails]
    blog: Optional[Blog]
    # podcast: Podcast

    def __str__(self):
        return f"""File: {self.name}
Metadata:
- Resume: {self.metadata.resume.__str__()}
- Utterances: {"Generated" if self.metadata.utterances else "Not generated"}
- Transcript: {"Generated" if self.metadata.transcript else "Not generated"}

Thumbnails:
- Landscape: {"Generated" if self.thumbnails.landscape else "Not generated"}
- Square: {"Generated" if self.thumbnails.square else "Not generated"}

Blog:
- Title: {self.blog.title[:100].replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ') if self.blog.title else "Not generated"}
- Description: {self.blog.description[:100].replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ') if self.blog.description else "Not generated"}
- Content: {self.blog.content[:100].replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ') if self.blog.content else "Not generated"}
- Linkedin: {self.blog.linkedin[:100].replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ') if self.blog.linkedin else "Not generated"}
        """

# Misc
class Prompt(BaseModel):
    """
    Schema for the prompts
    """
    text: str
    model: str = "opus"